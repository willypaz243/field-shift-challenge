# Field Shift: Adapting Farms with NASA Data — NASA Space Apps Challenge 2026

> Fuente: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
> Dificultad: Advanced / Intermediate. Video oficial: https://www.youtube.com/watch?v=cF0U2WXsM7o

## Descripción del reto

Los agricultores enfrentan temperaturas cambiantes, patrones de lluvia irregulares, escasez de agua,
clima extremo y deterioro de la salud del suelo. **Reto:** crear una **herramienta de apoyo a la
decisión (decision-support tool)** que use observaciones terrestres de la NASA junto con información
local de suelos, características de cultivos y prioridades del agricultor, para ayudar a explorar
**estrategias de rotación de cultivos** que fortalezcan la salud del suelo y adapten las granjas a
condiciones cambiantes.

El resultado debe ser una herramienta de **apoyo** — identifica patrones y posibilidades, pero
**no reemplaza** el juicio del agricultor ni la experiencia agronómica local.

## Objetivos

- Combinar datos NASA + info local (suelo, cultivos, prioridades del agricultor) en una app, modelo,
  mapa interactivo u otra herramienta de decisión.
- Analizar patrones de: temperatura, estrés térmico, lluvia, humedad del suelo, evaporación,
  riesgo de heladas, precipitación extrema, estrés de vegetación y tendencias de agua a largo plazo.
- Considerar prioridades del agricultor: uso de agua, valor forrajero, fijación de nitrógeno,
  reducción de erosión, mejora de materia orgánica, adecuación al mercado.
- Destacar: periodos en que los campos están típicamente desnudos (bare fields), estaciones donde los
  cultivos actuales son más vulnerables, oportunidades de rotación que interrumpan ciclos de plagas,
  reduzcan demanda de agua, mejoren infiltración o generen ingresos adicionales.
- **Comparar al menos 3 estrategias de rotación, incluida la rotación actual**, explicando para cada
  una: por qué se sugirió, evidencia que la respalda, beneficios, brechas de información y riesgos
  que requieren revisión local por agricultores o expertos.

## Datasets sugeridos (NASA)

| Dataset | Uso |
|---|---|
| **SMAP** | Humedad de superficie del suelo y estado congelamiento/deshielo (cada 2–3 días). Estrés hídrico, infiltración, señales tempranas de estrés de cultivo. |
| **GPM / IMERG** | Precipitación global (tasa y acumulación). Fiabilidad de lluvia, tormentas extremas, riesgo de erosión, tendencias de humedad. |
| **Landsat** (30 m) / **MODIS** / **VIIRS** (250–1000 m) | Reflectancia, NDVI, índices de vegetación, estrés vegetal, suelo desnudo, transiciones estacionales. |
| **NASA POWER** | Datos agroclimatológicos: temperatura, humedad, radiación. Uso de agua de cultivos, temporada de crecimiento, riesgo de heladas, idoneidad climática. |
| **SRTM** | Elevación/terreno: pendiente, escorrentía, riesgo de erosión, flujo de agua. |
| **ECOSTRESS** | Temperatura superficial (LST) y evapotranspiración (ET) de alta resolución. Hotspots de estrés vegetal, microclima a nivel de campo. |
| **GRACE / GRACE-FO** | Tendencias de agua a largo plazo (almacenamiento). |
| **GEDI** | Biomasa, altura de dosel, estructura de vegetación (contexto del paisaje). |

## Datasets complementarios (no-NASA / agencias)

