import re, time
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

_MAX_RETRIES = 3
_RETRY_DELAY = 2

_CLIENT = None


def _get_client() -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("Define DEEPSEEK_API_KEY en el .env")
        _CLIENT = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _CLIENT


SYSTEM_PROMPT = """Eres un analista experto en digitalizacion del sector construccion espanol.

Tu tarea es analizar empresas constructoras y extraer 3 campos concretos:

1. PROBLEMA DETECTADO (max 150 caracteres)
   - Que problema de digitalizacion/organizacion parece tener la empresa segun su web
   - Basado en EVIDENCIAS de la web, no inventes
   - Si la web tiene e-commerce: mencionarlo (probablemente ya tienen algo de digitalizacion)
   - Si la web es muy basica (una pagina estatica): probablemente estan atrasados digitalmente
   - Si la web tiene catalogo de productos sin venta online: gestionan pedidos por telefono/email
   - Sin web disponible: indicarlo, digitalizacion nula

2. IDEA DE MEJORA (max 150 caracteres)
   - Mejora concreta relacionada con el problema detectado
   - Enfocada en automatizacion, organizacion de documentos, ERP, vision centralizada
   - Debe ser PRACTICA y REALISTA para el tamano de la empresa

3. TAMANO ESTIMADO (max 100 caracteres)
   - Indicadores: empleados (si se encuentra en la web), facturacion estimada,
     si es familiar, antiguedad, ambito local/nacional
   - Si no hay datos, inferir por el tipo de web y catalogo

REGLAS IMPORTANTES:
- NO uses palabras comodin: "digitalizacion", "transformacion digital", "sinergias", "soluciones integrales"
- NO inventes datos que no esten respaldados por la web o el contexto del sector
- Responde UNICAMENTE con el formato indicado, sin explicaciones adicionales"""


USER_PROMPT_TEMPLATE = """Analiza esta empresa del sector construccion:

EMPRESA: {nombre}
PROVINCIA: {provincia}
CATEGORIA: {categoria}
WEB: {web}

{contenido_seccion}

Devuelve EXACTAMENTE este formato (sin explicaciones):
Problema: [max 150 chars]
Mejora: [max 150 chars]
Tamano: [max 100 chars]"""


def _parse_response(text: str) -> dict | None:
    if not text:
        return None

    problema = ""
    mejora = ""
    tamano = ""

    for line in text.strip().split("\n"):
        line = line.strip()
        if re.match(r'^Problema:\s*', line, re.IGNORECASE):
            problema = re.sub(r'^Problema:\s*', '', line, flags=re.IGNORECASE).strip()
        elif re.match(r'^Mejora:\s*', line, re.IGNORECASE):
            mejora = re.sub(r'^Mejora:\s*', '', line, flags=re.IGNORECASE).strip()
        elif re.match(r'^Tama(?:n|ñ)o:\s*', line, re.IGNORECASE):
            tamano = re.sub(r'^Tama(?:n|ñ)o:\s*', '', line, flags=re.IGNORECASE).strip()

    if problema or mejora or tamano:
        parsed = {
            "problema": problema[:150],
            "mejora": mejora[:150],
            "tamano": tamano[:100],
        }
        # Si algun campo quedo vacio, DeepSeek no genero respuesta completa
        if not all([problema, mejora, tamano]):
            return None
        return parsed


_FALLBACK_TEXT = (
    "Sin informacion",
    "Auditoria gratuita de 15 min",
    "Tamano no determinado",
)


def _es_fallback(resultado: dict) -> bool:
    """Detecta si el resultado es placeholder de fallback."""
    for val in resultado.values():
        for fb in _FALLBACK_TEXT:
            if fb in val:
                return True
    return False


def _fallback_inferir(nombre: str, provincia: str, categoria: str) -> dict:
    return {
        "problema": f"Empresa de {categoria} en {provincia}. Sin informacion suficiente en su web para determinar estado digital.",
        "mejora": f"Auditoria gratuita de 15 min para identificar oportunidades de automatizacion en {categoria}.",
        "tamano": f"Empresa del sector {categoria} en {provincia}. Tamano no determinado.",
    }


def investigar_empresa(nombre: str, provincia: str, categoria: str, web: str, contenido_web: str) -> dict:
    """
    Analiza una empresa usando DeepSeek y devuelve {problema, mejora, tamano, es_fallback}.
    es_fallback=True significa que la respuesta no es un analisis real.
    """
    if contenido_web and len(contenido_web) > 50:
        contenido_seccion = f"CONTENIDO DE SU WEB ({web}):\n{contenido_web[:25000]}"
    else:
        contenido_seccion = "[Sin contenido web disponible - analiza solo con el contexto del sector]"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        nombre=nombre,
        provincia=provincia,
        categoria=categoria,
        web=web or "No disponible",
        contenido_seccion=contenido_seccion,
    )

    client = _get_client()
    last_error = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )

            text = (response.choices[0].message.content or "").strip()
            parsed = _parse_response(text)

            if parsed:
                parsed["es_fallback"] = _es_fallback(parsed)
                return parsed

            print(f"  [WARN] Intento {attempt+1}: respuesta no parseable. Reintentando...")
            last_error = f"Respuesta no parseable: {text[:100]}"

        except Exception as e:
            last_error = str(e)
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAY * (attempt + 1)
                print(f"  [WARN] Intento {attempt+1} fallo: {e}. Reintentando en {delay}s...")
                time.sleep(delay)
            continue

        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_DELAY)

    print(f"  [ERROR] DeepSeek no respondio tras {_MAX_RETRIES} intentos: {last_error}")
    resultado = _fallback_inferir(nombre, provincia, categoria)
    resultado["es_fallback"] = True
    return resultado
