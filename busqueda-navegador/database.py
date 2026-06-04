"""
Base de datos del modulo busqueda-navegador.
Guarda los datos enriquecidos de cada empresa.
"""
import sqlite3, json, os, csv
from config import ENRICHED_DB


def get_connection():
    conn = sqlite3.connect(ENRICHED_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS enrichment (
            empresa_id INTEGER PRIMARY KEY,
            nombre TEXT,
            provincia TEXT,
            website TEXT,
            email_extraidos TEXT,
            telefono_contacto TEXT,
            persona_contacto TEXT,
            problema_detectado TEXT,
            idea_mejora TEXT,
            tamano_empresa TEXT,
            fecha_analisis TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()


def guardar_enrichment(empresa_id: int, datos: dict):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO enrichment
            (empresa_id, nombre, provincia, website, email_extraidos,
             telefono_contacto, persona_contacto, problema_detectado,
             idea_mejora, tamano_empresa, fecha_analisis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    datetime('now', 'localtime'))
        """, (
            empresa_id,
            datos.get("nombre", ""),
            datos.get("provincia", ""),
            datos.get("website", ""),
            json.dumps(datos.get("email_encontrados", []), ensure_ascii=False),
            datos.get("telefono_contacto", ""),
            datos.get("persona_contacto", ""),
            datos.get("problema_detectado", ""),
            datos.get("idea_mejora", ""),
            datos.get("tamano_empresa", ""),
        ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"  [DB ERROR] {e}")
    finally:
        conn.close()


def ya_procesada(empresa_id: int) -> bool:
    """Comprueba si una empresa ya fue procesada por este modulo."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM enrichment WHERE empresa_id = ?",
        (empresa_id,)
    ).fetchone()
    conn.close()
    return row is not None


def get_empresas_pendientes():
    """
    Lee las empresas del Modulo 1 que aun no han sido procesadas.
    """
    from config import MOD1_DB

    if not os.path.exists(MOD1_DB):
        print(f"[ERROR] No se encuentra la BD del Modulo 1: {MOD1_DB}")
        print("  Ejecuta primero busqueda-google-maps/main.py")
        return []

    conn_mod1 = sqlite3.connect(MOD1_DB)
    conn_mod1.row_factory = sqlite3.Row
    rows = conn_mod1.execute("""
        SELECT id, nombre, provincia, website
        FROM empresas
        ORDER BY provincia, nombre
    """).fetchall()
    conn_mod1.close()

    pendientes = []
    for row in rows:
        if not ya_procesada(row["id"]):
            pendientes.append(dict(row))
        else:
            print(f"  [SKIP] {row['nombre']} ya procesada")

    return pendientes


def exportar_csv(ruta: str):
    """Exporta datos combinados (Mod1 + enrichment) a CSV."""
    import csv
    conn = get_connection()

    rows = conn.execute("""
        SELECT nombre, provincia, website,
               email_extraidos, telefono_contacto,
               persona_contacto, problema_detectado,
               idea_mejora, tamano_empresa
        FROM enrichment
        ORDER BY provincia, nombre
    """).fetchall()
    conn.close()

    if not rows:
        print("  [CSV] No hay datos enriquecidos para exportar")
        return 0

    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Nombre", "Provincia", "Web", "Emails", "Telefono Contacto",
            "Persona Contacto", "Problema Detectado", "Idea de Mejora", "Tamano Empresa"
        ])
        for r in rows:
            writer.writerow([r[c] for c in range(len(r))])

    print(f"  [CSV] Exportadas {len(rows)} empresas enriquecidas a {ruta}")
    return len(rows)
