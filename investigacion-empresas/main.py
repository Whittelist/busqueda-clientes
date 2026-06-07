#!/usr/bin/env python3
"""
Modulo de Investigacion y Enriquecimiento de Empresas.

Para cada empresa del Sheet sin datos en Q (problema), R (idea_mejora) o U (tamano):
1. Scrapea TODO el sitio web (BFS crawl completo)
2. Envia contenido a DeepSeek para analisis
3. Escribe resultados en el Sheet

Uso:
    python main.py                    # dry-run por defecto
    python main.py --no-dry-run       # escritura real en Sheet
    python main.py --limit 10         # solo 10 empresas
    python main.py --no-dry-run --limit 5
"""
import sys, os, time, argparse
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(encoding="utf-8-sig")

from config import DELAY_BETWEEN_COMPANIES, MAX_COMPANIES_PER_RUN, DEEPSEEK_API_KEY
from sheets_client import sheets_service, leer_pendientes, escribir_resultados
from web_fetcher import fetch_sitio_completo
from investigador import investigar_empresa


def main():
    start = time.time()
    parser = argparse.ArgumentParser(description="Investigacion y Enriquecimiento de Empresas")
    parser.add_argument("--no-dry-run", action="store_true", help="Escribe en el Sheet (por defecto es dry-run)")
    parser.add_argument("--limit", type=int, default=None, help="Max empresas a procesar")
    parser.add_argument("--force", action="store_true", help="Omitir confirmacion interactiva")
    args = parser.parse_args()

    is_dry_run = not args.no_dry_run
    limit = args.limit or MAX_COMPANIES_PER_RUN

    if not DEEPSEEK_API_KEY:
        print("[ERROR] DEEPSEEK_API_KEY no configurada. Copia .env.example a .env")
        sys.exit(1)

    print("=" * 60)
    print("  INVESTIGACION DE EMPRESAS - Enriquecimiento automatico")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Dry-run: {is_dry_run}")
    print(f"  Limite: {limit} empresas")
    print("=" * 60)

    print("\n[1/3] Leyendo empresas pendientes del Sheet...")
    service = sheets_service()
    pendientes = leer_pendientes(service)
    total_pendientes = len(pendientes)

    if total_pendientes == 0:
        print("\n[!] No hay empresas pendientes. Todas tienen Q, R, U rellenos.")
        return

    print(f"  {total_pendientes} empresas pendientes encontradas")
    pendientes = pendientes[:limit]
    print(f"  Procesando {len(pendientes)} empresas en esta ejecucion\n")

    if not is_dry_run and not args.force:
        print(f"  [!] ATENCION: Se escribiran datos REALES en el Sheet")
        confirm = input(f"  Continuar? (s/N): ").strip().lower()
        if confirm != "s":
            print("  Abortado por usuario.")
            return

    procesadas = 0
    errores = 0
    saltadas = 0
    fallbacks = 0

    for i, empresa in enumerate(pendientes, 1):
        print(f"\n--- [{i}/{len(pendientes)}] {empresa.nombre} ({empresa.provincia}) ---")

        if not empresa.nombre:
            print("  [SALTADO] Sin nombre")
            saltadas += 1
            continue

        contenido_web = ""
        if empresa.web and empresa.web.lower() not in ("", "no se encontro", "no disponible"):
            print(f"  [WEB] {empresa.web}")
            contenido_web = fetch_sitio_completo(empresa.web)
            time.sleep(0.5)
        else:
            print("  [SIN WEB] No tiene web disponible")

        print("  [IA] Analizando con DeepSeek...")
        resultado = investigar_empresa(
            nombre=empresa.nombre,
            provincia=empresa.provincia,
            categoria=empresa.categoria,
            web=empresa.web,
            contenido_web=contenido_web,
        )

        es_fallback = resultado.get("es_fallback", False)

        print(f"  Problema: {resultado['problema']}")
        print(f"  Mejora:   {resultado['mejora']}")
        print(f"  Tamano:   {resultado['tamano']}")

        if es_fallback:
            fallbacks += 1

        if not is_dry_run:
            if es_fallback:
                print("  [SALTADO] Resultado es fallback (DeepSeek no respondio bien). No se escribe en Sheet para evitar datos placeholder.")
                errores += 1
            else:
                notas = f"Web: {empresa.web}" if empresa.web else "Sin web"
                escribir_resultados(service, empresa, resultado["problema"], resultado["mejora"], resultado["tamano"], notas)
                print("  [SHEET] Escrito en columnas Q, R, U")
                procesadas += 1
        else:
            if es_fallback:
                print("  [DRY-RUN] Resultado seria saltado (fallback)")
            else:
                print("  [DRY-RUN] No se escribe en Sheet")
            procesadas += 1

        if i < len(pendientes):
            print(f"  [ESPERA] {DELAY_BETWEEN_COMPANIES}s...")
            time.sleep(DELAY_BETWEEN_COMPANIES)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  [OK] COMPLETADO en {elapsed:.1f}s")
    print(f"  Procesadas: {procesadas}")
    print(f"  Fallbacks (no escritos): {fallbacks}")
    print(f"  Errores:    {errores}")
    print(f"  Saltadas:   {saltadas}")
    print(f"  Pendientes restantes: {total_pendientes - procesadas}")
    if is_dry_run:
        print(f"\n  [DRY-RUN] Para escribir en el Sheet, ejecuta: python main.py --no-dry-run")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrumpido por usuario")
        sys.exit(0)
