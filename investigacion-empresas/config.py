import os, re
from dotenv import load_dotenv

load_dotenv(encoding="utf-8-sig")

# --- Google Sheets ---
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
SHEET_NAME = "TEST EMPRESAS BOT 2"
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_token_sheets.json")

# --- Sheet column indices (0-based) ---
# A=nombre, B=provincia, C=categoria, D=web
# Q=problema, R=idea_mejora, T=notas, U=tamano
COL_INDEX = {
    "empresa": 0,
    "provincia": 1,
    "categoria": 2,
    "web": 3,
    "problema": 16,
    "idea_mejora": 17,
    "notas": 19,
    "tamano": 20,
}

# --- DeepSeek ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))

# --- Execution ---
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
DELAY_BETWEEN_COMPANIES = float(os.getenv("DELAY_BETWEEN_COMPANIES", "3"))
MAX_COMPANIES_PER_RUN = int(os.getenv("MAX_COMPANIES_PER_RUN", "25"))

# --- Web fetcher ---
WEB_FETCH_TIMEOUT = 15
WEB_FETCH_MAX_PAGES = 15
WEB_FETCH_MAX_CHARS = 30000
WEB_FETCH_DELAY = 1.0


def get_spreadsheet_id() -> str:
    value = SPREADSHEET_ID
    match = re.search(r"/spreadsheets/d/([^/]+)", value)
    return match.group(1) if match else value
