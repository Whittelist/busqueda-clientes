"""
Contenido web: fetch de paginas con extraccion de TEXTO VISIBLE (Ctrl+A).
Busca: pagina principal + contacto + quienes-somos + aviso-legal.
Extrae solo el texto visible, NO el HTML crudo.
"""
import requests
import re
import time
from urllib.parse import urljoin, urlparse


def _html_a_texto(html: str) -> str:
    """
    Convierte HTML a texto plano visible (como Ctrl+A + Ctrl+V).
    Elimina scripts, styles, metadata, y deja solo el texto que se ve.
    """
    if not html or html.startswith("["):
        return html
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        # Eliminar elementos no visibles
        for tag in soup(["script", "style", "meta", "noscript", "link", "svg", "path"]):
            tag.decompose()
        texto = soup.get_text(separator="\n")
        # Limpiar lineas vacias multiples
        lineas = [l.strip() for l in texto.split("\n") if l.strip()]
        return "\n".join(lineas)
    except ImportError:
        # Fallback: regex basico para extraer texto (sin bs4)
        texto = re.sub(r'<[^>]+>', ' ', html)
        texto = re.sub(r'\s+', ' ', texto)
        return texto


def fetch_url(url: str, timeout: int = 15) -> tuple:
    """
    Obtiene el contenido de una URL.
    Retorna (texto_visible, content_type, status_code) o (error_msg, None, 0).
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

        # Convertir HTML a texto visible (Ctrl+A)
        texto_visible = _html_a_texto(resp.text)
        return texto_visible, content_type, resp.status_code

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


def _fetch_url_raw(url: str, timeout: int = 15) -> str:
    """Devuelve el HTML original (solo para extraer enlaces)."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except:
        return ""


def fetch_con_profundidad(url: str, max_paginas: int = 4) -> str:
    """
    Fetch de la pagina principal + subpaginas de contacto.
    1. Obtiene HTML original para extraer enlaces a contacto
    2. Convierte CADA pagina a texto visible (Ctrl+A)
    3. Combina todo
    """
    base_domain = urlparse(url).netloc
    visitadas = set()
    por_visitar = [url]
    contenidos = []

    while por_visitar and len(visitadas) < max_paginas:
        current = por_visitar.pop(0)
        if current in visitadas:
            continue
        if urlparse(current).netloc != base_domain:
            continue

        # Si es la principal, obtener RAW primero para extraer links
        if current == url:
            html_raw = _fetch_url_raw(url)
            enlaces = _extraer_links(html_raw, url) if html_raw else []
            for enlace in enlaces:
                if enlace not in visitadas and _es_pagina_contacto(enlace):
                    por_visitar.append(enlace)
                    print(f"    -> Subpagina encontrada: {urlparse(enlace).path}")

        # Obtener texto visible
        texto, _, status = fetch_url(current)
        visitadas.add(current)

        if texto and texto.startswith("[ERROR]"):
            continue

        etiqueta = "PRINCIPAL" if current == url else current.split("/")[-1]
        contenidos.append(f"\n--- PAGINA: {etiqueta} ({current}) ---\n{texto}")
        time.sleep(0.5)

    paginas = len(visitadas)
    if not contenidos:
        return ""

    # Combinar con limites generosos (texto visible es compacto)
    combinado = contenidos[0][:5000] if contenidos else ""
    for c in contenidos[1:]:
        combinado += "\n\n" + c[:8000]
    if len(combinado) > 25000:
        combinado = combinado[:25000]

    print(f"  [FETCH] {paginas} pagina(s) visitada(s), {len(combinado)} chars total")
    return combinado


def _ddgs_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Busca en DuckDuckGo (no bloquea como Google).
    Retorna lista de dicts con title, href, body.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"titulo": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")[:200]}
            for r in results
        ]
    except ImportError:
        print("    [WARN] duckduckgo_search no instalado. pip install duckduckgo_search")
        return []
    except Exception as e:
        print(f"    [WARN] Error en DuckDuckGo: {e}")
        return []


def buscar_web_google(empresa: str, provincia: str) -> str:
    """
    Busca la web oficial de una empresa con DuckDuckGo + DeepSeek.
    1. Busca en DuckDuckGo
    2. Si hay varios resultados, DeepSeek elige la web oficial
    3. Devuelve la URL o ""
    """
    query = f'{empresa} {provincia}'
    print(f"  [BUSQUEDA] Buscando web para '{empresa}'...")

    resultados = _ddgs_search(query)
    
    if not resultados:
        print(f"    [NO] Sin resultados")
        return ""
    
    print(f"    Resultados: {len(resultados)}")
    for r in resultados:
        print(f"      {r['url']}")
    
    # Si solo hay 1 resultado, usarlo directamente
    if len(resultados) == 1:
        url = resultados[0]["url"]
        print(f"    -> Directo: {url}")
        return url
    
    # Varios resultados -> DeepSeek elige
    from deepseek_client import _consultar_deepseek
    
    prompt = f"""Eres un asistente que identifica la web OFICIAL de una empresa.

Empresa: "{empresa}"

Resultados:"""
    for i, r in enumerate(resultados, 1):
        prompt += f'\n{i}. TITULO: {r["titulo"]}\n   URL: {r["url"]}'
    
    prompt += f'\n\nResponde SOLO con el numero de la web OFICIAL. 0 si ninguna es clara.\nRespuesta:'
    
    respuesta = _consultar_deepseek(prompt, max_tokens=10)
    
    try:
        idx = int(respuesta.strip())
        if 1 <= idx <= len(resultados):
            url = resultados[idx - 1]["url"]
            print(f"    -> DeepSeek (#{idx}): {url}")
            return url
    except (ValueError, IndexError):
        pass
    
    print(f"    [NO] No se identifico web oficial")
    return ""
