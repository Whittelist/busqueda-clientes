"""
Crea la Sheet4 en el spreadsheet de SilviGon, clonando la estructura de Sheet1
y ampliando columnas para el proyecto Cliente Finder.

Sheet4 se usara para testear los datos de cliente_finder.
"""
import json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH = "C:/Users/bjazu/.openclaw/workspace/new_google_token.json"
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"

# === Cargar token ===
with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    token_info = json.load(f)

creds = Credentials.from_authorized_user_info(token_info)

# Refresh si expirado
if not creds.valid and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Guardar token refrescado
    token_info["token"] = creds.token
    token_info["expiry"] = creds.expiry.isoformat()
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_info, f, indent=2)
    print("[TOKEN] Refrescado correctamente")

service = build("sheets", "v4", credentials=creds)

# === Ver sheets existentes ===
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheets_existentes = [s["properties"]["title"] for s in spreadsheet["sheets"]]
print(f"Sheets existentes: {sheets_existentes}")

# === Leer headers de Sheet1 ===
range_sheet1 = "Sheet1!A1:Z1"
headers = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=range_sheet1
).execute().get("values", [[]])[0]

print(f"\nHeaders Sheet1 ({len(headers)} columnas):")
for i, h in enumerate(headers):
    print(f"  [{i}] {h}")

# === Definir headers para Sheet4 (Sheet1 + extras) ===
headers_sheet4 = [
    "Empresa",
    "Provincia",
    "Categoria",              # NUEVA: tipo de busqueda (prefabricados, aridos, etc)
    "Web",
    "Email",
    "Telefono",
    "Rating",                 # NUEVO: puntuacion Google Maps
    "Total Reviews",          # NUEVO: numero de reviews
    "Reviews (texto)",        # NUEVO: primeras reviews en texto
    "Direccion",              # NUEVA: direccion completa
    "Coordenadas",            # NUEVA: lat, lng
    "Google Maps URL",        # NUEVA: enlace directo
    "Estado",
    "Ultimo contacto",
    "Proxima accion",
    "Fecha proxima accion",
    "Problema detectado",
    "Idea de mejora",
    "Prioridad",
    "Notas",
    "Tamano empresa",
    "Numero de Contactos",
]

print(f"\nHeaders Sheet4 ({len(headers_sheet4)} columnas):")
for i, h in enumerate(headers_sheet4):
    print(f"  [{i}] {h}")

# === Crear Sheet4 ===
if "Sheet4" in sheets_existentes:
    print("\n[!] Sheet4 ya existe, voy a limpiarla...")
    # Limpiar contenido existente (todo menos header)
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet4!A2:Z2000"
    ).execute()
    # Actualizar header
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet4!A1:Z1",
        valueInputOption="RAW",
        body={"values": [headers_sheet4]}
    ).execute()
    print("[OK] Sheet4 limpiada y headers actualizados")
else:
    # Crear nueva sheet
    body = {
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": "Sheet4",
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": len(headers_sheet4)
                    }
                }
            }
        }]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    print("[OK] Sheet4 creada")

    # Poner headers
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet4!A1:Z1",
        valueInputOption="RAW",
        body={"values": [headers_sheet4]}
    ).execute()
    print("[OK] Headers escritos en Sheet4")

print(f"\n[DONE] Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print("  Ve a la pestanha 'Sheet4'")
