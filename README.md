# Busqueda de Clientes - Automatización

Proyecto modular de automatización de prospección comercial.

## Estructura

```
busqueda-clientes/
├── busqueda-google-maps/    ← Google Places API → SQLite + CSV + Sheets
├── busqueda-navegador/      ← Firecrawl + DeepSeek IA → enrichment (pendiente)
└── union/                   ← Fusión de ambos módulos (futuro)
```

## Flujo de trabajo

1. Cada módulo se desarrolla y testea de forma **independiente**
2. Cuando ambos funcionan por separado → backup → se unifican en `union/`
3. El resultado final será un pipeline completo: Maps → Web → IA → Sheets

## Módulos

### busqueda-google-maps ✅ (en desarrollo)
Busca empresas en Google Maps por categoría + ubicación.
Extrae: nombre, dirección, teléfono, web, rating, reviews.
Guarda en SQLite + exporta CSV.
Preparado para volcar a Google Sheets (Sheet4).

### busqueda-navegador ⏳ (pendiente)
Para empresas sin web o sin datos suficientes.
Firecrawl extrae contenido → DeepSeek analiza → extrae emails/teléfonos/contacto.

### union ⏳ (pendiente)
Pipeline completo: Maps → Navegador → Sheets.

## Repositorio

GitHub: https://github.com/Whittelist/busqueda-clientes
