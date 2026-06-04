"""
Sube datos enriquecidos a Sheet4, actualizando las filas correspondientes.
Lee el enrichment de la BD local y actualiza las columnas en Sheet4.
"""
import json, os, sqlite3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from config import SPREADSHEET_ID, TOKEN_PATH, ENRICHED_DB


def push_enriched():
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token_info = json.load(f)

    creds = Credentials.from_authorized_user_info(token_info)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_info["token"] = creds.token
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(token_info, f, indent=2)

    service = build("sheets", "v4", credentials=creds)

    # Leer emails y datos enriquecidos
    conn = sqlite3.connect(ENRICHED_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT nombre, email_extraidos, telefono_contacto,
               persona_contacto, problema_detectado, idea_mejora,
               tamano_empresa, website
        FROM enrichment
        ORDER BY provincia, nombre
    """).fetchall()
    conn.close()

    if not rows:
        print("[!] No hay datos enriquecidos para subir")
        return

    # Leer datos actuales de Sheet4 para encontrar filas por nombre
    sheet_data = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="TEST EMPRESAS BOT 2!A2:V2000"
    ).execute().get("values", [])

    # Mapa: nombre_empresa -> indice_fila (2-indexed en sheets)
    nombre_a_fila = {}
    for i, row in enumerate(sheet_data):
        if row:
            nombre_a_fila[row[0].strip().lower()] = i + 2  # +2 por header (A1) + 0-index

    actualizadas = 0
    for r in rows:
        nombre = r["nombre"].strip().lower()
        fila = nombre_a_fila.get(nombre)
        if not fila:
            continue

        emails = json.loads(r["email_extraidos"] or "[]")
        email_str = ", ".join(emails)

        # Columnas en Sheet4: D=Web, E=Email, F=Telefono, Q=Problema, R=Idea, U=Tamano
        cells = {}
        if email_str:
            cells["E"] = email_str
        else:
            cells["E"] = "No encontrado"
        if r["telefono_contacto"]:
            cells["F"] = r["telefono_contacto"]
        if not r["website"]:
            cells["D"] = "No encontrado"
        elif "No se encontro" in str(r["website"]):
            cells["D"] = "No encontrado"
        if r["problema_detectado"]:
            cells["Q"] = r["problema_detectado"]
        if r["idea_mejora"]:
            cells["R"] = r["idea_mejora"]
        if r["tamano_empresa"]:
            cells["U"] = r["tamano_empresa"]

        for col, val in cells.items():
            cell = f"{col}{fila}"
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"TEST EMPRESAS BOT 2!{cell}",
                valueInputOption="RAW",
                body={"values": [[val]]}
            ).execute()

        actualizadas += 1
        print(f"  [OK] {r['nombre']}: email={email_str or 'N/A'}, problema={r['problema_detectado'][:40] if r['problema_detectado'] else 'N/A'}...")

    print(f"\n[OK] {actualizadas} filas actualizadas en Sheet4")
    print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    push_enriched()