- **USDA Ag Data Commons** — datasets abiertos de agricultura (suelos, cultivos, manejo, fenología).
- **Web Soil Survey (WSS) / SSURGO / STATSGO2** — suelos oficiales de EE.UU.: textura, materia orgánica, drenaje, grupos hidrológicos, riesgo de erosión.
- **Cropland Data Layer (CDL) / CropScape** — clasificación de cultivos 30 m anual EE.UU.
- **PRISM Climate Data** (Oregon State) — precipitación, temperatura, fechas de heladas, normales de 30 años.
- **NAIP** — imágenes aéreas ~1 m (temporada de crecimiento EE.UU.).
- **NLCD (USGS)** — cobertura terrestre 30 m.
- **NLDAS / GLDAS** — series temporales continuas de clima/estado de superficie.
- **FAO GAEZ** — idoneidad agroclimática global por cultivo.
- **CoCoRaHS** — observaciones comunitarias de precipitación (validación de IMERG).
- **USGS NWIS** — niveles de agua subterránea, caudales, calidad de agua.
- **USDA AMS Market News** — precios y demanda de commodities (viabilidad de mercado de rotaciones).
- **USDA NASS QuickStats** — estadísticas agrícolas por condado (rendimientos, superficie plantada).
- **OpenET** — ET a escala de campo (oeste de EE.UU.), complementa ECOSTRESS y POWER.
- **USFS LANDFIRE** — vegetación, combustibles, características del paisaje.
- **ESA Copernicus Sentinel-2** — 10–20 m multiespectral (red-edge, NIR, SWIR), ideal para NDVI/EVI y detección de estrés a nivel de campo.
- **ERA5 (ECMWF)** — reanálisis climático horario global para rellenar huecos y construir series temporales.

## Consideraciones sugeridas (del enunciado)

### 1. Entender condiciones y datos
- Relacionar cambios de temperatura, humedad de suelo, lluvia, evaporación y estrés de vegetación
  con vulnerabilidad de cultivos y salud del suelo.
- Explicar términos científicos: evapotranspiración, anomalías de humedad de suelo, índices de
  vegetación (NDVI), riesgo de heladas, indicadores de balance hídrico.
- Aclarar cómo difieren las observaciones satelitales vs. mediciones en terreno, y cómo combinarlas
  mejora la precisión.

### 2. IA/Modelado/Fusión de datos ("SI" = sistemas inteligentes/IA)
- Comparar enfoques de IA/estadísticos para identificar patrones en histórico clima-suelo.
- Resaltar transiciones estacionales, periodos de campo desnudo, momentos de estrés de cultivos.
- Explicar incertidumbre del modelo y dónde se necesita validación de expertos locales.
- **Armonización de datasets**: remuestrear/agregar a una malla común de análisis para combinar
  SMAP + ECOSTRESS + GPM + Landsat/MODIS + GEDI + suelos en features coherentes y explicables.

### 3. Exploración de estrategias de rotación
- Comparar escenarios por: ciclo de nutrientes, riesgo de erosión, aporte de materia orgánica,
  interrupción de ciclos de plagas, uso de agua, potencial forrajero, consideraciones de mercado.
- Mapear qué rotaciones mejor se alinean con prioridades del agricultor.
- Explicar cómo contribuyen cultivos fijadores de nitrógeno, cultivos de cobertura, cultivos de raíz
  profunda y cultivos tolerantes a sequía a la salud del suelo a largo plazo.

### 4. Mapeo geoespacial y visualización
- Mapas interactivos de tendencias: humedad de suelo a largo plazo, olas de calor, declive de
  almacenamiento de agua.
- Visualizar vulnerabilidades a nivel de campo: zonas de riesgo de erosión, hotspots de estrés
  hídrico, áreas propensas a heladas.
- Add-ons opcionales: líneas de tiempo, overlays comparando datasets, sliders de escenarios
  (ajustar lluvia/temperatura).

### 5. Diseño centrado en el agricultor
- Interpretable para agricultores con poca experiencia técnica/geoespacial.
- Permitir que el agricultor ingrese prioridades y restricciones propias: disponibilidad de agua,
  limitaciones de equipos, preferencias de mercado.
- Recordatorios visibles de que la herramienta apoya —no reemplaza— la experiencia local, y señalar
  dónde es especialmente importante el juicio humano.