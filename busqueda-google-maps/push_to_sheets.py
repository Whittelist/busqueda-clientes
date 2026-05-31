"""
Sube los datos de SQLite a Google Sheets (Sheet4).
Usa el token OAuth existente (Gmail + Sheets).
"""
import json, os, sqlite3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH = "C:/Users/bjazu/.openclaw/workspace/new_google_token.json"
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
SHEET_NAME = "Sheet4"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "clientes.db")


def get_datos():
    """Lee empresas de SQLite y las prepara para Sheets."""
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] No existe la BD: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cols = [c[1] for c in conn.execute('PRAGMA table_info(empresas)').fetchall()]
    query = f"""
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
        datos.append(fila)

    return datos


def push_to_sheets(datos: list[list]):
    """Escribe los datos en Sheet4."""
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token_info = json.load(f)

    creds = Credentials.from_authorized_user_info(token_info)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_info["token"] = creds.token
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(token_info, f, indent=2)

    service = build("sheets", "v4", credentials=creds)

    # Limpiar datos viejos (todo menos header)
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A2:Z10000"
    ).execute()

    # Escribir datos nuevos
    if datos:
        body = {"values": datos}
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!A2",
            valueInputOption="RAW",
            body=body
        ).execute()
        return result.get("updatedRows", 0)

    return 0


def main():
    print("Subiendo datos a Sheet4...")
    datos = get_datos()

    if not datos:
        print("[!] No hay datos en la BD. Ejecuta primero main.py")
        return

    print(f"  {len(datos)} empresas encontradas en BD")

    filas = push_to_sheets(datos)
    print(f"  {filas} filas escritas en Sheet4")

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    print(f"\n[OK] Abre {url} y ve a la pestana '{SHEET_NAME}'")


if __name__ == "__main__":
    main()
