import requests
import re
import time
from urllib.parse import urljoin, urlparse
from config import WEB_FETCH_TIMEOUT, WEB_FETCH_MAX_PAGES, WEB_FETCH_MAX_CHARS, WEB_FETCH_DELAY

import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

EXCLUDE_PATH_PATTERNS = [
    r'/cdn-cgi/', r'/wp-json/', r'/feed/', r'/xmlrpc\.php',
    r'wp-.*\.php', r'/trackback/', r'/comment',
    r'/cart', r'/checkout', r'/my-account', r'/login', r'/logout',
    r'/register', r'/signup', r'/signin',
    r'/lost-password', r'/reset-password',
    r'/add-to-cart', r'/remove', r'/wishlist',
    r'\.pdf$', r'\.zip$', r'\.rar$', r'\.jpg$', r'\.jpeg$',
    r'\.png$', r'\.gif$', r'\.svg$', r'\.ico$', r'\.css$', r'\.js$',
    r'\.xml$', r'\.json$', r'\.txt$',
    r'/page/', r'/page/\d+',
    r'/amp/', r'/amp$',
    r'javascript:', r'mailto:', r'tel:',
]

EXCLUDE_QUERY_PATTERNS = [
    r'page=', r'paged=', r'limit=', r'offset=', r'start=',
]


def _debe_excluir(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    fragment = parsed.fragment.lower()

    combined_path = path + fragment
    for pat in EXCLUDE_PATH_PATTERNS:
        if re.search(pat, combined_path):
            return True

    for pat in EXCLUDE_QUERY_PATTERNS:
        if re.search(pat, query):
            return True

    return False


def _html_a_texto(html: str) -> str:
    if not html or html.startswith("["):
        return html
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "meta", "noscript", "link", "svg", "path"]):
            tag.decompose()
        texto = soup.get_text(separator="\n")
        lineas = [l.strip() for l in texto.split("\n") if l.strip()]
        return "\n".join(lineas)
    except ImportError:
        texto = re.sub(r'<[^>]+>', ' ', html)
        texto = re.sub(r'\s+', ' ', texto)
        return texto


def fetch_url(url: str, timeout: int = None) -> tuple:
    """
    Obtiene contenido de una URL.
    Retorna (texto_visible, content_type, status_code, raw_html).
    """
    if not url:
        return "", None, 0, ""

    timeout = timeout or WEB_FETCH_TIMEOUT
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
            return f"[NO HTML] {content_type}", content_type, resp.status_code, ""

        texto_visible = _html_a_texto(resp.text)
        return texto_visible, content_type, resp.status_code, resp.text

    except requests.exceptions.Timeout:
        return "", None, 0, ""
    except requests.exceptions.ConnectionError:
        return "", None, 0, ""
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 0
        return "", None, status, ""
    except Exception:
        return "", None, 0, ""


def _extraer_links(html: str, base_url: str) -> list[str]:
    """Extrae todos los href de una pagina HTML usando BeautifulSoup."""
    if not html:
        return []
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        urls = set()
        base_domain = urlparse(base_url).netloc
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            full = urljoin(base_url, href)
            if urlparse(full).netloc == base_domain:
                urls.add(full)
        return list(urls)
    except ImportError:
        urls = re.findall(r'href="([^"]+)"', html)
        absolutos = []
        for u in urls:
            if u and not u.startswith("#") and not u.startswith("javascript"):
                full = urljoin(base_url, u)
                if urlparse(full).netloc == urlparse(base_url).netloc:
                    absolutos.append(full)
        return list(set(absolutos))


def fetch_sitio_completo(url: str, max_paginas: int = None, max_chars: int = None) -> str:
    """
    BFS crawl completo del sitio web de la empresa.
    Descubre todas las rutas internas, visita hasta max_paginas,
    extrae texto visible de cada una y combina todo.
    """
    if not url:
        return ""

    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    max_paginas = max_paginas or WEB_FETCH_MAX_PAGES
    max_chars = max_chars or WEB_FETCH_MAX_CHARS
    base_domain = urlparse(url).netloc

    visitadas = set()
    por_visitar = [url]
    encoladas = {url}
    contenidos = []

    while por_visitar and len(visitadas) < max_paginas:
        current = por_visitar.pop(0)

        if current in visitadas:
            continue

        parsed = urlparse(current)
        if parsed.netloc != base_domain:
            continue

        if _debe_excluir(current):
            continue

        visitadas.add(current)

        texto, _, _, raw_html = fetch_url(current)
        if not texto:
            continue

        etiqueta = "PRINCIPAL" if current == url else parsed.path.rstrip("/").split("/")[-1]
        contenidos.append(f"\n--- {etiqueta} ({current}) ---\n{texto}")

        # Extraer enlaces de esta pagina y encolar nuevas URLs
        if raw_html:
            nuevos = _extraer_links(raw_html, current)
            for enlace in nuevos:
                if enlace not in visitadas and enlace not in encoladas:
                    if not _debe_excluir(enlace):
                        por_visitar.append(enlace)
                        encoladas.add(enlace)

        time.sleep(WEB_FETCH_DELAY * 0.3)

    if not contenidos:
        return ""

    combinado = contenidos[0][:5000] if contenidos else ""
    for c in contenidos[1:]:
        combinado += "\n\n" + c[:8000]
    if len(combinado) > max_chars:
        combinado = combinado[:max_chars]

    paginas = len(visitadas)
    print(f"  [FETCH] {paginas} pagina(s) visitada(s), {len(combinado)} chars")
    return combinado
