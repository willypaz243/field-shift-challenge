# Backlog — "Turnos del Valle" (Field Shift: Adapting Farms with NASA Data)

> Plan de 24–30 h (hackathon 14–15/11/2026). Equipo: web, UI/UX, ing. datos, BD, ML, sci. datos.
>
> **Objetivo del reto (obligatorio):** herramienta de **apoyo a la decisión** que combine datos
> NASA + información local (suelos, cultivos, prioridades del agricultor) para ayudar a adaptar
> la granja a condiciones cambiantes. El enunciado exige **comparar al menos 3 estrategias de
> rotación, incluida la rotación actual** — ver [CHALLENGE.md](./CHALLENGE.md).
> La app **apoya, no reemplaza** el juicio del agricultor (recordatorio visible en UI).

---

## 1. Producto en una línea

El agricultor elige **zona** (comuna, vía GPS o selección) y **cultivo** (papa, choclo, lechuga,
haba, etc.). La app le devuelve:

1. **Ventana óptima de siembra→cosecha** del próximo año (rango de fechas + confianza),
   comparando el **vector de condiciones óptimas del cultivo** contra la **proyección climática
   diaria** (mismas variables) sobre una ventana de duración = ciclo del cultivo.
2. **Alertas** (1–2 semanas antes) cuando la proyección replica el patrón climático que
   precedió a **eventos históricos imprevistos** (helada, granizo, inundación, sequía).
3. **Recomendaciones de rotación** (≥3 estrategias vs. la actual) con evidencia local.

Todo el cálculo de comparación se hace **en el dispositivo**; el servidor solo entrega
proyecciones y catálogo (offline-first, mínima dependencia de internet).

## 2. Arquitectura

```
FUENTES                      ETL (ingest)                  SERVIDOR                     MOVIL (offline-first)
─────────────────────────    ──────────────    ──────────────────────────────          ─────────────────────
NASA POWER (diaria 1984+) ─┐
GPM/IMERG  (diaria 2000+) ─┼─► ETL ─► DB ──► modelo serie temporal ─► API ─► sync JSON ──► DB local
SMAP L4    (3h  2015+)   ─┤    (limpio,       (clima histórico)       /zones    cultivos +     (SQLite)
GAMC WMS   (zonas)      ─┤     normaliza,     ─► proyección 365 d ── /crops    proyección      ─► scoring local
SRTM       (elev/pend)  ─┘     carga)         ─► band. incertid.    /forecasts  del año       ─► ventana óptima
eventos hist. (curado)  ───────┘              ─► reglas de alerta ── /sync     ──────────────  ─► alertas locales
```

- **Zonas de análisis:** solo zonas **agrícolas** del Cercado (delimitadas con GAMC, ver §4).
- **Proyecciones en cache:** la API genera/actualiza la proyección anual por zona (cron)
  y la guarda en `forecasts`; el móvil nunca entrena ni proyecta.
- **Comparación en dispositivo:** vector cultivo × serie proyectada → ventana óptima (misma
  función de scoring que en el servidor, para poder validar que devuelven lo mismo).

## 3. Fuentes de datos (decisiones)

| # | Fuente | Qué aporta | Rango | Formato / acceso | Prioridad |
|---|---|---|---|---|---|
| 1 | **NASA POWER** (Power-DA) | Clima **diario**: T2M/T2Max/T2Min, PRECTOT, RH2M, WS2M, SW, Q2M, PS | **1984 → presente** (cubre 2010–2025 + antes ✅) | JSON por punto vía API (token Earthdata gratuito); 0.5° | **P0** |
| 2 | **GPM / IMERG** | Precipitación satelital diaria (validación de POWER, tormentas extremas) | 2000 → presente | HDF5 vía Earthdata/CMR (subconjunto bbox valle) | P1 |
| 3 | **SMAP L4 SPL4SMGP v8** | **Humedad de suelo** superficial + zona radicular (3-h → promedio diario) | **2015-03-31 → presente** | HDF5, 9 km, EASE-Grid (EPSG:6933), Earthdata; DOI 10.5067/T5RUATAQREF8 | P1 |
| 4 | **GAMC WMS** (key p04) | Zonas: periurbanos (mask urbano), distritos/comunas, drenaje | estático | WMS vía proxy (rate limit 10–15 s/peticion) | **P0** (obligatorio) |
| 5 | **SRTM 30 m** | Elevación + pendiente por zona (erosión, escorrentía) | estático | Tiled GeoTIFF (dwtkns/earthdata) | P2 |
| 6 | **Cultivos** (CROPS.md) | Vector de condiciones óptimas por cultivo (T, heladas, agua, ciclo, fixN, mercado) | curado | tabla local `crops` | **P0** |
| 7 | **Eventos históricos** | Fechas de eventos imprevistos (helada/granizo/inundación/sequía) para alertas | curado 10–20 eventos | tabla local `events` | P1 |

