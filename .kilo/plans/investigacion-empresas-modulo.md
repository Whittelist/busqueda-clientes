# Plan: Módulo de Investigación y Enriquecimiento de Empresas

## Objetivo

Crear un módulo `investigacion-empresas/` que automatice el enriquecimiento de empresas constructoras en el Google Sheet "TEST EMPRESAS BOT 2". Para cada empresa sin datos en Q (problema), R (idea_mejora) o U (tamano), el módulo:

1. Scrapea el contenido de su página web
2. Lo envía a DeepSeek para analizar y extraer: problema detectado, idea de mejora, y tamaño estimado
3. Escribe los resultados de vuelta al Sheet

Esto alimenta al módulo `busqueda-emails` con información de calidad para redactar emails personalizados.

---

## Arquitectura

```
investigacion-empresas/
├── config.py          # DeepSeek API, Google Sheets ID, columnas, límites
├── main.py            # Orquestador principal (CLI)
├── sheets_client.py   # Lectura/escritura del Google Sheet
├── investigador.py    # Lógica: fetch web + llamada DeepSeek + parseo
├── web_fetcher.py     # Copia adaptada de busqueda-navegador/web_fetcher.py
├── requirements.txt
└── .env.example
```

---

## Flujo de Ejecución

```
main.py
  │
  ├─ 1. sheets_client.leer_empresas_pendientes()
  │     Lee TEST EMPRESAS BOT 2, filtra filas con Q/R/U vacías
  │     Devuelve lista de Empresa (nombre, provincia, categoria, web, row_number)
  │
  ├─ 2. Para cada empresa (con rate limiting):
  │     ├─ web_fetcher.fetch_sitio_completo(web)
  │     │     BFS crawl: descubre TODAS las rutas internas
  │     │     Visita hasta 15 páginas del sitio
  │     │     Extrae solo texto visible (Ctrl+A) de cada una
  │     │     Combina todo con tope ~30k chars
  │     │     Si falla → texto = "" (no bloquea el flujo)
  │     │
  │     ├─ investigador.investigar_empresa(nombre, provincia, categoria, web, contenido_web)
  │     │     Construye prompt con toda la info
  │     │     Llama a DeepSeek (OpenAI client)
  │     │     Parsea respuesta → {problema, mejora, tamano}
  │     │
  │     └─ sheets_client.escribir_resultados(row_number, problema, mejora, tamano)
  │           Escribe en columnas Q, R, U del Sheet
  │
  └─ 3. Reporte final: X empresas procesadas, Y errores
```

---

## Decisiones Técnicas

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| **Método investigación** | Web fetcher local + DeepSeek API | Sin coste extra de APIs de búsqueda. Reutiliza web_fetcher.py existente. DeepSeek ya se paga en busqueda-emails. |
| **Procesamiento** | Solo filas con Q/R/U vacías | Idempotente, re-ejecutable, no sobrescribe datos ya válidos. |
| **Alcance scrapeo** | BFS crawl completo del sitio (hasta 15 páginas) | Necesitamos TODO el contenido para analizar problemas, tamaño, productos. No solo contacto. |
| **DeepSeek modelo** | `deepseek-v4-flash` (mismo que busqueda-emails) | Consistencia con el resto del proyecto. Barato y rápido. |
| **Google Sheets** | Mismo SPREADSHEET_ID y token que busqueda-emails | Un solo sheet, una sola fuente de verdad. |
| **Rate limiting** | 1-3s delay entre llamadas DeepSeek | Evita rate limits. 25 empresas ≈ 2-3 minutos. |
| **Ejecución** | `python main.py` desde CLI | Simple, portable, mismo patrón que busqueda-google-maps/main.py |

---

## Prompt de DeepSeek

Se usará el contenido de `prompt_enriquecimiento.md` como base, adaptado para ser un system prompt + user prompt con los datos de cada empresa.

Ejemplo de system prompt:
```
Eres un analista experto en digitalización del sector construcción español.
Tu tarea es analizar empresas constructoras y detectar:
1. PROBLEMA: qué problema de digitalización parece tener según su web
2. MEJORA: una mejora concreta de automatización/software que podrían implementar
3. TAMAÑO: estimación basada en empleados, ámbito, facturación, años de actividad

REGLAS:
- Basado en EVIDENCIAS de su web, no inventes
- Sin web = digitalización nula, mencionarlo
- Web con e-commerce = más avanzados, centrarse en otro problema
- Web estática básica = atraso digital
- Cada campo máx 150 caracteres
- NO uses palabras como "digitalización", "transformación digital", "sinergias", "soluciones integrales"
```

