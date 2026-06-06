#!/usr/bin/env python3
"""
Campaign Runner - Orquestador principal de la campana de emails.

Uso:
    python campaign_runner.py                 # Produccion: envia emails reales
    python campaign_runner.py --draft          # Test: crea borradores + actualiza Sheet
    python campaign_runner.py --dry-run        # Simulacion: no toca nada
    python campaign_runner.py --test           # 5 borradores, no toca Sheet
    python campaign_runner.py --auth           # Re-autorizar OAuth
"""
import sys, os, time
from datetime import datetime
from zoneinfo import ZoneInfo

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from config import (
    DRY_RUN, DAILY_LIMIT, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS,
    TIMEZONE, FROM_EMAIL, SCOPES, TOKEN_PATH, SPREADSHEET_ID, COL_INDEX
)
from sheets_tracker import (
    sheets_service, leer_empresas, local_hoy, actualizar_tracking
)
from gmail_client import gmail_service, send_email, create_draft, detectar_respuestas, obtener_thread_id_por_email
from email_composer import generar_email, FIRMA


def auth_flow():
    print("=" * 60)
    print("  AUTENTICACION GOOGLE")
    print("  Se abrira el navegador para autorizar Gmail + Sheets")
    print("=" * 60)

    from google_auth_oauthlib.flow import InstalledAppFlow

    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("[ERROR] Define GOOGLE_OAUTH_CLIENT_ID y GOOGLE_OAUTH_CLIENT_SECRET en .env")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        SCOPES,
    )

    oauth_port = int(os.getenv("GOOGLE_OAUTH_PORT", "8080"))
    try:
        creds = flow.run_local_server(port=oauth_port, prompt="consent")
    except Exception as e:
        if "redirect_uri_mismatch" in str(e):
            print(f"\n[ERROR] redirect_uri_mismatch. Anade en Google Cloud Console:")
            print(f"  http://localhost:{oauth_port}/")
        else:
            print(f"[ERROR] {e}")
        sys.exit(1)

    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n[OK] Token guardado en {TOKEN_PATH}")
    print(f"  Scopes: {', '.join(creds.scopes or [])}")


def paso_detectar_respuestas(gmail_svc, sheets_svc):
    """Detecta respuestas en inbox y marca como respondido en Sheet."""
    print(f"\n{'='*60}")
    print(f"  PASO 1: Detectando respuestas en inbox...")
    print(f"{'='*60}")

    respuestas = detectar_respuestas(gmail_svc)
    if not respuestas:
        print("  No se detectaron nuevas respuestas.")
        return

    empresas = leer_empresas(sheets_svc)
    marcadas = 0

    for r in respuestas:
        print(f"    [REPLY] De: {r['email_origen']} | Asunto: {r['subject'][:60]}")

        encontrada = False
        for emp in empresas:
            if emp.contiene_email(r["email_origen"]):
                if emp.estado == "respondido":
                    print(f"      [SKIP] {emp.nombre} ya estaba marcado como respondido")
                    encontrada = True
                    break

                col_estado_idx = COL_INDEX.get("estado")
                if col_estado_idx is not None:
                    col_letter = chr(65 + col_estado_idx)
                    cell = f"'TEST EMPRESAS BOT 2'!{col_letter}{emp.row_number}"
                    try:
                        sheets_svc.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=cell,
                            valueInputOption="USER_ENTERED",
                            body={"values": [["respondido"]]}
                        ).execute()
                        print(f"      -> Marcado como respondido en Sheet ({emp.nombre})")
                        marcadas += 1
                    except Exception as e:
                        print(f"      [WARN] Error actualizando Sheet: {e}")
                encontrada = True
                break

        if not encontrada:
            print(f"      [INFO] No se encontro empresa con ese email en el Sheet")

    print(f"  [OK] Paso 1 completado - {marcadas} empresa(s) marcada(s) como respondido")


