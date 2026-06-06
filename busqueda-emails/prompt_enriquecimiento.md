# PROMPT PARA ENRIQUECER EMPRESAS CONSTRUCTORAS
## Silvigon — Automatización e IA para el sector construcción

---

## 1. QUIÉNES SOMOS

**Silvigon** es una consultora española que ayuda a empresas del sector construcción (áridos, prefabricados de hormigón, mezclas bituminosas, excavaciones, obra civil) a digitalizar sus procesos mediante automatización (RPA) e inteligencia artificial.

**Las fundadoras:**
- **Silvia Perea** — Co-fundadora. Experiencia en desarrollo de ERPs internos (ej: ERP para Valencia Basket con gestión de jugadores, nutrición, entrenamiento y cantera).
- **Brayan Zúñiga** — Co-fundador. Experiencia técnica en automatización e IA.

**Nuestra propuesta de valor:**
- Consultoría GRATUITA de 15 minutos sin compromiso
- No vendemos nada en el primer contacto
- Queremos entender sus problemas reales y mostrarles lo que la tecnología puede hacer por ellos

---

## 2. SECTORES OBJETIVO

Empresas españolas de:
- Áridos (canteras, graveras)
- Prefabricados de hormigón (bloques, vigas, bovedillas, adoquines, bordillos)
- Mezclas bituminosas (asfaltos, aglomerados)
- Excavaciones y movimientos de tierras
- Construcción en general (obra civil, edificación)
- Hormigón (plantas de hormigón, bombas)

---

## 3. PROBLEMAS REALES QUE SUELEN TENER

Basado en conocimiento del sector (auditoría en construcción). Estos son los problemas REALES, no supuestos técnicos:

1. **Todo en papel** — Partes de trabajo, albaranes, ensayos, registros de producción, documentación de calidad. Siguen imprimiendo, archivando en carpetas, perdiendo documentos.
2. **Gente haciendo tareas manuales absurdas** — Personas pasando datos de papeles a Excel, reescribiendo la misma información en varios sitios, haciendo cálculos a mano.
3. **Documentación desorganizada** — No encuentran un certificado de ensayo de hace 3 meses, no saben dónde está el albarán de tal pedido, pierden tiempo buscando.
4. **Sin ERP ni visión centralizada** — No tienen un solo sitio donde ver el estado de la empresa: pedidos pendientes, producción del día, stock real, facturación.
5. **No saben por dónde empezar a digitalizarse** — Creen que es caro, que es solo para grandes empresas, no saben lo que existe ni lo que cuesta.
6. **Desconocimiento de IA** — No saben que la IA puede ayudarles a organizar documentos, predecir roturas de stock, automatizar respuestas a clientes, etc.

---

## 4. CAMPOS A RELLENAR PARA CADA EMPRESA

Para cada empresa, necesitamos 3 campos:

### 4.1. `problema_detectado` (máx 150 caracteres)
Descripción breve del problema principal que parece tener la empresa según su web, tamaño y sector.
- Basado en EVIDENCIAS de su web, no invents.
- Si la web tiene e-commerce, mencionarlo.
- Si la web es muy básica (una página estática), probablemente están muy atrasados digitalmente.
- Si la web tiene catálogo de productos pero no se puede comprar online, probablemente gestionan pedidos por teléfono/email.
- Ejemplo: "Empresa familiar con varias líneas de producto pero sin tienda online. La web es estática. Probablemente gestionan todo por teléfono y papel."

### 4.2. `idea_mejora` (máx 150 caracteres)
Una posible mejora concreta que podrían implementar.
- Debe estar relacionada con el problema detectado.
- Enfocada en automatización, organización de documentos, ERP, visión centralizada.
- Ejemplo: "Podrían centralizar los pedidos y la documentación técnica en un sistema sencillo sin necesidad de ERP complejo."

### 4.3. `tamano` (máx 100 caracteres)
Tamaño estimado de la empresa.
- Indicadores: número de empleados (si se encuentra), facturación estimada, si es empresa familiar, años de antigüedad, ámbito local/nacional.
- Ejemplo: "Pequeña empresa familiar, < 15 empleados, ámbito provincial."
- Ejemplo: "Mediana empresa, 50+ empleados, varias delegaciones."

---

## 5. DÓNDE INVESTIGAR

Para cada empresa, revisa en este orden:

1. **Su web** (campo proporcionado)
   - ¿Tiene tienda online? ¿Catálogo? ¿Blog?
   - ¿La web es moderna o antigua? (indica nivel de digitalización)
   - ¿Qué productos/servicios ofrecen exactamente?
   - ¿Tienen sección de "trabaja con nosotros" o "proyectos"?

2. **Registros públicos** si la web no da suficiente información:
   - Google Maps (reviews, fotos, horarios)
   - LinkedIn (empleados, tamaño)
   - eInforma / Datacom (datos mercantiles si están disponibles)

3. **Sentido común del sector** (experiencia en construcción):
   - Empresa pequeña + web antigua = probablemente todo en papel
   - Empresa con varias líneas de producto = desorganización documental
   - Empresa con 30+ años = procesos heredados, resistentes al cambio

---

## 6. FORMATO DE SALIDA

Devuelve los datos en este formato EXACTO. SEPÁRAME CADA EMPRESA CON UNA LÍNEA DE "---":

```
Empresa: [Nombre exacto]
Problema: [problema_detectado - máx 150 chars]
Mejora: [idea_mejora - máx 150 chars]
Tamaño: [tamano - máx 100 chars]
---
Empresa: [Nombre exacto]
Problema: ...
Mejora: ...
Tamaño: ...
```

NO añadas explicaciones, ni introducciones, ni resúmenes. Solo los datos.

---

## 7. LISTA DE EMPRESAS PARA ENRIQUECER

(Inserta aquí las empresas del Sheet que necesitas investigar)
