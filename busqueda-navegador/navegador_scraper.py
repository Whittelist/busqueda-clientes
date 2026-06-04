#!/usr/bin/env python3
"""
Modulo 2: Busqueda Navegador
Para cada empresa del Modulo 1 que NO haya sido procesada aun:
- Si tiene web: fetch + extraer emails con regex
- Si no tiene web: buscar en Google + fetch + extraer emails
- Guarda resultados

Uso:
    python navegador_scraper.py
"""
import sys, os, time, re
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

# Asegurar que estamos en el directorio correcto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_empresas_pendientes, guardar_enrichment, exportar_csv
from web_fetcher import fetch_con_profundidad, buscar_web_google
from config import ENRICHED_DB


def extraer_emails(contenido: str) -> list[str]:
    """Extrae emails del texto plano con regex."""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contenido or "")
    validos = [e for e in emails if not e.endswith(('.png', '.jpg', '.gif', '.svg', '.css', '.js'))]
    mailtos = re.findall(r'mailto:([^"\'<>\s]+)', contenido or "")
    todos = list(set(validos + mailtos))
    return todos


def extraer_telefonos(contenido: str) -> list[str]:
    """Extrae telefonos espanoles del texto plano con regex."""
    nums = re.findall(r'(?:\+34)?[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{3}', contenido or "")
    unicos = list(set(nums))
    return unicos


def procesar_empresa(empresa: dict) -> bool:
    """
    Procesa una empresa: busca web si no tiene, fetch, extraer emails, guarda.
    Retorna True si se proceso correctamente.
    """
    nombre = empresa["nombre"]
    provincia = empresa["provincia"]
    website = empresa.get("website", "") or ""

    print(f"\n{'='*60}")
    print(f"[{nombre}] ({provincia})")

    # 1. Si no tiene web, intentar buscar
    if not website or website == "No se encontro":
        print("  [NO WEB] Buscando en Google...")
        website = buscar_web_google(nombre, provincia)
        if not website:
            print("  [SIN WEB] No se encontro web. Guardando como pendiente...")
            guardar_enrichment(empresa["id"], {
                "nombre": nombre,
                "provincia": provincia,
                "website": "",  # no sobreescribir col D
                "email_encontrados": [],
                "telefono_contacto": "",
                "persona_contacto": "",
            })
            return True
        time.sleep(1)

    # 2. Fetch web
    print(f"  [FETCH] {website}")
    contenido = fetch_con_profundidad(website)

    # 3. Extraer emails y telefonos con regex
    emails = extraer_emails(contenido)
    telefonos = extraer_telefonos(contenido)

    # 4. Mostrar resultados
    if emails:
        print(f"  [EMAILS] {', '.join(emails)}")
    else:
        print(f"  [EMAILS] No encontrados")
    if telefonos:
        print(f"  [TLF] {', '.join(telefonos)}")

    # 5. Guardar en BD
    datos = {
        "nombre": nombre,
        "provincia": provincia,
        "website": website,
        "email_encontrados": emails,
        "telefono_contacto": ", ".join(telefonos) if telefonos else "",
        "persona_contacto": "",
    }
    guardar_enrichment(empresa["id"], datos)
    print(f"  [OK] Guardado")

    return True


def main():
    start = time.time()
    print(f"{'='*60}")
    print(f"  NAVEGADOR - Busqueda y enrichment de empresas")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    init_db()

    pendientes = get_empresas_pendientes()
    if not pendientes:
        print("\n[!] No hay empresas pendientes de procesar.")
        print("  O bien todas estan procesadas o no hay datos del Modulo 1.")
        return

    print(f"\n[INFO] {len(pendientes)} empresas pendientes de procesar\n")

    procesadas = 0
    errores = 0

    for i, empresa in enumerate(pendientes, 1):
        print(f"\n[{i}/{len(pendientes)}]", end="")
        try:
            ok = procesar_empresa(empresa)
            if ok:
                procesadas += 1
            else:
                errores += 1
        except KeyboardInterrupt:
            print("\n\n[!] Interrumpido por usuario")
            break
        except Exception as e:
            print(f"\n  [ERROR INESPERADO] {e}")
            errores += 1

        # Pausa entre empresas para no saturar
        time.sleep(1)

    # Exportar CSV de enrichment
    csv_path = os.path.join(os.path.dirname(__file__), "data", "enriched.csv")
    exportar_csv(csv_path)

    # Subir resultados al sheet automaticamente
    print(f"\n  [PUSH] Subiendo resultados al sheet...")
    from push_to_sheets import push_enriched
    push_enriched()

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  [OK] COMPLETADO en {elapsed:.1f}s")
    print(f"  Procesadas: {procesadas}")
    print(f"  Errores:    {errores}")
    print(f"  {csv_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