def generar_asunto(emp, touch: int) -> str:
    """Genera asunto corto, en minusculas, personalizado por empresa, sin lenguaje de ventas."""
    nombre_corto = emp.nombre.split(",")[0].split("S.L")[0].split("-")[0].strip()
    palabras = nombre_corto.split()
    if len(nombre_corto) > 18:
        nombre_corto = " ".join(palabras[:2])

    pain_points = [
        "papel y albaranes",
        "documentacion y papel",
        "procesos manuales",
        "desorganizacion",
        "sin erp",
        "tareas repetitivas",
        "albaranes en papel",
        "registros a mano",
        "organizar papeles",
        "control de obra",
    ]
    pp = pain_points[(hash(emp.nombre) + touch) % len(pain_points)]

    subjects = {
        1: f"{nombre_corto.lower()}, {pp}",
        2: f"{nombre_corto.lower()}, otra idea",
        3: f"{nombre_corto.lower()}, una reflexion",
        4: f"{nombre_corto.lower()}, ?seguis en papel?",
        5: f"{nombre_corto.lower()}, sin presion",
    }
    return subjects.get(touch, f"{nombre_corto.lower()}, {pp}")


def paso_enviar_emails(gmail_svc, sheets_svc, dry_run: bool, test_mode: bool = False, draft_mode: bool = False):
    """Clasifica candidatos, prioriza y envia."""
    hoy = local_hoy()

    print(f"\n{'='*60}")
    print(f"  PASO 2: Leyendo empresas del Sheet...")
    print(f"{'='*60}")

    empresas = leer_empresas(sheets_svc)
    print(f"  {len(empresas)} empresas encontradas")

    candidatas = []
    for emp in empresas:
        if not emp.tiene_email_valido():
            continue
        touch_needed = emp.necesita_touch(hoy)
        if touch_needed is not None:
            candidatas.append((emp, touch_needed))

    print(f"  {len(candidatas)} empresa(s) necesita(n) email hoy")

    if not candidatas:
        print("\n  No hay empresas para contactar hoy.")
        return

    candidatas.sort(key=lambda x: x[1], reverse=True)

    if test_mode:
        candidatas = candidatas[:5]
        print(f"\n  [TEST] Limitado a 5 empresas")

    print(f"\n{'='*60}")
    print(f"  PASO 3: Procesando emails (max {DAILY_LIMIT}/dia)")
    print(f"{'='*60}")

    if dry_run:
        print("  [DRY RUN] Solo simulacion — no se crea nada, no se actualiza Sheet")
    if test_mode:
        print("  [TEST] 5 borradores en Gmail — no se actualiza Sheet")
    if draft_mode:
        print("  [DRAFT] Borradores en Gmail + Sheet actualizado (como produccion)")

    enviados = 0
    for emp, touch in candidatas:
        if enviados >= DAILY_LIMIT:
            print(f"  [LIMITE] Alcanzado maximo de {DAILY_LIMIT} envios por dia")
            break

        print(f"\n  --- [{touch}/5] {emp.nombre} ({emp.provincia}) ---")

        try:
            cuerpo = generar_email(
                nombre=emp.nombre,
                categoria=emp.categoria,
                provincia=emp.provincia,
                problema=emp.problema,
                idea=emp.idea_mejora,
                tamano=emp.tamano,
                web=emp.web,
                touch=touch,
                contexto_extra=emp.contexto_completo(),
            )
        except Exception as e:
            print(f"    [ERROR IA] {e}")
            continue

        asunto = generar_asunto(emp, touch)

        print(f"    Asunto: {asunto}")
        print(f"    Para: {emp.mejor_email()}")
        preview = cuerpo[:120].replace("\n", " ").strip()
        print(f"    Preview: {preview}...")

        if dry_run:
            enviados += 1
            continue

        if test_mode:
            create_draft(gmail_svc, emp.mejor_email(), asunto, cuerpo)
            enviados += 1
            continue

        if draft_mode:
            create_draft(gmail_svc, emp.mejor_email(), asunto, cuerpo)
            try:
                actualizar_tracking(sheets_svc, emp, touch, hoy, asunto)
                print(f"    [SHEET] Tracking actualizado (estado={touch}, num_contactos={touch})")
            except Exception as e:
                print(f"    [WARN] Error actualizando Sheet: {e}")
            enviados += 1
            time.sleep(MIN_DELAY_SECONDS)
            continue

        # --- PRODUCCION: enviar email real ---
        thread_id = None
        if touch > 1:
            thread_id = obtener_thread_id_por_email(gmail_svc, emp.mejor_email())

        exito, msg = send_email(gmail_svc, emp.mejor_email(), asunto, cuerpo, thread_id=thread_id)

        if exito:
            try:
                actualizar_tracking(sheets_svc, emp, touch, hoy, asunto)
            except Exception as e:
                print(f"    [WARN] Error actualizando Sheet: {e}")
            enviados += 1

            delay = MIN_DELAY_SECONDS + (MAX_DELAY_SECONDS - MIN_DELAY_SECONDS) * (hash(emp.nombre) % 4) / 4.0
            print(f"    Esperando {delay:.1f}s...")
            time.sleep(delay)
        else:
            print(f"    [ERROR] {msg}")

    print(f"\n  [OK] {enviados} emails procesados")


