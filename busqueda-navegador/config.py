"""
Configuracion del modulo busqueda-navegador.
"""
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = ***"DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"  # deepseek-chat == V4 Flash (barato)
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# Ruta a la BD del Modulo 1 (lectura)
MOD1_DB = os.path.join(
    os.path.dirname(__file__),
    "..", "busqueda-google-maps", "data", "clientes.db"
)

# BD local de este modulo (guarda enrichment)
ENRICHED_DB = os.path.join(os.path.dirname(__file__), "data", "enriched.db")

# Sheet4 en Google Drive
SPREADSHEET_ID = "1mh3RWXa1mr3a_neJUOkHG-rG9pEgA3jcjrFCWK73BwQ"
TOKEN_PATH = "C:/Users/bjazu/.openclaw/workspace/new_google_token.json"

# DeepSeek prompt para extraer datos de la web
EXTRACTION_PROMPT = """
Eres un analista de prospeccion comercial. Analiza el contenido de la web de una empresa
y extrae la siguiente informacion en formato JSON. Responde SOLO con el JSON, sin explicaciones.

{
  "email_encontrados": ["email1@ejemplo.com"],
  "proveedor_email": "pagina de contacto" o "quienes somos" o "aviso legal" o "no encontrado",
  "problema_detectado": "Describe brevemente problemas visibles en la web (ej: web anticuada, sin certificaciones, falta informacion de contacto, diseno pobre, no responsive, etc). Max 100 caracteres.",
  "idea_mejora": "Sugiere una mejora concreta para su digitalizacion o proceso comercial. Max 100 caracteres.",
  "tamano_empresa": "pequena" o "mediana" o "grande",
  "telefono_contacto": "telefono encontrado en la web si es diferente al de Google Maps o vacio si no",
  "persona_contacto": "nombre de persona de contacto si aparece o vacio si no"
}

IMPORTANTE:
- Busca emails en toda la pagina, especialmente en contacto, aviso legal, quienes somos
- Si hay multiples emails, incluye todos
- No inventes informacion que no este en la pagina
- Responde SOLO JSON valido
"""
