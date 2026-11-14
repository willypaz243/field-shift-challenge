# Referencias — proyectos existentes y enfoques (Field Shift 2026)

> Fecha de búsqueda: 14/11/2026. Compilación de referencias para decidir el alcance del MVP de 24 h.

## 1. Space Apps — ganadores y proyectos anteriores relevantes

### Zumorroda-X — Ganador Global 2025 (reto "Farm Navigators")
- Página del proyecto: <https://www.spaceappschallenge.org/2025/find-a-team/zumorroda-x?tab=project>
- **Qué hicieron:** juego educativo narrativo "Henry's Farm Adventures" (Phaser.js + Python/ML) que traduce datos NASA a mini-juegos: olas de calor (India 2021), inundaciones (Pakistán 2022, comparador de imágenes Landsat antes/después), salinización (Egipto), sequía y NDVI (EE.UU.), gestión de cultivos (Brasil, modelo IA de CO₂/adaptación).
- **Lección:** ganó global con *narrativa educativa + datos reales*, no con dashboards complejos. El detalle: historias locales + datos satelitales visibles.

### Otros proyectos del mismo ecosistema (Farm Navigators 2025)
- **AgriSure.ai** — dashboard MODIS NDVI + SMAP + GPM para recomendaciones de riego/agricultura: <https://www.instagram.com/reel/DQH5VRBkvqO>
- **AETERNA UD** (Facatativá, Colombia) — nominado global con enfoque en satélites y cultivos: <https://www.spaceappschallenge.org/2025/awards/global-nominees>
- **CropWatch AI** (arquetipo del hub de ganadores 2016–2025): Landsat/MODIS NDVI + SMAP + OpenET → heatmap NDVI, detección de estrés por sequía, dashboard de agricultor (Python ML + Earth Engine + React).
- Repo compilado de 10 años de ganadores: <https://github.com/Mahdi-hasan-shuvo/spaceappschallenge>

## 2. Proyectos open source de rotación de cultivos (lógica reutilizable)

| Proyecto | Enlace | Qué aporta |
|---|---|---|
| **boersanne/crop-rotation-planner** | <https://github.com/boersanne/crop-rotation-planner> | Planificador multi-año en el navegador, **cero dependencias**: detecta conflictos por familia botánica (periodos de descanso), premia buenas sucesiones. MIT. Es la lógica de rotación más fácil de portar. |
| **AgriOptima** | <https://github.com/UttamSingh809/Agrioptima> | Rotación + riego optimizada con Programación Dinámica: maximiza ganancia con presupuesto de agua y salud del suelo. |
| **Crop-recommendation-and-rotation-plan** | <https://github.com/andreeaacotos/Crop-recommendation-and-rotation-plan> | Algoritmo genético para planes de rotación de 2–5 años. |
| **Cropify** (MERN) | <https://github.com/amandaputney/Cropify> | UI de planificación/visualización de rotación para pequeñas fincas. |
| **soil_health_monitoring** | <https://github.com/mbreitenhuber/soil_health_monitoring> | Monitoreo de salud del suelo con Earth Observation (rotación, pastoreo). |
| **Awesome-Precision-Agriculture** | <https://github.com/ishandutta2007/Awesome-Precision-Agriculture> | Índice de herramientas/dashboards de agricultura de precisión. |

## 3. Estado del arte / papers (método)

| Referencia | Enlace | Idea clave |
|---|---|---|
| **AI4CROPR** (Fenz et al., 2023, comput. electron. agr.) | <https://www.sciencedirect.com/science/article/pii/S1161030123002174> | Deriva **matrices de rotación y valores de pre-cultivo** a partir de series temporales NDVI. Replicable en versión simplificada con NDVI MODIS/VIIRS para el valle. |
| **fruchtfolge** (DSS de rotación con big data espacial) | citado en <https://arxiv.org/html/2506.02384v1> | DSS de rotación espacialmente explícito; revisión de sistemas DSS satelitales. |
| USDA **CropSuit** | <https://www.facebook.com/AgriculturalResearchService/posts/485611800425559> | Web app de idoneidad de cultivos por suelo+clima — el patrón "slider de prioridades" que pide el reto. |
| Mapeo de rotaciones en áridos (NDVI + calendario local) | <https://www.nature.com/articles/s41598-026-57420-6> | NDVI time-series + calendario de siembra local → mapa de rotaciones. |

## 4. Qué se puede hacer en 24 h (síntesis)

- ✅ NASA POWER por API (sin auth, punto lat/lon) — clima, ET, heladas, radiación.
- ✅ Capas WMS GAMC (ya tienen API key y UUIDs) como contexto territorial.
- ✅ Lógica de rotación tipo *family conflicts + successions* (port de boersanne) + tabla de cultivos del valle de Cochabamba.
- ✅ NDVI MODIS/VIIRS para historial de "campo desnudo" / estrés estacional (o imágenes demo pre-descargadas).
- ⚠️ Evitar: modelos ML entrenados en el hackathon, pipelines Earth Engine, descargar SMAP L4 crudo.
