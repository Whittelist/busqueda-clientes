#!/usr/bin/env python3
"""
Escanea el Sheet 'TEST EMPRESAS BOT 2' en busca de duplicados por email.
Si dos filas comparten al menos un email, se fusionan: se queda la fila con mas datos
y la otra se vacia (se borra su contenido).

Uso:
    python dedup.py                    # dry-run (solo muestra)
    python dedup.py --apply            # aplica los cambios
    python dedup.py --apply --force    # sin confirmacion interactiva
"""
import json, os, sys, re, argparse
from collections import defaultdict

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
SHEET_NAME = "TEST EMPRESAS BOT 2"
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "busqueda-emails", "google_token_sheets.json")
COLUMNS = 22


def extraer_emails(text: str) -> list[str]:
    if not text:
        return []
    partes = re.split(r'[,;]', text)
    validos = []
    for p in partes:
        p = p.strip().lower()
        if re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', p):
            validos.append(p)
    return validos


def _contar_campos_llenos(row: list) -> int:
    """Cuenta cuantos campos no vacios tiene una fila (sin contar col 0 = nombre)."""
    return sum(1 for v in row[1:] if v and v.strip())


def _fusionar_filas(principal: list, secundaria: list) -> list:
    """Fusiona dos filas: se queda con el valor no vacio de cada columna."""
    resultado = []
    for i in range(max(len(principal), len(secundaria))):
        a = principal[i] if i < len(principal) else ""
        b = secundaria[i] if i < len(secundaria) else ""
        # Si una tiene email y la otra no, priorizar la que tiene email
        if i == 4:  # Columna email
            if a and b:
                # Unir emails sin duplicar
                todos = set(extraer_emails(a) + extraer_emails(b))
                resultado.append(", ".join(sorted(todos)))
            else:
                resultado.append(a or b)
        else:
            resultado.append(a or b)
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Dedup por email en Sheet")
    parser.add_argument("--apply", action="store_true", help="Aplicar cambios (dry-run por defecto)")
    parser.add_argument("--force", action="store_true", help="Omitir confirmacion")
    args = parser.parse_args()

    is_dry = not args.apply
    EMAIL_COL = 4

    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token_info = json.load(f)
    creds = Credentials.from_authorized_user_info(token_info)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    service = build("sheets", "v4", credentials=creds)

    print("Leyendo datos del Sheet...")
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A2:V2000"
    ).execute()
    raw = result.get("values", [])

    # Indice: email → [(row_number, row_values)]
    email_idx = defaultdict(list)
    filas = []
    for i, row in enumerate(raw):
        if not row or not row[0]:
            continue
        row_num = i + 2
        filas.append((row_num, row))
        email_val = row[EMAIL_COL] if len(row) > EMAIL_COL else ""
        for e in extraer_emails(email_val):
            email_idx[e].append((row_num, row))

    # Detectar grupos duplicados
    visitados = set()
    grupos = []

    for email, ocurrencias in email_idx.items():
        # Solo nos interesan emails con 2+ ocurrencias
        if len(ocurrencias) < 2:
            continue
        # Recoger todas las filas de este email cluster
        cluster_rows = set()
        for rn, rv in ocurrencias:
            if rn not in visitados:
                cluster_rows.add(rn)

        if len(cluster_rows) < 2:
            continue

        grupo = []
        for rn, rv in ocurrencias:
            if rn in cluster_rows:
                grupo.append((rn, rv))
                visitados.add(rn)

        if len(grupo) >= 2:
            grupos.append(grupo)

    if not grupos:
        print("No se encontraron duplicados por email.")
        return

    print(f"\nSe encontraron {len(grupos)} grupo(s) con emails duplicados:\n")

    fusiones = []
    for grupo in grupos:
        # La fila con mas datos = principal
        grupo.sort(key=lambda x: _contar_campos_llenos(x[1]), reverse=True)
        principal_rn, principal_row = grupo[0]
        print(f"  Principal: fila {principal_rn} - {principal_row[0]} ({_contar_campos_llenos(principal_row)} campos)")

        for sec_rn, sec_row in grupo[1:]:
            print(f"    Duplicada: fila {sec_rn} - {sec_row[0]} ({_contar_campos_llenos(sec_row)} campos)")
            # Emails que causan la duplicacion
            emails_princ = set(extraer_emails(principal_row[EMAIL_COL] if len(principal_row) > EMAIL_COL else ""))
            emails_sec = set(extraer_emails(sec_row[EMAIL_COL] if len(sec_row) > EMAIL_COL else ""))
            comunes = emails_princ & emails_sec
            print(f"      Email(s) compartido(s): {', '.join(comunes)}")

        fusiones.append(grupo)

    print(f"\nTotal: {len(fusiones)} grupos, {sum(len(g) for g in fusiones)} filas implicadas.")

    if is_dry:
        print("\n[DRY-RUN] Para aplicar los cambios: python dedup.py --apply")
        return

    if not args.force:
        confirm = input("\nAplicar fusiones y limpiar duplicadas? (s/N): ").strip().lower()
        if confirm != "s":
            print("Abortado.")
            return

    # Aplicar: fusionar datos en principal, limpiar secundarias
    batch_data = []
    borradas = 0

    for grupo in fusiones:
        grupo.sort(key=lambda x: _contar_campos_llenos(x[1]), reverse=True)
        principal_rn, principal_row = grupo[0]

        for sec_rn, sec_row in grupo[1:]:
            # Fusionar datos de secundaria en principal
            fusionada = _fusionar_filas(principal_row, sec_row)
            batch_data.append({
                "range": f"'{SHEET_NAME}'!A{principal_rn}",
                "values": [fusionada]
            })
            # Vaciar la fila duplicada
            vacia = [""] * COLUMNS
            batch_data.append({
                "range": f"'{SHEET_NAME}'!A{sec_rn}",
                "values": [vacia]
            })
            borradas += 1
            principal_row = fusionada

    if batch_data:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "RAW", "data": batch_data}
        ).execute()

    print(f"\n[OK] {borradas} filas duplicadas limpiadas, datos fusionados en las principales.")
    print(f"     Revisa el Sheet y borra manualmente las filas vacias si es necesario.")


if __name__ == "__main__":
    main()