> **Nota SMAP (verificado 14/11 en nsidc.org/data/spl4smgp/versions/8):**
> - Producto 3-horario (no 9-días), 9 km; **un solo píxel puede cubrir varias comunas**
>   (el valle ocupa ~2×2 píxeles) → tratarlo como "humedad de suelo del valle", no por comuna.
> - ⚠️ **14/05/2026–28/07/2026**: problema de geolocalización, datos en reprocesamiento →
>   excluir ese tramo del entrenamiento (o marcarlo).
> - Requiere cuenta Earthdata (gratis) y descarga por script Python (Data Access Tool).
> - Variables: surface soil moisture, root zone soil moisture, frozen fraction, incertidumbre.

> **Nota POWER:** la serie diaria 1984+ resuelve el requisito "2010–2025 y antes si es
> posible". Usar 2010–2025 como ventana de entrenamiento principal; 1984–2009 como
> contexto/climatología larga.

## 4. Uso de datos GAMC (obligatorio del reto) — 4 utilidades concretas

| # | Capa GAMC | Utilidad en el problema | Cómo |
|---|---|---|---|
| G1 | **Periurbanos** (mask) | **Excluir zonas urbanas** de la malla de análisis (requisito: "solo zonas agrícolas") y detectar **presión urbanística** sobre tierras de cultivo → narrativa central de *Field Shift*: la agricultura se está "shiftando" | GetMap alta resolución (800×512+) → binarizar PNG (naranja+verde = urbano) → mask por grid point |
| G2 | **Limite Distritos** (GetFeatureInfo) | **Selector de zona** del agricultor (comuna) y **granularidad de la proyección/cache** (D1–D12; verificado D4=MOLLE, D9=ITOCTA, D12=ADELA ZAMUDIO) | 1 GetFeatureInfo por grid point → `zones.comuna` |
| G3 | **Drenaje e Influencia** (mask) | **Riesgo de erosión/inundación** por cercanía a quebradas → penaliza cultivos sensibles (papa en faldeos, hortalizas en zona de influencia) | GetMap → distancias a líneas en raster; featureinfo vacío (12 pts) → solo uso visual/mask |
| G4 | **Cota 2750** (contexto CROPS.md; capa en p02, no autorizada por key p04) | **Zonificación altitudinal**: >2750 m = uso agrícola-forestal no urbanizable (papaliza, haba, tarwi, avena) vs. valle (hortalizas, choclo) | SRTM elevación + conocimiento documentado; pedir a GAMC acceso a la capa si da tiempo |

> Bonus (si sobra tiempo): CSVs MÓNICA PM10 (ya descargados) como contexto de calidad de
> aire en alertas.

## 5. Esquema de datos (DB)

```sql
zones(id, nombre, comuna, distrito, lat, lon, elev_m, pendiente,
      es_agricola bool,            -- mask GAMC periurbanos
      cerca_drenaje int,           -- dist. a quebrada (m)
      altitud_alta bool)           -- >2750 m

climate_history(zone_id, fecha, tmin, tmax, tmean, pmm, rh, sw, ws,
                sm_surface, sm_root)   -- sm_* desde 2015 (SMAP)

crops(id, nombre, t_opt_min, t_opt_max, tol_helada enum, demanda_agua enum,
      ciclos_dias int, fix_n bool, mercado enum, foto_url)
      -- vector de condiciones óptimas (CROPS.md)

events(id, tipo, fecha, zona_id, descripcion, fuente)

forecasts(zone_id, anio, fecha, tmin, tmax, tmean, pmm, rh, sw, ws,
          sm_surface, sm_root,          -- proyección diaria 365 d
          incert_min, incert_max,       -- banda de incertidumbre
          creado_en)                     -- cache: se regenera por cron

sync_version(id, creado_en, hash)       -- versionado para sync delta del móvil
```

**Vector de características común** (cultivo ↔ proyección):
`[tmin, tmax, tmean, pmm, rh, sw, ws, sm_surface, sm_root]` — el cultivo define rangos
óptimos por variable + penalizadores (helada, déficit hídrico), no una distribución.

## 6. Backlog por fases

### Fase 0 — Bases (hoy, 2–3 h) — *bloqueante*
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 0.1 | Cuenta Earthdata + token API POWER | 0,5 h | `curl` de POWER para 1 punto del valle devuelve JSON diario |
| 0.2 | Definir grid de zonas: 1–3 puntos agrícolas por distrito (D1–D12) usando mask periurbanos | 1 h | Lista de ~15–25 zonas (lat/lon, comuna vía GetFeatureInfo GAMC) |
| 0.3 | Definir schema (§5) + repo de datos (`data/`, `src/etl`, `src/model`, `api/`, `app/`) | 0,5 h | Schema documentado; estructura de carpetas |
| 0.4 | Catálogo de cultivos en tabla `crops` (de CROPS.md: papa, choclo, trigo, papaliza, hortalizas/lechuga, alfalfa, haba, tarwi, quinua, avena, flores, durazno) | 1 h (paralelo) | ≥10 cultivos con vector de condiciones |

