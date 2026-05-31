"""
Contenido web: fetch de paginas usando requests + fallback a Firecrawl.
Con manejo de errores y timeouts.
"""
import requests
import time
from urllib.parse import urlparse


def fetch_url(url: str, timeout: int = 15) -> str:
    """
    Obtiene el contenido de una URL.
    Primero intenta requests normal. Si falla, devuelve error descriptivo.
    """
    if not url:
        return ""

    # Normalizar URL
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        # Detectar encoding
        if resp.encoding and resp.encoding.lower() != "utf-8":
            resp.encoding = resp.apparent_encoding or "utf-8"

        content_type = resp.headers.get("content-type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return f"[NO HTML] La URL no devolvio HTML: {content_type}"

        text = resp.text[:15000]  # Limitar a 15K chars para DeepSeek
        return text

    except requests.exceptions.Timeout:
        return f"[ERROR] Timeout al acceder a {url}"
    except requests.exceptions.ConnectionError:
        return f"[ERROR] No se pudo conectar a {url}"
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] HTTP {e.response.status_code} en {url}"
    except Exception as e:
        return f"[ERROR] {e}"


def buscar_web_google(empresa: str, provincia: str) -> str:
    """
    Busca la web de una empresa en Google si no tiene web conocida.
    Devuelve la URL encontrada o string vacio.
    """
    query = f"{empresa} {provincia} sitio web oficial"
    print(f"  [BUSQUEDA] Buscando web para '{empresa}'...")

    try:
        params = {
            "q": query,
            "hl": "es",
            "num": 3,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(
            "https://www.google.com/search",
            params=params,
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()

        # Extraer URLs de resultados con regex basico
        import re
        urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
        for u in urls:
            # Filtrar resultados de Google (no anuncios, no google.com)
            parsed = urlparse(u)
            if "google" not in parsed.netloc and "youtube" not in parsed.netloc:
                # Limpiar URL de parametros de tracking
                clean = u.split("&")[0]
                print(f"    -> Posible web: {clean}")
                return clean

        print(f"    [NO] No se encontro web para '{empresa}'")
        return ""

    except Exception as e:
        print(f"    [WARN] Error en busqueda: {e}")
        return ""
