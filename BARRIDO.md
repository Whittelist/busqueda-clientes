# Mapa de Barrido por Comunidades Autonomas

Cada comunidad se procesa cambiando `COMUNIDAD_ACTIVA` en `busqueda-google-maps/config.py`
y ejecutando `main.py`. Luego hacer `push_to_sheets.py` para subir al Sheet.

---

## Modulos del Pipeline

| Modulo | Estado | Descripcion |
|--------|--------|-------------|
| `busqueda-google-maps/` | ✅ | Scrapea Google Places API → SQLite → Sheet |
| `busqueda-navegador/` | ⏳ | Fetch web + extrae emails/tlf |
| `investigacion-empresas/` | ✅ | DeepSeek analiza web → problema/mejora/tamano en Q,R,U |
| `dedup.py` | ✅ | Detecta duplicados por email en el Sheet y los fusiona |
| `busqueda-emails/` | ⏳ | Campana de emails (se alimenta del Sheet) |

## Notas

- **Dedup**: `push_to_sheets.py` ya detecta duplicados por email al insertar. Ademas, `dedup.py --apply` escanea y fusiona filas con emails compartidos.
- **API Key Google Places**: `AIzaSyDEVokq9VndWe6uW2J9HoRc6cVhk2EQIsY` (cuenta Silvigon)
- **Sheet**: `TEST EMPRESAS BOT 2` en el spreadsheet de busqueda-clientes

---

## Barrido por Comunidades

## [ ] Andalucia
- [ ] Almeria
- [ ] Cadiz
- [ ] Cordoba
- [ ] Granada
- [ ] Huelva
- [ ] Jaen
- [ ] Malaga
- [x] Sevilla

## [ ] Aragon
- [ ] Huesca
- [ ] Teruel
- [ ] Zaragoza

## [ ] Asturias
- [ ] Asturias

## [ ] Baleares
- [ ] Islas Baleares

## [ ] Canarias
- [ ] Las Palmas
- [ ] Santa Cruz de Tenerife

## [ ] Cantabria
- [ ] Cantabria

## [x] Castilla-La Mancha (Ciudad Real)
- [ ] Albacete
- [x] Ciudad Real
- [ ] Cuenca
- [ ] Guadalajara
- [ ] Toledo

## [ ] Castilla y Leon
- [ ] Avila
- [ ] Burgos
- [ ] Leon
- [ ] Palencia
- [ ] Salamanca
- [ ] Segovia
- [ ] Soria
- [ ] Valladolid
- [ ] Zamora

## [ ] Catalunya
- [ ] Barcelona
- [ ] Girona
- [ ] Lleida
- [ ] Tarragona

## [ ] Comunidad Valenciana
- [x] Alicante
- [ ] Castellon
- [ ] Valencia

## [ ] Extremadura
- [ ] Badajoz
- [ ] Caceres

## [ ] Galicia
- [ ] A Coruna
- [ ] Lugo
- [ ] Ourense
- [ ] Pontevedra

## [ ] La Rioja
- [ ] La Rioja

## [ ] Madrid
- [ ] Madrid

## [ ] Murcia
- [ ] Murcia

## [ ] Navarra
- [ ] Navarra

## [ ] Pais Vasco
- [ ] Alava
- [ ] Bizkaia
- [ ] Gipuzkoa

---

**Total: 17 comunidades autonomas + 50 provincias**
