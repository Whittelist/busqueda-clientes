"""
Modulo 1: Google Maps Scraper
Usa Google Places API para buscar empresas por categoria y ubicacion.
Extrae: nombre, direccion, telefono, web, rating, reviews (texto), coordenadas.

API: Google Places API (Text Search + Place Details)
Docs: https://developers.google.com/maps/documentation/places/web-service/search-text
"""
import requests
import json
import time
from config import (
    GOOGLE_PLACES_API_KEY,
    PLACES_TEXTSEARCH_URL,
    PLACES_DETAILS_URL,
)


def _build_query(categoria: str, provincia: str) -> str:
    return f"{categoria} {provincia}"


def _text_search(query: str, pagetoken: str = None) -> dict:
    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "es",
    }
    if pagetoken:
        params["pagetoken"] = pagetoken

    resp = requests.get(PLACES_TEXTSEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _place_details(place_id: str) -> dict:
    params = {
        "place_id": place_id,
        "fields": "website,formatted_phone_number,international_phone_number,reviews,url",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "es",
    }
    try:
        resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception as e:
        print(f"  [WARN] Error obteniendo detalles de {place_id}: {e}")
    return {}


def _parse_result(result: dict, provincia: str, categoria: str) -> dict:
    place_id = result.get("place_id", "")

    details = {}
    if place_id:
        details = _place_details(place_id)
        time.sleep(0.05)

    reviews = details.get("reviews", [])
    reviews_clean = [
        {
            "author": r.get("author_name"),
            "rating": r.get("rating"),
            "text": r.get("text"),
            "time": r.get("relative_time_description"),
        }
        for r in reviews
    ]

    return {
        "place_id": place_id,
        "nombre": result.get("name", ""),
        "direccion": result.get("formatted_address", ""),
        "telefono": details.get("formatted_phone_number") or result.get("formatted_phone_number", ""),
        "website": details.get("website") or result.get("website", ""),
        "categoria": categoria,
        "rating": result.get("rating"),
        "total_reviews": result.get("user_ratings_total", 0),
        "reviews_json": json.dumps(reviews_clean, ensure_ascii=False),
        "provincia": provincia,
        "latitud": result.get("geometry", {}).get("location", {}).get("lat"),
        "longitud": result.get("geometry", {}).get("location", {}).get("lng"),
        "google_maps_url": details.get("url", ""),
        "business_status": result.get("business_status", ""),
    }


def buscar_empresas(categoria: str, provincia: str) -> list[dict]:
    """
    Busca empresas en una provincia para una categoria.
    Maneja paginacion automatica (hasta 3 paginas = ~60 resultados).
    """
    query = _build_query(categoria, provincia)
    print(f"\n[MAPS] Buscando: '{query}'")

    empresas = []
    pagetoken = None
    pagina = 1

    while pagina <= 3:
        try:
            data = _text_search(query, pagetoken)
            status = data.get("status", "")

            if status != "OK":
                if status == "ZERO_RESULTS":
                    print(f"  [INFO] Sin resultados en {provincia} para '{categoria}'")
                else:
                    print(f"  [ERROR] API returned {status}: {data.get('error_message', '')}")
                break

            results = data.get("results", [])
            print(f"  [Pagina {pagina}] {len(results)} resultados")

            for r in results:
                empresa = _parse_result(r, provincia, categoria)
                empresas.append(empresa)
                phone_tag = f' | tel:{empresa["telefono"]}' if empresa['telefono'] else ''
                web_tag = ' | web' if empresa['website'] else ''
                print(f"    [OK] {empresa['nombre']} | rating:{empresa['rating'] or '?'} | {empresa['total_reviews']} reviews{phone_tag}{web_tag}")

            pagetoken = data.get("next_page_token")
            if not pagetoken:
                break

            print("  -> Mas resultados... esperando 2s")
            time.sleep(2)
            pagina += 1

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] {e}")
            break

    print(f"  > Total en {provincia}: {len(empresas)} empresas")
    return empresas


def buscar_todo(categorias: list[str], provincias: list[str]) -> list[dict]:
    if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "tu_api_key_aqui":
        print("[FATAL] No has configurado GOOGLE_PLACES_API_KEY en .env")
        print("  Ve a https://console.cloud.google.com/apis/credentials")
        print("  Crea una API Key y habilita 'Places API'")
        return []

    todas = []
    total_general = 0

    for cat in categorias:
        for prov in provincias:
            empresas = buscar_empresas(cat, prov)
            if empresas:
                todas.extend(empresas)
                total_general += len(empresas)
            time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"[FINAL] Total empresas encontradas: {total_general}")
    print(f"{'='*50}")
    return todas
