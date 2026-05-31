"""
Cliente DeepSeek API para extraccion de datos estructurados de paginas web.
Usa deepseek-chat (V4 Flash) - modelo rapido y economico.
"""
import requests
import json
import time
from config import EXTRACTION_PROMPT, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_URL


def extraer_datos(contenido: str, empresa: str, url: str) -> dict:
    """
    Envia el contenido de la web a DeepSeek y extrae datos estructurados.
    Retorna dict con: email_encontrados, problema_detectado, idea_mejora, etc.
    """
    if not contenido or contenido.startswith("[ERROR]") or contenido.startswith("[NO HTML]"):
        return {
            "email_encontrados": [],
            "proveedor_email": "",
            "problema_detectado": f"Error al acceder a la web: {contenido[:80]}" if contenido else "Sin web disponible",
            "idea_mejora": "No se pudo analizar la web",
            "tamano_empresa": "",
            "telefono_contacto": "",
            "persona_contacto": "",
        }

    # Truncar si es muy largo
    contenido_recortado = contenido[:12000]

    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": f"Empresa: {empresa}\nURL: {url}\n\nContenido de la web:\n\n{contenido_recortado}"}
    ]

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
    }

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        content = ""
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")

        # Parsear JSON de la respuesta
        return _parsear_respuesta(content, empresa)

    except requests.exceptions.Timeout:
        print(f"  [WARN] DeepSeek timeout para {empresa}")
        return {"email_encontrados": [], "problema_detectado": "Timeout de IA", "idea_mejora": "", "tamano_empresa": ""}
    except Exception as e:
        print(f"  [WARN] DeepSeek error para {empresa}: {e}")
        return {"email_encontrados": [], "problema_detectado": f"Error IA: {str(e)[:80]}", "idea_mejora": "", "tamano_empresa": ""}


def _parsear_respuesta(content: str, empresa: str) -> dict:
    """Parsea la respuesta JSON de DeepSeek."""
    if not content:
        return {"email_encontrados": [], "problema_detectado": "", "idea_mejora": "", "tamano_empresa": ""}

    # Intentar extraer JSON de la respuesta (puede venir con markdown)
    import re
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Buscar { } directamente
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            print(f"  [WARN] No se pudo extraer JSON de respuesta DeepSeek para {empresa}")
            return {"email_encontrados": [], "problema_detectado": "Error parseando respuesta IA", "idea_mejora": "", "tamano_empresa": ""}

    try:
        parsed = json.loads(json_str)
        return {
            "email_encontrados": parsed.get("email_encontrados", []),
            "proveedor_email": parsed.get("proveedor_email", ""),
            "problema_detectado": parsed.get("problema_detectado", ""),
            "idea_mejora": parsed.get("idea_mejora", ""),
            "tamano_empresa": parsed.get("tamano_empresa", ""),
            "telefono_contacto": parsed.get("telefono_contacto", ""),
            "persona_contacto": parsed.get("persona_contacto", ""),
        }
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON invalido para {empresa}: {e}")
        return {"email_encontrados": [], "problema_detectado": "Error parseando respuesta IA", "idea_mejora": "", "tamano_empresa": ""}
