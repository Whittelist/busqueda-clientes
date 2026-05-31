"""
Gestor de base de datos SQLite.
Guarda empresas y contactos de forma estructurada.
"""
import sqlite3
from datetime import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT UNIQUE,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            website TEXT,
            categoria TEXT,
            rating REAL,
            total_reviews INTEGER,
            reviews_json TEXT,
            provincia TEXT,
            latitud REAL,
            longitud REAL,
            google_maps_url TEXT,
            business_status TEXT,
            fecha_creacion TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS busquedas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            provincia TEXT NOT NULL,
            total_resultados INTEGER,
            fecha TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)

    conn.commit()
    conn.close()
    print("[DB] Base de datos inicializada correctamente.")


def insertar_empresa(empresa: dict) -> bool:
    """
    Inserta una empresa en la BD.
    Returns True si es nueva, False si ya existía (duplicado).
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO empresas
            (place_id, nombre, direccion, telefono, website, categoria,
             rating, total_reviews, reviews_json, provincia,
             latitud, longitud, google_maps_url, business_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            empresa.get("place_id"),
            empresa.get("nombre"),
            empresa.get("direccion"),
            empresa.get("telefono"),
            empresa.get("website"),
            empresa.get("categoria"),
            empresa.get("rating"),
            empresa.get("total_reviews"),
            empresa.get("reviews_json"),
            empresa.get("provincia"),
            empresa.get("latitud"),
            empresa.get("longitud"),
            empresa.get("google_maps_url"),
            empresa.get("business_status"),
        ))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"[DB] Error insertando {empresa.get('nombre')}: {e}")
        return False
    finally:
        conn.close()


def registrar_busqueda(query: str, provincia: str, total: int):
    """Registra una búsqueda realizada."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO busquedas (query, provincia, total_resultados) VALUES (?, ?, ?)",
            (query, provincia, total)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB] Error registrando búsqueda: {e}")
    finally:
        conn.close()


def exportar_csv(ruta: str):
    """Exporta todas las empresas a CSV."""
    import csv
    conn = get_connection()
    rows = conn.execute("""
        SELECT nombre, direccion, telefono, website, categoria,
               rating, total_reviews, provincia, google_maps_url
        FROM empresas
        ORDER BY provincia, nombre
    """).fetchall()
    conn.close()

    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Nombre", "Dirección", "Teléfono", "Web", "Categoría",
            "Rating", "Total Reviews", "Provincia", "Google Maps URL"
        ])
        for row in rows:
            writer.writerow([row[c] for c in range(len(row))])

    print(f"[CSV] Exportadas {len(rows)} empresas a {ruta}")
    return len(rows)


def resumen():
    """Devuelve estadísticas de la BD."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
    por_provincia = conn.execute(
        "SELECT provincia, COUNT(*) as cnt FROM empresas GROUP BY provincia ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {"total": total, "por_provincia": dict(por_provincia)}
