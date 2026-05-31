# Cliente Finder - Project Spec (SDD)

## Objetivo de negocio
Automatizar la prospeccion comercial en el sector construccion: buscar empresas de prefabricados de hormigon por comunidad autonoma, extraer datos de contacto, enriquecer con IA y gestionar el seguimiento.

## Arquitectura (por modulos)

```
Modulo 1: maps_scraper.py    [LISTO para test]
  Google Places API > SQLite + CSV
  - Busca por categoria + provincia
  - Extrae: nombre, direccion, telefono, web, rating, reviews
  - Exporta CSV para Drive

Modulo 2: web_scraper.py     [PENDIENTE]
  DeepSeek V4 Flash > enrichment
  - Para empresas sin telefono/email
  - Fetch web + IA extrae datos
  - Actualiza BD

Modulo 3: sheets_push.py     [PENDIENTE]
  SQLite > Google Sheets
  - Sincroniza BD con Spreadsheet en Drive
  - Usa token Gmail existente

Modulo 4: seguimiento.py     [PENDIENTE]
  Estados de contacto + respuestas
  - Follow-up automatico
  - Email sender con plantillas
```

## MVP (Modulo 1 solo)

**Input:** Categoria + Provincia (desde config.py)
**Proceso:**
1. Google Places Text Search -> lista de places
2. Por cada place -> Place Details (telefono, web, reviews)
3. Guardar en SQLite
4. Exportar CSV

**Output:** CSV con:
- Nombre, Direccion, Telefono, Web, Categoria
- Rating, Total Reviews, Reviews (JSON)
- Provincia, Coordenadas, URL Google Maps

## Proximo paso (cuando funcione M1)
- Modulo 2: web_scraper con DeepSeek
- Buscar emails en webs de empresas
- Enriquecer datos faltantes