### Fase 1 — ETL: explorar, extraer, cargar (hoy→noche, 4–6 h) — *prioridad máxima*
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 1.1 | **POWER** diario 1984–2025-11 para todos los puntos del grid | 2 h | CSV/DB por zona sin huecos (interpolación lineal ≤3 días si los hay) |
| 1.2 | **GPM/IMERG** diario 2010–2025 (bbox valle) | 1,5 h | Serie de precipitación cruzada con POWER (correlación > 0,8 como sanity check) |
| 1.3 | **SMAP SPL4SMGP v8** 2015–2025: píxeles del valle, 3-h → promedio diario, reproyección EASE→WGS84; excluir 2026-05/07 | 1,5 h | `sm_surface`/`sm_root` diarios en DB |
| 1.4 | **GAMC**: mask periurbanos (binaria), distancias a drenaje, comuna por punto | 1 h (batch con sleeps 12 s) | `zones.es_agricola`, `cerca_drenaje`, `comuna` |
| 1.5 | **SRTM** elevación/pendiente por zona | 0,5 h | `zones.elev_m`, `pendiente` |
| 1.6 | Carga a DB + script de re-ejecución idempotente | 1 h | `bash etl.sh` reconstruye todo desde cero |
| 1.7 | **Eventos históricos** (10–20: heladas, granizadas, inundaciones, sequías del valle; fuentes prensa/BOCU/SNIG) | 1 h (paralelo) | `events` con fecha + zona + tipo |

**Hito 1 (noche del día 1):** DB completa (clima 2010+ por zona, cultivos, eventos, zonas GAMC) → **datos listos para entrenar**.

### Fase 2 — Modelos (noche día 1 → mañana día 2, 4–5 h)
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 2.1 | EDA + validación de series contra conocimiento local (lluvia dic–feb, heladas may–ago, seca may–sep) | 1 h | Informe corto de anomalías/validación |
| 2.2 | Modelo serie temporal por zona/variable: **estacionalidad (Fourier/Prophet) + tendencia + residuo**; alternativa SARIMA | 2 h | Proyección 365 d por variable con banda de incertidumbre |
| 2.3 | **Backtest**: holdout 2024–2025 → MAE/RMSE por variable (número para el pitch) | 0,5 h | Métricas documentadas |
| 2.4 | **Scoring de ventana**: para cada ventana de L días (ciclo del cultivo) en la proyección, score = cumplimiento de rangos óptimos − penalizadores (heladas, déficit agua, erosión por drenaje) | 1 h | Top-3 ventanas + confianza por cultivo/zona; función compartida servidor↔móvil |
| 2.5 | **Reglas de alerta**: firma climática de N días previos a cada evento histórico (T, lluvia, días secos) → similitud con ventanas proyectadas > umbral → alerta | 1 h | ≥1 regla funcional (helada o lluvia extrema) con 5+ eventos |
| 2.6 | **Módulo rotaciones** (requisito oficial): ≥3 estrategias vs. rotación actual (papa→trigo→maíz), score por agua/fixN/erosión/mercado (CROPS.md) | 1 h (paralelo UI) | 3 estrategias comparables con "por qué se sugirió / evidencia / riesgos" |

### Fase 3 — API + cache (mañana día 2, 3 h)
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 3.1 | FastAPI: `GET /zones` (agrícolas), `GET /crops`, `GET /zones/{id}/forecast?anio=` | 1,5 h | Endpoints documentados (OpenAPI) |
| 3.2 | **Cron de proyecciones**: regenera `forecasts` por zona (semanal + on-demand) → cache BD | 1 h | Tabla `forecasts` poblada; regeneración idempotente |
| 3.3 | `GET /sync` (JSON versionado: crops + forecasts de la comuna seleccionada) | 0,5 h | Payload < 500 KB; delta por `sync_version` |

