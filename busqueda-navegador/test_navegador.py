"""
Test rapido del modulo navegador con 1 empresa.
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_empresas_pendientes, guardar_enrichment
from web_fetcher import fetch_url
from deepseek_client import extraer_datos

init_db()
pendientes = get_empresas_pendientes()

if not pendientes:
    print("[!] No hay empresas pendientes. Todas procesadas o BD no encontrada.")
    sys.exit(1)

# Probar solo 1
emp = pendientes[0]
print(f"\n[TEST] Procesando: {emp['nombre']} | web: {emp.get('website', 'sin web')}")

website = emp.get("website", "")
if not website:
    print("[TEST] Sin web - saltando...")
else:
    contenido = fetch_url(website)
    print(f"[TEST] Contenido obtenido: {len(contenido)} chars")

    datos = extraer_datos(contenido, emp["nombre"], website)
    datos["nombre"] = emp["nombre"]
    datos["provincia"] = emp["provincia"]
    datos["website"] = website

    print(f"\n[RESULTADO]")
    print(f"  Emails: {datos.get('email_encontrados', [])}")
    print(f"  Problema: {datos.get('problema_detectado', '')}")
    print(f"  Mejora: {datos.get('idea_mejora', '')}")
    print(f"  Tamano: {datos.get('tamano_empresa', '')}")
    print(f"  Telefono: {datos.get('telefono_contacto', '')}")
    print(f"  Persona: {datos.get('persona_contacto', '')}")

    guardar_enrichment(emp["id"], datos)
    print(f"\n[OK] Guardado en BD de enrichment")
