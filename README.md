# Cliente Finder — Automatización de prospección comercial

Busca empresas en Google Maps por categoría y ubicación, extrae datos, los enriquece y los guarda para gestión de contactos.

## Arquitectura (por módulos)

```
Módulo 1: maps_scraper.py    ← Google Places API → SQLite + CSV
Módulo 2: web_scraper.py      ← Fetch web + DeepSeek → enriquecimiento
Módulo 3: sheets_push.py      ← SQLite → Google Sheets
Módulo 4: seguimiento.py      ← Estados, contactos, respuestas
```

## Cómo usar (Módulo 1)

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tu API key de Google Places
python main.py
```

## Estado actual

- [x] Módulo 1: Google Maps scraper funcional
- [ ] Módulo 2: Web scraper + IA
- [ ] Módulo 3: Google Sheets push
- [ ] Módulo 4: Seguimiento