### Fase 4 — Móvil offline-first (día 2, 4–6 h, paralelo) — *según mockup Figma*
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 4.1 | Pantallas: cultivo+foto, **indicar zona (GPS) + confirmar**, calendario clima (proyección semanal), reporte general histórico, registro/retroalimentación, notificaciones | 3 h | Mockup cubierto; flujo demo completo |
| 4.2 | **Sync**: al conectar a internet → descarga crops + proyección de la comuna → SQLite local | 1 h | La app funciona 100 % sin internet tras el primer sync |
| 4.3 | **Scoring en dispositivo** (misma función que 2.4) → ventana óptima (fecha inicio/fin + guía) | 1 h | Resultado idéntico al servidor (test) |
| 4.4 | **Notificaciones locales** 1–2 semanas antes (eventos previstos por patrón) + aviso de eventos de otros usuarios cercanos | 1 h | Notificación push local con la ventana de riesgo |
| 4.5 | **Retroalimentación**: el agricultor registra cosecha/ventana real → se guarda local y se sincroniza (comunidad: alertar a usuarios cercanos) | 0,5 h | Registro funcional (stretch) |
| 4.6 | Recordatorio visible: "apoya, no reemplaza" + dónde cuenta el juicio local | 0,25 h | Texto en pantalla de resultado |

### Fase 5 — Demo y pitch (cierre día 2, 3 h)
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 5.1 | Demo: elegir comuna + cultivo → ventana óptima + alerta + mapa GAMC (capas WMS en mapa) | 1 h | Flujo sin errores en vivo |
| 5.2 | Pitch alineado al reto: NASA (POWER/GPM/SMAP) + **GAMC (zonas, presión urbana, drenaje)** + rotaciones (≥3) + incertidumbre + apoyo-no-reemplazo | 1 h | Guion 5 min |
| 5.3 | Video 3–5 min | 1 h | Grabado |

## 7. Cortes de MVP (si falta tiempo, en orden de descarte)

1. **Móvil → PWA web** (si el nativo no cierra a tiempo; el scoring local funciona igual).
2. **Eventos/alertas → 1 regla + 5 eventos** (helada o lluvia).
3. **Rotaciones → tabla estática** de 3 estrategias (sin scoring dinámico).
4. **Zonas → 5 comunas** en vez de 12 (Itocta, Molle, A. Zamudio, Tiquipaya, Valle Hermoso).
5. **SMAP → descartar** (quedan POWER + GPM; humedad de suelo se menciona como "próximamente").
6. **SRTM → descartar** (pendiente/erosión se toma de la capa drenaje GAMC).
7. **GPM → solo POWER** (una sola fuente de clima).

## 8. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Earthdata/token POWER tarde | **Alto** (bloquea todo) | **Tarea 0.1 primera de hoy**; fallback: POWER vía Earthdata Search (descarga manual de 1–2 puntos) |
| SMAP 9 km grueso + reprocesamiento 2026-05/07 | Medio | Trato "valle" no comunal; excluir tramo; es P1 descartable |
| Rate limit GAMC (429) | Medio | Batch con sleeps 12 s (script probado); todo lo descargable ya está en `data/gamc/04/` |
| Proyección 1 año "honestidad" | Medio (pitch) | Enmarcar como **ciclo estacional + tendencia + incertidumbre** (no "predicción mágica"); mostrar backtest con números |
| FeatureInfo drenaje vacío | Bajo | Solo mask visual (G3); no depende de atributos |
| Vector cultivo ↔ proyección con variables de rangos distintos | Medio | Misma lista de variables en ambas (§5); rangos con tolerancia (p.ej. ±1 °C) |
| Cota 2750 no autorizada por key p04 | Bajo | SRTM + conocimiento documentado (CROPS.md); pedir acceso a GAMC si da tiempo |

## 9. Timeline resumiendo (24 h)

```
DÍA 1 (sábado)                    DÍA 2 (domingo)
─────────────────────────────────  ─────────────────────────────────
06:00  F0: Earthdata, grid, schema, cultivos
09:00  F1: ETL (POWER→GPM→SMAP→GAMC→SRTM→eventos)
18:00  Hito 1: DB lista para entrenar
22:00  F2: EDA + modelo + backtest + scoring
06:00  F2: alertas + rotaciones
09:00  F3: API + cron cache          F4: móvil (UI + sync + scoring local)
15:00  Integración API↔móvil
18:00  F5: demo + pitch + video
```

## 10. Referencias

- Reto oficial: <https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/> · [CHALLENGE.md](./CHALLENGE.md)
- SMAP v8: <https://nsidc.org/data/spl4smgp/versions/8> (DOI 10.5067/T5RUATAQREF8)
- POWER API: <https://power.larc.nasa.gov/api/documents/>
- Series temporales (ref. equipo): <https://www.ibm.com/mx-es/think/topics/time-series-model>
- Cultivos y condiciones óptimas: [CROPS.md](./CROPS.md) · Contexto local: [LOCAL-CONTEXT.md](./LOCAL-CONTEXT.md)
- Acceso GAMC (live): [GAMC-ACCESS.md](./GAMC-ACCESS.md) · Datos descargados: [data/gamc/04/](../data/gamc/04/README.md)
- Mockup: Figma "Field Shift — App Agricultor (mobile)"
