"""
Configuracion del modulo busqueda-navegador.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Ruta a la BD del Modulo 1 (lectura)
MOD1_DB = os.path.join(
    os.path.dirname(__file__),
    "..", "busqueda-google-maps", "data", "clientes.db"
)

# BD local de este modulo (guarda enrichment)
ENRICHED_DB = os.path.join(os.path.dirname(__file__), "data", "enriched.db")

# Sheet4 en Google Drive
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
TOKEN_PATH = "C:/Users/bjazu/Documents/Github/Automatizar emails 2/google_token_sheets.json"
