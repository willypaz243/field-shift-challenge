# Comparativa de retos GAMC — dificultad ordenada (fácil → difícil)

> Evaluación del 14/11/2026. Criterios: (1) dificultad técnica del núcleo del reto,
> (2) soporte de datos del GAMC, (3) viabilidad en 24 h, (4) preparación que ya tenemos.

| # | Reto (oficial) | Proyecto GAMC | Dificultad oficial | Dificultad para nosotros | Datos GAMC |
|---|---|---|---|---|---|
| 1 | **Be An Earth System Trend Detective!** | 01 (Microclimas Urbanos con IA) **y** 05 (Visualizador Gestión Distrital) | Advanced | 🟢 **Media-baja** | **La mejor dotada**: 12 capas urbanas + **Red MÓNICA (Excel, 2 estaciones continuas)** + GeoJSON transporte |
| 2 | **Field Shift: Adapting Farms with NASA Data** | 04 (Agrotecnología y Gestión del Agua) | Advanced/Intermediate | 🟡 **Media** (pero ya explorada a fondo) | 3 capas (periurbanos, drenaje, distritos) |
| 3 | **Harmonization of MODIS and VIIRS Hot Spots** | 03 (Armonización Satelital p/ Incendios) | Advanced/Intermediate | 🟠 **Media-alta** | 3 capas (periurbanos, cota 2750, distritos) — poco soporte |
| 4 | **Dancing with the SARs** | 02 (Alerta Temprana de Riesgos en Cuencas) | Advanced | 🔴 **Alta** | 7 capas (cuencas UH 7/8, cota 2750, emergencias…) — solo contexto |

## 1. Be An Earth System Trend Detective! — 🟢 la más abordable

**Qué pide:** herramienta que selecciona variables de misiones NASA/modelos (MODIS, OMI, AIRS,
GPM, MERRA-2, GLDAS), genera y visualiza **series temporales** por región, y determina qué,
dónde, cuánto cambia y si es **estadísticamente significativo** (t-test, Mann-Kendall,
intervalos de confianza). Tendencias **lineales bastan** (lo dice el enunciado).

**Por qué es la más fácil para nosotros:**
- El núcleo es *plot + estadística de libro*: regresión lineal, Mann-Kendall, significancia.
  Nada de ML, ni procesamiento de imágenes.
- Datos fáciles: **NASA POWER** (API sin auth), **Giovanni** (API scriptable de series
  mensuales MERRA-2/GLDAS), FIRMS. Datos diarios/mensuales, "los más fáciles de procesar"
  según el propio enunciado.
- **Soporte GAMC único:** doble proyecto (01 + 05) = 12 capas urbanas + los **únicos datos
  descargables reales** de todo el portal: **Red MÓNICA** (registros continuos de 2 estaciones
  terrestres en Cochabamba) y GeoJSON de transporte. Ventaja narrativa: contrastar
  tendencia satelital vs. medición terrestre local.
- Público definido (estudiantes + público con bagaje) → la exigencia de UX es menor.

**Riesgo:** es un reto *Advanced* popular; la diferenciación será el análisis local de
Cochabamba (microclimas urbanos con Red MÓNICA + capas GAMC).

## 2. Field Shift: Adapting Farms with NASA Data — 🟡 media (con ventaja de preparación)

**Qué pide:** herramienta de decisión que combine NASA + suelo local + prioridades del
agricultor para comparar **≥3 rotaciones de cultivos** con evidencia, brechas y riesgos.

**Por qué es media:** no pide estadística sofisticada, pero sí un producto multidimensional
(mapa + tabla de cultivos + lógica de scoring + explicaciones honestas). Nuestro plan de
"Turnos del Valle" ya está perfilado: NASA POWER + capas GAMC + tabla de cultivos del valle
+ port de lógica de rotación. La exploración del contexto local (SITAP, clima, expansión
urbana) ya está hecha y commiteada.

**Riesgo:** ~1.660 equipos ya inscritos en este reto → competencia alta; el alcance es más
amplio que el de Trend Detective.

## 3. Harmonization of MODIS and VIIRS Hot Spots — 🟠 media-alta

**Qué pide:** app web con **calendario de actividad de fuego** armonizando los hotspots
MODIS (2000–hoy) y VIIRS (más detalle, distinta resolución/sensibilidad), con comparación
contra medianas históricas y descarga CSV.

**Por qué es media-alta:**
- Bajar hotspots es fácil (**FIRMS API con MAP_KEY gratuito**, CSV directo).
- El núcleo difícil es la **armonización metodológica**: distinta resolución espacial
  (375 m vs 1 km), distinta sensibilidad y calendario de observación. Un ajuste
  estadístico bien hecho es nivel paper; una versión simplificada (remuestreo a malla
  común + ponderación por confianza + heatmap calendario) es viable pero hay que
  defenderla bien ante los jueces.
- GAMC aporta poco (3 capas de contexto); el enfoque local (chaqueos/incendios en los
  valles y el oriente boliviano) lo pone el equipo.

**Riesgo:** la parte de "harmonización honesta" puede comerse horas críticas del hackathon.

## 4. Dancing with the SARs — 🔴 la más difícil

**Qué pide:** aplicación interactiva con datos **SAR de la misión NISAR** (NASA-ISRO) para
rastrear cambios de superficie (humedales, glaciares, deforestación, subsistencia,
terremotos…), con polarizaciones, series temporales de imágenes radar y storytelling.

**Por qué es la más difícil:**
- Procesamiento SAR real: descarga de escenas enormes (ASF Vertex), corrección de speckle,
  polarizaciones, geocorrección, detección de cambio — sin experiencia previa, la curva de
  aprendizaje consume el hackathon completo.
- GAMC aporta 7 capas de contexto (cuencas, cota 2750, emergencias) pero **nada resuelve
  el núcleo radar** del reto.
- El enunciado admite entregables narrativos (story map, video, "hasta una danza
  interpretativa"), lo que suaviza, pero la parte técnica es la más alta de los cuatro.

## Recomendación del equipo de datos

1. **Trend Detective** es la opción de mejor relación valor/esfuerzo: núcleo técnico simple,
   y es el **único reto con datos GAMC descargables reales** (Red MÓNICA) → diferenciación
   local sólida (detective de tendencias del microclima urbano de Cochabamba: temperatura
   satelital MERRA-2/GLDAS vs. estaciones terrestres; expansión urbana via capas GAMC).
2. **Field Shift** sigue siendo fuerte por la preparación ya invertida y su historia local
   (papa/maíz periurbano + presión urbana); es la opción "ya lista para ejecutar".
3. Hot Spots solo si el equipo tiene perfil de datos fuerte y acepta simplificar la
   armonización; SARs no recomendado para 24 h sin experiencia previa en radar.
