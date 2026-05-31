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
        SELECT e.nombre, e.email_extraidos, e.telefono_contacto,
               e.persona_contacto, e.problema_detectado, e.idea_mejora,
               e.tamano_empresa
        FROM enrichment e
        ORDER BY e.provincia, e.nombre
    """).fetchall()
    conn.close()

    if not rows:
        print("[!] No hay datos enriquecidos para subir")
        return

    # Leer datos actuales de Sheet4 para encontrar filas por nombre
    sheet_data = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet4!A2:V2000"
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

        # Columnas en Sheet4: E=Email, F=Telefono, M=Estado, Q=Problema, R=Idea, U=Tamano
        updates = []
        if email_str:
            updates.append(f"E{fila}")
        if r["problema_detectado"]:
            updates.append(f"Q{fila}")
        if r["idea_mejora"]:
            updates.append(f"R{fila}")
        if r["tamano_empresa"]:
            updates.append(f"U{fila}")

        for cell in updates:
            col = cell[0]
            val = {
                "E": email_str,
                "Q": r["problema_detectado"],
                "R": r["idea_mejora"],
                "U": r["tamano_empresa"],
            }[col]

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"Sheet4!{cell}",
                valueInputOption="RAW",
                body={"values": [[val]]}
            ).execute()

        actualizadas += 1
        print(f"  [OK] {r['nombre']}: email={email_str or 'N/A'}, problema={r['problema_detectado'][:40] if r['problema_detectado'] else 'N/A'}...")

    print(f"\n[OK] {actualizadas} filas actualizadas en Sheet4")
    print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    push_enriched()
