"""
Test rapido del modulo de base de datos y exportacion.
No necesita API key - usa datos simulados.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, insertar_empresa, exportar_csv, resumen
from config import CSV_OUTPUT


def test_db():
    print("=" * 50)
    print("TEST: Base de datos SQLite")
    print("=" * 50)

    init_db()

    empresas_test = [
        {
            "place_id": "test_001",
            "nombre": "Hormigones Test SL",
            "direccion": "Calle Mayor 10, Sevilla",
            "telefono": "+34 954 123 456",
            "website": "https://hormigonestest.com",
            "categoria": "prefabricados de hormigon",
            "rating": 4.2,
            "total_reviews": 15,
            "reviews_json": json.dumps([
                {"author": "Juan", "rating": 5, "text": "Muy buen servicio", "time": "2 meses atras"}
            ], ensure_ascii=False),
            "provincia": "Sevilla",
            "latitud": 37.3891,
            "longitud": -5.9845,
            "google_maps_url": "https://maps.google.com/?cid=test001",
            "business_status": "OPERATIONAL",
        },
        {
            "place_id": "test_002",
            "nombre": "Prefabricados Andaluces SA",
            "direccion": "Av. de la Industria 45, Malaga",
            "telefono": "+34 952 789 012",
            "website": "",
            "categoria": "prefabricados de hormigon",
            "rating": 3.8,
            "total_reviews": 8,
            "reviews_json": "[]",
            "provincia": "Malaga",
            "latitud": 36.7213,
            "longitud": -4.4214,
            "google_maps_url": "https://maps.google.com/?cid=test002",
            "business_status": "OPERATIONAL",
        },
        {
            "place_id": "test_003",
            "nombre": "Bloques Hormigon Granada",
            "direccion": "Poligono Industrial, Granada",
            "telefono": "",
            "website": "https://bloquesgranada.com",
            "categoria": "prefabricados de hormigon",
            "rating": 4.5,
            "total_reviews": 42,
            "reviews_json": "[]",
            "provincia": "Granada",
            "latitud": 37.1760,
            "longitud": -3.5980,
            "google_maps_url": "https://maps.google.com/?cid=test003",
            "business_status": "OPERATIONAL",
        },
    ]

    for emp in empresas_test:
        if insertar_empresa(emp):
            print(f"  [OK] Insertada: {emp['nombre']}")
        else:
            print(f"  [~] Duplicado: {emp['nombre']}")

    total = exportar_csv(CSV_OUTPUT)
    stats = resumen()

    print(f"\nResumen:")
    print(f"  Total empresas: {stats['total']}")
    for prov, cnt in stats["por_provincia"].items():
        print(f"    - {prov}: {cnt}")
    print(f"  CSV: {CSV_OUTPUT} ({total} empresas)")

    print(f"\n[OK] TEST COMPLETADO")
    return True


if __name__ == "__main__":
    test_db()
