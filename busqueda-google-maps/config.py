"""
Configuracion centralizada del proyecto.
Define las comunidades autonomas con sus provincias.
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

# --- Comunidades Autonomas ---
COMUNIDADES = {
    "Andalucia": ["Almeria", "Cadiz", "Cordoba", "Granada", "Huelva", "Jaen", "Malaga", "Sevilla"],
    "Aragon": ["Huesca", "Teruel", "Zaragoza"],
    "Asturias": ["Asturias"],
    "Baleares": ["Islas Baleares"],
    "Canarias": ["Las Palmas", "Santa Cruz de Tenerife"],
    "Cantabria": ["Cantabria"],
    "Castilla-La Mancha": ["Albacete", "Ciudad Real", "Cuenca", "Guadalajara", "Toledo"],
    "Castilla y Leon": ["Avila", "Burgos", "Leon", "Palencia", "Salamanca", "Segovia", "Soria", "Valladolid", "Zamora"],
    "Catalunya": ["Barcelona", "Girona", "Lleida", "Tarragona"],
    "Comunidad Valenciana": ["Alicante", "Castellon", "Valencia"],
    "Extremadura": ["Badajoz", "Caceres"],
    "Galicia": ["A Coruna", "Lugo", "Ourense", "Pontevedra"],
    "La Rioja": ["La Rioja"],
    "Madrid": ["Madrid"],
    "Murcia": ["Murcia"],
    "Navarra": ["Navarra"],
    "Pais Vasco": ["Alava", "Bizkaia", "Gipuzkoa"],
}

# --- Categorias de busqueda ---
CATEGORIAS = [
    "prefabricados de hormigon",
]

# --- Seleccion activa (cambiar aqui para buscar en otra comunidad) ---
COMUNIDAD_ACTIVA = "Castilla-La Mancha"
PROVINCIAS_ACTIVAS = ["Ciudad Real"]

# --- Base de datos ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "clientes.db")

# --- Salida CSV ---
CSV_OUTPUT = os.path.join(os.path.dirname(__file__), "data", "resultados.csv")
