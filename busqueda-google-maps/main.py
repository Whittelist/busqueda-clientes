#!/usr/bin/env python3
"""
Cliente Finder - Orquestador principal.
Ejecuta el pipeline completo: scrape > BD > CSV.

Uso basico:
    python main.py

Primera vez:
    1. Copia .env.example a .env
    2. Pon tu API key de Google Places
    3. Ejecuta este script
"""
import sys
import time
from datetime import datetime

from config import CATEGORIAS, PROVINCIAS_ACTIVAS, COMUNIDAD_ACTIVA, CSV_OUTPUT
from database import init_db, insertar_empresa, registrar_busqueda, exportar_csv, resumen
from maps_scraper import buscar_todo


def main():
    start = time.time()
    print("=" * 60)
    print("  CLIENTE FINDER - Prospeccion Automatizada")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    init_db()

    print(f"  Buscando en: {COMUNIDAD_ACTIVA}")
    empresas = buscar_todo(
        categorias=CATEGORIAS,
        provincias=PROVINCIAS_ACTIVAS,
    )

    if not empresas:
        print("\n[!] No se encontraron empresas. Revisa:")
        print("  1. Que GOOGLE_PLACES_API_KEY este configurada en .env")
        print("  2. Que la API de Places este habilitada en Google Cloud Console")
        print("  3. Que las categorias tengan resultados en las provincias indicadas")
        sys.exit(1)

    nuevas = 0
    duplicados = 0
    for emp in empresas:
        if insertar_empresa(emp):
            nuevas += 1
        else:
            duplicados += 1

    for cat in CATEGORIAS:
        for prov in PROVINCIAS_ACTIVAS:
            total_x_prov = sum(1 for e in empresas if e["provincia"] == prov)
            if total_x_prov > 0:
                registrar_busqueda(cat, prov, total_x_prov)

    total_csv = exportar_csv(CSV_OUTPUT)
    stats = resumen()

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  [OK] COMPLETADO en {elapsed:.1f}s")
    print(f"  Total en BD:     {stats['total']}")
    print(f"  Nuevas hoy:      {nuevas}")
    print(f"  Duplicados:      {duplicados}")
    print(f"  CSV exportado:   {total_csv} empresas")
    print(f"  {CSV_OUTPUT}")
    print(f"\n  Por provincia:")
    for prov, cnt in stats["por_provincia"].items():
        print(f"    - {prov}: {cnt}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
