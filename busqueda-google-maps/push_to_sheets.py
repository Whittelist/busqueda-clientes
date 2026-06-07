"""
Sube los datos de SQLite a Google Sheets (TEST EMPRESAS BOT 2).
UPSERT + DEDUP por email: no borra datos existentes, solo añade empresas nuevas
o actualiza filas que ya existen (emparejando por nombre + provincia).
Ademas, detecta duplicados por email: si el nuevo dato comparte email con
una fila existente (aunque tenga distinto nombre), se fusiona en lugar de insertar.
"""
import json, os, re, sqlite3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "busqueda-emails", "google_token_sheets.json")
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
SHEET_NAME = "TEST EMPRESAS BOT 2"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "clientes.db")
EMAIL_COL = 4   # Columna E
COLUMNS = 22    # A a V


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


def _sheets_service():
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token_info = json.load(f)
    creds = Credentials.from_authorized_user_info(token_info)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(json.loads(creds.to_json()), f, indent=2)
    return build("sheets", "v4", credentials=creds)


def _leer_sheet(service) -> dict:
    """Lee filas del sheet. Devuelve dict {(nombre, provincia): {row, values}}."""
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A2:V2000"
    ).execute()
    raw = result.get("values", [])
    existentes = {}
    for i, row in enumerate(raw):
        if not row or not row[0]:
            continue
        nombre = (row[0] or "").strip().lower()
        provincia = (row[1] or "").strip().lower() if len(row) > 1 else ""
        clave = (nombre, provincia)
        existentes[clave] = {"row": i + 2, "values": row}
    return existentes


def _construir_mapa_email(existentes: dict) -> dict[str, list[tuple]]:
    """email → [(row_number, clave), ...]"""
    mapa = {}
    for clave, info in existentes.items():
        email_val = info["values"][EMAIL_COL] if len(info["values"]) > EMAIL_COL else ""
        for email in extraer_emails(email_val):
            if email not in mapa:
                mapa[email] = []
            mapa[email].append((info["row"], clave))
    return mapa


def get_datos():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No existe la BD: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT nombre, provincia, categoria, website as web,
               '' as email, telefono,
               rating, total_reviews, reviews_json, direccion,
               latitud || ',' || longitud as coordenadas, google_maps_url,
               '' as estado, '' as ultimo_contacto, '' as proxima_accion,
               '' as fecha_prox_accion, '' as problema, '' as idea_mejora,
               '' as prioridad, '' as notas, '' as tamano, '' as num_contactos
        FROM empresas
        ORDER BY provincia, nombre
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    datos = []
    for r in rows:
        fila = []
        for col in range(len(r)):
            val = r[col]
            if val is None:
                val = ""
            elif isinstance(val, float):
                val = round(val, 2)
            fila.append(str(val) if not isinstance(val, (int, float)) else val)
        while len(fila) < COLUMNS:
            fila.append("")
        datos.append(fila)

    return datos


def push_to_sheets(datos: list[list], service=None):
    """
    Upsert + dedup por email.
    - Si coincide (nombre, provincia): actualiza.
    - Si no coincide pero comparte email con fila existente: actualiza esa fila (fusion).
    - Si no coincide nada: inserta nueva fila.
    """
    if service is None:
        service = _sheets_service()

    existentes = _leer_sheet(service)
    mapa_email = _construir_mapa_email(existentes)
    updates = []
    nuevas = []
    insertadas = 0
    actualizadas = 0
    dedup_email = 0

    for fila in datos:
        nombre = (fila[0] or "").strip().lower()
        provincia = (fila[1] or "").strip().lower() if len(fila) > 1 else ""
        clave = (nombre, provincia)

        # 1. Coincidencia exacta por nombre + provincia
        if clave in existentes:
            row_num = existentes[clave]["row"]
            updates.append({"range": f"'{SHEET_NAME}'!A{row_num}", "values": [fila]})
            actualizadas += 1
            continue

        # 2. Coincidencia por email
        emails_nuevos = extraer_emails(fila[EMAIL_COL]) if len(fila) > EMAIL_COL else []
        encontrado_por_email = None
        for email in emails_nuevos:
            if email in mapa_email:
                encontrado_por_email = mapa_email[email][0]  # (row, clave)
                break

        if encontrado_por_email:
            row_num, clave_existente = encontrado_por_email
            print(f"  [DEDUP] '{fila[0]}' coincide por email con fila {row_num} ('{clave_existente[0]}')")
            updates.append({"range": f"'{SHEET_NAME}'!A{row_num}", "values": [fila]})
            actualizadas += 1
            dedup_email += 1
            # Actualizar el mapa para futuras iteraciones
            existentes[clave] = existentes[clave_existente]
            continue

        # 3. No coincide: insertar nueva
        nuevas.append(fila)
        insertadas += 1

    if updates:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "RAW", "data": updates}
        ).execute()

    if nuevas:
        ultima_fila = max((e["row"] for e in existentes.values()), default=1) + 1
        body = {"values": nuevas}
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!A{ultima_fila}",
            valueInputOption="RAW",
            body=body
        ).execute()
        insertadas = result.get("updatedRows", len(nuevas))

    return actualizadas, insertadas, dedup_email


def main():
    print("Subiendo datos a TEST EMPRESAS BOT 2 (UPSERT + DEDUP)...")
    datos = get_datos()

    if not datos:
        print("[!] No hay datos en la BD. Ejecuta primero main.py")
        return

    print(f"  {len(datos)} empresas encontradas en BD")
    service = _sheets_service()
    act, ins, dedup = push_to_sheets(datos, service)
    print(f"  Actualizadas: {act}  (de las cuales {dedup} por email)")
    print(f"  Insertadas:   {ins}")
    print(f"  Total:        {act + ins}")

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    print(f"\n[OK] Abre {url} y ve a la pestana '{SHEET_NAME}'")


if __name__ == "__main__":
    main()
