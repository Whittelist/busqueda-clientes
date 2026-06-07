import os, sys, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SPREADSHEET_ID, TOKEN_PATH
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Auth
with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    token_info = json.load(f)
creds = Credentials.from_authorized_user_info(token_info)
service = build("sheets", "v4", credentials=creds)

# Read Sheet4
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="TEST EMPRESAS BOT 2!A2:V2000"
).execute()
rows = result.get("values", [])

if not rows:
    print("[!] No hay datos en Sheet4")
    sys.exit(0)

# Create Module 1 DB
mod1_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "busqueda-google-maps", "data")
os.makedirs(mod1_dir, exist_ok=True)
mod1_db = os.path.join(mod1_dir, "clientes.db")

conn = sqlite3.connect(mod1_db)
conn.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        provincia TEXT,
        website TEXT
    )
""")
conn.execute("DELETE FROM empresas")

count = 0
skipped = 0
for i, row in enumerate(rows, 1):
    nombre = (row[0] if len(row) > 0 else "").strip()
    provincia = (row[2] if len(row) > 2 else "").strip()
    website = (row[3] if len(row) > 3 else "").strip()
    email_existente = (row[4] if len(row) > 4 else "").strip()
    if not nombre:
        continue
    # Si ya fue procesado por el bot (columna E no vacia) -> saltar
    if email_existente:
        skipped += 1
        continue
    conn.execute(
        "INSERT INTO empresas (id, nombre, provincia, website) VALUES (?, ?, ?, ?)",
        (i, nombre, provincia, website)
    )
    count += 1

conn.commit()
conn.close()
print(f"[OK] Sheet4 leido: {count} empresas incompletas cargadas ({skipped} completas saltadas)")
print(f"  BD: {mod1_db}")
print(f"  BD: {mod1_db}")
