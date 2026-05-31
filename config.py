"""
Configuración centralizada del proyecto.
Carga variables de entorno y define constantes.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# --- Google Places API ---
PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place"
PLACES_TEXTSEARCH_URL = f"{PLACES_API_BASE}/textsearch/json"
PLACES_DETAILS_URL = f"{PLACES_API_BASE}/details/json"

# --- Búsqueda ---
# Provincias de Andalucía para test
ANDALUCIA_PROVINCIAS = [
    "Almería", "Cádiz", "Córdoba", "Granada",
    "Huelva", "Jaén", "Málaga", "Sevilla"
]

# Categorías/niche a buscar (la primera para test)
CATEGORIAS = [
    "prefabricados de hormigón",
]

# Radio de búsqueda en metros (por defecto 50km = cubre provincia entera)
SEARCH_RADIUS = 50000

# --- Base de datos ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "clientes.db")

# --- Salida CSV ---
CSV_OUTPUT = os.path.join(os.path.dirname(__file__), "data", "resultados.csv")
