"""
Contenido web: fetch de paginas con seguimiento de enlaces a contacto.
Busca: pagina principal + contacto + quienes-somos + aviso-legal.
Acumula todo el contenido para enviar a DeepSeek.
"""
import requests
import re
import time
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser


class LinkFinder(HTMLParser):
    """Extrae enlaces de una pagina HTML."""
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            text_lower = attrs_dict.get("text", "").lower()
            if href and not href.startswith("#") and not href.startswith("javascript"):
                full_url = urljoin(self.base_url, href)
                self.links.append(full_url)

    def handle_data(self, data):
        # Store the last text node for context (not perfect but helps)
        pass


def fetch_url(url: str, timeout: int = 15) -> tuple:
    """
    Obtiene el contenido de una URL.
    Retorna (texto, content_type, status_code) o (error_msg, None, 0).
    """
    if not url:
        return "", None, 0

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

        content_type = resp.headers.get("content-type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return f"[NO HTML] {content_type}", content_type, resp.status_code

        return resp.text, content_type, resp.status_code

    except requests.exceptions.Timeout:
        return f"[ERROR] Timeout", None, 0
    except requests.exceptions.ConnectionError:
        return f"[ERROR] No conexion", None, 0
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] HTTP {e.response.status_code}", None, e.response.status_code
    except Exception as e:
        return f"[ERROR] {e}", None, 0


def _extraer_links(html: str, base_url: str) -> list[str]:
    """Extrae todos los href de una pagina HTML."""
    # Regex simple para href
    urls = re.findall(r'href="([^"]+)"', html)
    absolutos = []
    for u in urls:
        if u and not u.startswith("#") and not u.startswith("javascript"):
            full = urljoin(base_url, u)
            # Solo URLs del mismo dominio
            if urlparse(full).netloc == urlparse(base_url).netloc:
                absolutos.append(full)
    return list(set(absolutos))


def _es_pagina_contacto(url: str, texto_enlace: str = "") -> bool:
    """Detecta si una URL es de contacto, quienes-somos, aviso-legal."""
    path = urlparse(url).path.lower()
    palabras_clave = [
        "contact", "contacto", "contact-us",
        "quienes-somos", "quienes_somos", "about", "about-us",
        "nosotros", "la-empresa", "empresa",
        "aviso-legal", "aviso_legal", "legal",
        "informacion", "information",
        "direccion", "dirección",
    ]
    for kw in palabras_clave:
        if kw in path:
            return True
    # Tambien revisar el texto del enlace si se proporciona
    texto_lower = texto_enlace.lower()
    for kw in palabras_clave:
        if kw in texto_lower:
            return True
    return False


def fetch_con_profundidad(url: str, max_paginas: int = 4) -> str:
    """
    Fetch de la pagina principal + subpaginas de contacto.
    Retorna todo el contenido combinado.
    """
    base_domain = urlparse(url).netloc
    visitadas = set()
    por_visitar = [url]
    contenidos = []

    while por_visitar and len(visitadas) < max_paginas:
        current = por_visitar.pop(0)
        if current in visitadas:
            continue

        # Solo mismo dominio
        if urlparse(current).netloc != base_domain:
            continue

        texto, _, status = fetch_url(current)
        visitadas.add(current)

        if texto and texto.startswith("[ERROR]"):
            continue

        etiqueta = "PRINCIPAL" if current == url else current.split("/")[-1]
        contenidos.append(f"\n--- PAGINA: {etiqueta} ({current}) ---\n{texto}")

        # Si es la pagina principal, buscar enlaces a contacto
        if current == url:
            enlaces = _extraer_links(texto, url)
            for enlace in enlaces:
                if enlace not in visitadas and _es_pagina_contacto(enlace):
                    por_visitar.append(enlace)
                    print(f"    -> Subpagina encontrada: {urlparse(enlace).path}")

        time.sleep(0.5)

    # Limitar cada pagina individualmente (no el total)
    # La pagina principal hasta 12K, subpaginas hasta 10K cada una
    # Pagina principal 15K, subpaginas SIN LIMITE (enteras)
    # Las subpaginas de contacto tienen la info al final, tras mucho HTML
    combinado = contenidos[0][:15000] if contenidos else ""
    for c in contenidos[1:]:
        combinado += "\n\n" + c
    # Limite total generoso: 80K (DeepSeek Flash tiene 1M contexto)
    if len(combinado) > 80000:
        combinado = combinado[:80000]

    paginas = len(visitadas)
    print(f"  [FETCH] {paginas} pagina(s) visitada(s), {len(combinado)} chars total")
    return combinado


def buscar_web_google(empresa: str, provincia: str) -> str:
    """Busca la web de una empresa en Google."""
    query = f"{empresa} {provincia} sitio web oficial"
    print(f"  [BUSQUEDA] Buscando web para '{empresa}'...")

    try:
        params = {"q": query, "hl": "es", "num": 3}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(
            "https://www.google.com/search", params=params, headers=headers, timeout=10
        )
        resp.raise_for_status()

        urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
        for u in urls:
            parsed = urlparse(u)
            if "google" not in parsed.netloc and "youtube" not in parsed.netloc:
                clean = u.split("&")[0]
                print(f"    -> Posible web: {clean}")
                return clean

        print(f"    [NO] No se encontro web")
        return ""

    except Exception as e:
        print(f"    [WARN] Error: {e}")
        return ""
