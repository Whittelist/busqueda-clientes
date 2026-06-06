import os, re
from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

# --- Google Sheets ---
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
SHEET_NAME = "TEST EMPRESAS BOT 2"
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_token_sheets.json")

# --- Gmail ---
FROM_EMAIL = os.getenv("FROM_EMAIL", "equipo@silvigon.com")

# --- Envio ---
DAILY_LIMIT = int(os.getenv("DAILY_DRAFT_LIMIT", "25"))
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 5
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")

# --- Secuencia de toques (dias de gap desde el envio anterior) ---
# Touch 1: dia 0, Touch 2: +4d, Touch 3: +6d, Touch 4: +7d, Touch 5: +7d
TOUCH_GAPS = {1: 0, 2: 4, 3: 6, 4: 7, 5: 7}
MAX_TOUCH = 5

# --- Scopes OAuth ---
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# --- Columnas en TEST EMPRESAS BOT 2 ---
# Basado en: Modulo 1 escribe A-V completo, Modulo 2 enriquece D, E, F, Q, R, U
# A=nombre, B=provincia, C=categoria, D=web, E=email, F=telefono
# M=estado, N=ultimo_contacto, O=proxima_accion, P=fecha_prox_accion
# Q=problema, R=idea_mejora, S=prioridad, T=notas, U=tamano, V=num_contactos
COL_INDEX = {
    "empresa": 0,       # A
    "provincia": 1,     # B
    "categoria": 2,     # C
    "web": 3,           # D
    "email": 4,         # E
    "telefono": 5,      # F
    "estado": 12,       # M
    "ultimo_contacto": 13,  # N
    "proxima_accion": 14,   # O
    "problema": 16,     # Q
    "idea_mejora": 17,  # R
    "prioridad": 18,    # S
    "notas": 19,        # T
    "tamano": 20,       # U
    "num_contactos": 21, # V
}

# --- DeepSeek ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# --- Timezone ---
TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")


def get_spreadsheet_id() -> str:
    value = SPREADSHEET_ID
    match = re.search(r"/spreadsheets/d/([^/]+)", value)
    return match.group(1) if match else value
