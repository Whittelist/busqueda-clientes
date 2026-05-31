# Busqueda Google Maps - Módulo 1

Busca empresas en Google Maps por categoría y ubicación. Extrae datos estructurados y los guarda en SQLite + CSV.

## Cómo usar

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con GOOGLE_PLACES_API_KEY
python main.py
```

## Salida

- SQLite: `data/clientes.db`
- CSV: `data/resultados.csv`
- Google Sheets: Sheet4 del spreadsheet de SilviGon (con setup_sheet4.py)

## Estructura interna

```
busqueda-google-maps/
├── main.py              ← Orquestador
├── maps_scraper.py      ← Google Places API
├── database.py          ← SQLite + CSV
├── config.py            ← Config (provincias, categorías, APIs)
├── setup_sheet4.py      ← Crea/limpia Sheet4 en Drive
├── test_db.py           ← Test offline (datos simulados)
├── .env.example
├── requirements.txt
└── PROJECT.md
```