User prompt:
```
Analiza esta empresa del sector construcción:

EMPRESA: {nombre}
PROVINCIA: {provincia}
CATEGORÍA: {categoria}
WEB: {web}

CONTENIDO DE SU WEB:
{contenido_web}

Devuelve EXACTAMENTE en este formato:
Problema: [máx 150 chars]
Mejora: [máx 150 chars]
Tamaño: [máx 100 chars]
```

---

## Integración con el Ecosistema

```
busqueda-google-maps/   → Llena columnas A-L (nombre, web, teléfono, etc.)
busqueda-navegador/     → Enriquece columnas D, E, F (web alternativa, email, teléfono extra)
investigacion-empresas/ → Llena columnas Q, R, U (problema, mejora, tamaño)  ← NUEVO
busqueda-emails/        → Lee TODO lo anterior y genera emails personalizados
```

---

## Archivos a Crear/Modificar

### Nuevos

1. **investigacion-empresas/config.py** — Configuración centralizada
2. **investigacion-empresas/sheets_client.py** — Lectura/escritura de Google Sheets
3. **investigacion-empresas/investigador.py** — Lógica core (DeepSeek prompt + parseo)
4. **investigacion-empresas/main.py** — Orquestador CLI
5. **investigacion-empresas/requirements.txt** — Dependencias
6. **investigacion-empresas/.env.example** — Variables de entorno necesarias

### Existentes (no modificar)

- `busqueda-navegador/web_fetcher.py` — Se referencia, pero mejor copiar/adaptar para no acoplarse

---

## Plan de Implementación

### Fase 1: Estructura base
- Crear `config.py` con todas las constantes (SPREADSHEET_ID, SHEET_NAME, columnas Q/R/U, DeepSeek config, rate limits)
- Crear `requirements.txt`

### Fase 2: Cliente de Google Sheets
- Implementar `sheets_client.py`:
  - `leer_empresas_pendientes()` → filtra filas con Q/R/U vacías
  - `escribir_resultados(row, problema, mejora, tamano)` → escribe en Q, R, U

### Fase 3: Investigador (DeepSeek)
- Implementar `investigador.py`:
  - `investigar_empresa(nombre, provincia, categoria, web, contenido_web)` → dict
  - Construir prompts basados en `prompt_enriquecimiento.md`
  - Llamar DeepSeek vía OpenAI client
  - Parsear respuesta con regex (robusto a pequeñas variaciones)
  - Fallback: si no hay contenido web, inferir desde sector/experiencia

### Fase 4: Web fetcher (adaptado para investigación completa)
- Copiar `web_fetcher.py` de `busqueda-navegador/` como base
- Añadir nueva función `fetch_sitio_completo(url, max_paginas=15)`:
  - **BFS crawl** desde la main page: extrae TODOS los enlaces internos (no solo contacto)
  - Filtra solo: enlaces del mismo dominio, excluye `#`, `javascript:`, `mailto:`, rutas obvias no-contenido (`/login`, `/cart`, `/cdn-cgi`, etc.)
  - Visita hasta `max_paginas=15` páginas (frente a las 4 actuales)
  - Cada página: extrae solo texto visible (`_html_a_texto()`)
  - Combina todo con tope de ~30k caracteres (suficiente para DeepSeek)
- Mantener `fetch_con_profundidad()` original para compatibilidad

### Fase 5: Orquestador (main.py)
- Implementar `main.py`:
  - Leer empresas pendientes
  - Loop con rate limiting (time.sleep entre iteraciones)
  - Para cada empresa: fetch web → investigar → escribir sheet
  - Reporte final con stats
  - Manejo de errores (si falla una, continuar con la siguiente)

### Fase 6: Testing
- Ejecutar en DRY_RUN primero (solo log, no escribir sheet)
- Ejecutar con 5 empresas de prueba
- Verificar resultados en Sheet
- Ajustar prompts si es necesario

---

## Notas y Consideraciones

- **Columna T (notas)**: El prompt menciona registrar fuentes y evidencias. Podemos guardarlas en la columna T para trazabilidad.
- **Re-ejecución segura**: Solo procesa filas con Q/R/U vacías. Si quieres regenerar, borras esas columnas en el Sheet y re-ejecutas.
- **Coste DeepSeek**: ~0.14€ por cada 1M tokens input. Con 25 empresas y ~5000 chars de contenido web cada una, estimado <0.01€ por ejecución completa.
- **Sin dependencia de Firecrawl ni Hermes**: La investigación se basa en scrapeo directo de la web de la empresa + conocimiento del sector de DeepSeek. Esto mantiene el módulo portable y sin dependencias externas adicionales.