def mostrar_resumen(sheets_svc):
    """Muestra resumen leyendo directamente del Sheet."""
    empresas = leer_empresas(sheets_svc)
    total = len(empresas)
    con_email = sum(1 for e in empresas if e.tiene_email_valido())
    por_estado = {}
    por_touch = {}
    for e in empresas:
        estado = e.estado or "pendiente"
        por_estado[estado] = por_estado.get(estado, 0) + 1
        if e.num_contactos > 0:
            por_touch[e.num_contactos] = por_touch.get(e.num_contactos, 0) + 1

    print(f"\n{'='*60}")
    print(f"  RESUMEN DE CAMPANA (desde Sheet)")
    print(f"{'='*60}")
    print(f"  Total empresas: {total}")
    print(f"  Con email valido: {con_email}")
    if por_estado:
        print(f"  Por estado:")
        for estado, cnt in sorted(por_estado.items()):
            print(f"    {estado}: {cnt}")
    if por_touch:
        print(f"  Por touch:")
        for touch, cnt in sorted(por_touch.items()):
            print(f"    Touch {touch}: {cnt}")


def main():
    dry_run = "--dry-run" in sys.argv
    test_mode = "--test" in sys.argv
    draft_mode = "--draft" in sys.argv

    if "--auth" in sys.argv:
        auth_flow()
        return

    print("=" * 60)
    print(f"  SILVIGON - Campana de Emails B2B")
    print(f"  Fecha: {datetime.now(ZoneInfo(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  From: {FROM_EMAIL}")
    print(f"  Limite diario: {DAILY_LIMIT}")
    print(f"  Modo: {'DRY RUN' if dry_run else 'DRAFT' if draft_mode else 'TEST' if test_mode else 'PRODUCCION'}")
    print(f"{'='*60}")

    gmail_svc = gmail_service()
    sheets_svc = sheets_service()
    print("[OK] Servicios de Google inicializados")

    paso_detectar_respuestas(gmail_svc, sheets_svc)

    hoy = local_hoy()
    if not test_mode and not draft_mode and hoy.weekday() >= 5:
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        print(f"\n[INFO] Hoy es {dias[hoy.weekday()]}. No se envian emails en fin de semana.")
        mostrar_resumen(sheets_svc)
        return

    paso_enviar_emails(gmail_svc, sheets_svc, dry_run, test_mode, draft_mode)

    if not test_mode:
        mostrar_resumen(sheets_svc)

    print(f"\n{'='*60}")
    print(f"  [OK] Campana completada")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
