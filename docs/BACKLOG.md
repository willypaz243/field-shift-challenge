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
| 1 | **NASA POWER** (Power-DA) | Clima **diario**: T2M, T2MDEW, RH2M, WS2M, PS, PRECTOT, TS, SW/LW (all-sky). Base para **ET₀ (Hargreaves)** | **1984 → presente** (cubre 2010–2025 + antes ✅) | JSON por punto vía API, 0.5° — **verificado 14/11: funciona SIN token** (v2.10.3); `start`/`end` = int `YYYYMMDD`; **no hay T2MIN/T2MAX en diario** | **P0** |
| 1b | **ERA5** (CDS ECMWF) | **t2m_min / t2m_max** diarios (heladas) + validación de T2M | **1940 → presente** | API CDS (clave gratis en cds.climate.copernicus.eu); `reanalysis-era5-single-levels` | **P0** |
| 2 | **GPM / IMERG** | Precipitación satelital diaria (validación de POWER, tormentas extremas) | 2000 → presente | NetCDF vía Earthdata/CMR (`GPM_3IMERGDL` diario, `GPM_3IMERGHH` 30-min); ✅ **EULA aceptado 14/11** | P1 |
| 3 | **SMAP L4 SPL4SMGP v8** | **Humedad de suelo** superficial + zona radicular (3-h → promedio diario) | **2015-03-31 → presente (brecha 2026-05/07 ya rellena, verificado)** | HDF5 9 km EASE-Grid (EPSG:6933); descarga directa CMR+token verificada; **granules globales ~148 MB** (~1,3 GB/día) | P1 |
| 4 | **GAMC WMS** (key p04) | Zonas: periurbanos (mask urbano), distritos/comunas, drenaje | estático | WMS vía proxy (rate limit 10–15 s/peticion) | **P0** (obligatorio) |
| 5 | **SRTM 30 m** | Elevación + pendiente por zona (erosión, escorrentía) | estático | Tiled GeoTIFF (dwtkns/earthdata) | P2 |
| 6 | **Cultivos** (CROPS.md) | Vector de condiciones óptimas por cultivo (T, heladas, agua, ciclo, fixN, mercado, **plagas, forraje, sequía**) | curado | tabla local `crops` | **P0** |
| 7 | **Eventos históricos** | Fechas de eventos imprevistos (helada/granizo/inundación/sequía) para alertas | curado 10–20 eventos | tabla local `events` | P1 |
| 8 | **GEOS-FP / GEOS-S2S** (NASA) | **Pronóstico de corto plazo (28 días)** para la app (complementa el modelo estacional) | presente → +28 d | API JSON (GMAO) | P1 |
| 9 | **Landsat 8/9 / Sentinel-2** | **NDVI** (estrés vegetal, campo desnudo / bare fields), límites de parcelas | 2013+ / 2015+ | COG/GeoTIFF (USGS/AWS) | P2 |
| 10 | **Riego N°1 La Angostura** (local) | **Nivel de represa** (%) → disponibilidad de agua para riego, alertas | continuo | CSV/API local (asociación) | P1 |

> **Armonización de datasets (decisión):** todos los productos se llevan a una **malla común de ~1 km**
> para clima/suelo y **~30 m** para NDVI/parcelas (ver API-CONTRACT §11). POWER 0.5° → interpolación
> bilineal; SMAP 9 km → promedio de píxeles del valle; IMERG 0.1° → resampling al punto; GAMC vector →
> punto en polígono. La app no ve las resoluciones originales: solo la malla unificada.

> **Nota SMAP (verificado 14/11 en nsidc.org + CMR en vivo con token Earthdata):**
> - Producto 3-horario (no 9-días), 9 km; **un solo píxel puede cubrir varias comunas**
>   (el valle ocupa ~2×2 píxeles) → tratarlo como "humedad de suelo del valle", no por comuna.
> - ✅ **La ventana de reprocesamiento 14/05/2026–28/07/2026 ya está CUBIERTA** (verificado
>   en vivo en CMR: 9 granules/día en el bbox el 15/06, 20/07, 15/10 y 01/11 de 2026).
>   No excluir ese tramo.
> - Acceso verificado en vivo (token `EARTHDATA_TOKEN` del `.env`):
>   - Colección `C3480440870-NSIDC_CPRD` (SPL4SMGP v8, NSIDC_CPRD).
>   - Búsqueda de granules por `bounding_box` + `temporal` en CMR ✅.
>   - Descarga directa HTTPS con `Bearer` ✅ (~148 MB/granule, 6.5 s).
> - Variables: surface soil moisture, root zone soil moisture, frozen fraction, incertidumbre.
>
> **Nota GPM/IMERG (verificado 14/11 en CMR con token):**
> - Colecciones disponibles: `GPM_3IMERGDL` (diaria, v07, `C2723754859-GES_DISC`) y
>   `GPM_3IMERGHH` (30-min, v07, `C2723754847-GES_DISC`). `GPM_3GR` **ya no existe** en CMR.
> - Granules por el bbox del valle: ~1/día (IMERGDL).
> - ⚠️ **La descarga de IMERG devuelve 403 `EULA Acceptance Failure`**: hay que aceptar el
>   EULA una vez desde la cuenta Earthdata en
>   `https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ`
>   (el SMAP no lo pide). Pendiente de acción del equipo.

> **Nota POWER (verificado en vivo el 14/11, API v2.10.3):**
> - **Funciona sin token** (probado 2× sin `token` y con token inválido). El token oficial
>   (https://power.larc.nasa.gov/api/tokens/, email → 32 chars) sigue recomendado como
>   buena práctica, pero no bloquea.
> - `start`/`end` = **entero `YYYYMMDD`** (no epoch). Rango disponible: 1981/1984 → presente.
> - Parámetros válidos del diario `community=ag`: `T2M, T2MDEW, RH2M, WS2M, PS, PRECTOT, TS,
>   ALLSKY_SFC_SW_DWN, ALLSKY_SFC_LW_DWN, CLRSKY_SFC_SW_DWN`. **NO existen** `T2MIN/T2MAX`
>   ni `ET/SWC/Q2M` en diario.
> - **tmin/tmax (heladas):** derivar de **hourly `T2M`** (verificado: 2025-11-01 → min 8.6 °C
>   05:00, max 23.1 °C 12:00) o usar **ERA5** (`t2m_min/t2m_max`, 1940+).
> - La respuesta incluye la **elevación del punto** (Cochabamba valle: 3126 m) → útil para
>   `zones.elev_m` sin SRTM.
> - Ejemplo verificado:
>   `https://power.larc.nasa.gov/api/temporal/daily/point?latitude=-17.39&longitude=-66.17&start=20251101&end=20251107&parameters=T2M,PRECTOT,RH2M,WS2M,PS&community=ag&format=JSON`
>
> **Nota de ventana de entrenamiento:** usar 2010–2025 como principal; 1984–2009 como
> contexto/climatología larga (resuelve el requisito "antes de 2010 si es posible").

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

parcels(id, zone_id, lat, lon, area_m2, fuente_agua enum,
        prioridad enum)            -- agua/tierra/forraje/vender (perfil agricultor)

climate_history(zone_id, fecha, tmin, tmax, tmean, pmm, rh, sw, ws,
                et0,                          -- ET₀ Hargreaves (mm/día)
                sm_surface, sm_root)         -- sm_* desde 2015 (SMAP)

crops(id, nombre, t_opt_min, t_opt_max, tol_helada enum, demanda_agua enum,
      ciclos_dias int, fix_n bool, mercado enum,
      breaks_pest_cycle bool,        -- interrumpe ciclo de plagas
      forage_value enum,            -- bajo/medio/alto
      drought_tolerant enum,        -- no/poco/alto
      deep_rooting bool,            -- raíz profunda (infiltración)
      kcInicial float, kcMedio float, kcFinal float,  -- FAO-56
      foto_url)
      -- vector de condiciones óptimas (CROPS.md) + criterios de rotación

events(id, tipo, fecha, zona_id, descripcion, fuente)

reservoir(id, nombre, nivel_pct, volumen_hm3, estado enum, actualizado_en)
          -- La Angostura (Riego N°1)

forecasts(zone_id, anio, fecha, tmin, tmax, tmean, pmm, rh, sw, ws,
          et0, sm_surface, sm_root,   -- proyección diaria 365 d
          incert_min, incert_max,     -- banda de incertidumbre
          creado_en)                   -- cache: se regenera por cron

reports(id, parcela_id, tipo, fecha, foto_url, audio_url, enviado_en)
        -- reportes comunitarios (sin nombre)

sync_version(id, creado_en, hash)       -- versionado para sync delta del móvil
```

**Vector de características común** (cultivo ↔ proyección):
`[tmin, tmax, tmean, pmm, rh, sw, ws, et0, sm_surface, sm_root]` — el cultivo define rangos
óptimos por variable + penalizadores (helada, déficit hídrico, erosión), no una distribución.

**Dimensiones de scoring de rotaciones** (ver API-CONTRACT §6):
`[agua, tierra, forraje, vender]` — cada plan de rotación se puntúa 1–3 por dimensión.
El peso de cada dimensión lo determina `objetivo` (perfil del agricultor) + `epoca` (seca/lluvias).
Criterios adicionales: `fix_n`, `breaks_pest_cycle`, `drought_tolerant`, `deep_rooting`,
`meses_sin_cultivo` (bare field), `cerca_drenaje` (erosión).

## 6. Backlog por fases

### Fase 0 — Bases (hoy, 2–3 h) — *bloqueante*
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 0.1 | Claves de acceso: **CDS (ERA5)** — registro gratis + API key; Earthdata (para SMAP, P1, puede esperar). **POWER ya no pide token** (verificado 14/11) | 1 h | `curl` de POWER devuelve JSON diario ✅ (hecho); **token Earthdata ✅ en `.env` y verificado en vivo (CMR + descarga SMAP)**; `cdsapi` de ERA5 pendiente |
| 0.2 | Definir grid de zonas: 1–3 puntos agrícolas por distrito (D1–D12) usando mask periurbanos | 1 h | Lista de ~15–25 zonas (lat/lon, comuna vía GetFeatureInfo GAMC) |
| 0.3 | Definir schema (§5) + repo de datos (`data/`, `src/etl`, `src/model`, `api/`, `app/`) | 0,5 h | Schema documentado; estructura de carpetas |
| 0.4 | Catálogo de cultivos en tabla `crops` (de CROPS.md: papa, choclo, trigo, papaliza, hortalizas/lechuga, alfalfa, haba, tarwi, quinua, avena, flores, durazno). **Campos necesarios para rotaciones**: `fix_n`, `breaks_pest_cycle`, `forage_value`, `drought_tolerant`, `deep_rooting`, `erosion_sens`, `kc{inicial,medio,final}` (FAO-56), `mercado` | 1,5 h (paralelo) | ≥10 cultivos con vector de condiciones + **criterios de rotación completos** (ver API-CONTRACT §4) |

### Fase 1 — ETL: explorar, extraer, cargar (hoy→noche, 4–6 h) — *prioridad máxima*
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 1.1 | **POWER** diario 1984–2025-11 para todos los puntos del grid | 2 h | CSV/DB por zona sin huecos (interpolación lineal ≤3 días si los hay) — ✅ **HECHO 14/11**: 10 zonas × 15,342 filas (1984-01-01→2025-12-31), `tmean` 100% completo, `tmin/tmax` 2010+ sin huecos (derivado de hourly), `lw` solo nulo 1984–87. Heladas 2010–25: 194 días, pico may–sep ✅ coherente con CROPS.md. Nota: los 10 puntos caen en la **misma celda POWER 0.5°** (serie idéntica; solo difiere `elev_m`=3126 m) → el refinamiento por zona lo dan GAMC + SRTM |
| 1.2 | **GPM/IMERG** diario 2010–2025 (bbox valle) | 1,5 h | Serie de precipitación cruzada con POWER (correlación > 0,8 como sanity check) |
| 1.3 | **SMAP SPL4SMGP v8** 2015–2025: píxeles del valle, 3-h → promedio diario, reproyección EASE→WGS84 (brecha 2026-05/07 ya cubierta; ⚠️ granules globales ~148 MB → decidir ventana/estrategia de descarga) | 1,5 h | `sm_surface`/`sm_root` diarios en DB |
| 1.4 | **GAMC**: mask periurbanos (binaria), distancias a drenaje, comuna por punto | 1 h (batch con sleeps 12 s) | `zones.es_agricola`, `cerca_drenaje`, `comuna` |
| 1.5 | **SRTM** elevación/pendiente por zona | 0,5 h | `zones.elev_m`, `pendiente` |
| 1.6 | Carga a DB + script de re-ejecución idempotente | 1 h | `bash etl.sh` reconstruye todo desde cero |
| 1.7 | **Eventos históricos** (10–20: heladas, granizadas, inundaciones, sequías del valle; fuentes prensa/BOCU/SNIG) | 1 h (paralelo) | `events` con fecha + zona + tipo |

**Hito 1 (noche del día 1):** DB completa (clima 2010+ por zona, cultivos, eventos, zonas GAMC) → **datos listos para entrenar**.

### Fase 2 — Modelos (noche día 1 → mañana día 2, 5–6 h)
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 2.1 | EDA + validación de series contra conocimiento local (lluvia dic–feb, heladas may–ago, seca may–sep) | 1 h | Informe corto de anomalías/validación |
| 2.2 | Modelo serie temporal por zona/variable: **estacionalidad (Fourier/Prophet) + tendencia + residuo**; alternativa SARIMA. Incluir **ET₀ (Hargreaves)** como variable derivada: `ET₀ = 0.0023 × (Tmean+15) × √RA` | 2 h | Proyección 365 d por variable (incl. ET₀) con banda de incertidumbre |
| 2.3 | **Backtest**: holdout 2024–2025 → MAE/RMSE por variable (número para el pitch) | 0,5 h | Métricas documentadas |
| 2.4 | **Scoring de ventana**: para cada ventana de L días (ciclo del cultivo) en la proyección, score = cumplimiento de rangos óptimos − penalizadores (heladas, déficit agua [pmm vs ET₀×Kc], erosión por drenaje) | 1 h | Top-3 ventanas + confianza por cultivo/zona; función compartida servidor↔móvil |
| 2.5 | **Reglas de alerta**: firma climática de N días previos a cada evento histórico (T, lluvia, días secos) → similitud con ventanas proyectadas > umbral → alerta | 1 h | ≥1 regla funcional (helada o lluvia extrema) con 5+ eventos |
| 2.6 | **Módulo rotaciones** (requisito oficial): ≥3 estrategias vs. rotación actual (papa→trigo→maíz). **Estructura por plan** (ver API-CONTRACT §6): `por_que`, `bueno[]`, `riesgos[]`, `falta_saber[]`, `evidencia[{codigo, fuente}]`, `puntaje{agua,tierra,forraje,vender}`, `etiquetas[]`, `confianza`. Criterios de scoring: agua (ET₀ vs pmm), tierra (fixN, erosión, materia orgánica), forraje (valor), vender (mercado), plagas (`breaks_pest_cycle`), bare field (`meses_sin_cultivo`) | 1,5 h (paralelo UI) | 3+ estrategias con los **5 campos completos** (por qué, evidencia, beneficios, brechas, riesgos) + puntaje por 4 objetivos |

### Fase 3 — API + cache (mañana día 2, 3–4 h)
> **Referencia:** [`API-CONTRACT.md`](API-CONTRACT.md) define todos los endpoints, formatos y códigos.
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 3.1 | FastAPI: endpoints del API-CONTRACT §1–§8 (parcelas, clima, agua, cultivos, rotaciones, avisos, zona) | 2 h | Endpoints documentados (OpenAPI); response schemas coinciden con API-CONTRACT |
| 3.2 | **Cron de proyecciones**: regenera `forecasts` por zona (semanal + on-demand) → cache BD. Incluir **ET₀** y **pronóstico 28 d (GEOS)** si disponible | 1 h | Tabla `forecasts` poblada; `/clima/pronostico?dias=28` funcional |
| 3.3 | `GET /sync` (JSON versionado: crops + forecasts + rotaciones de la comuna) | 0,5 h | Payload < 500 KB; delta por `sync_version` |
| 3.4 | **`GET /rotaciones`** con la estructura completa de API-CONTRACT §6 (5 campos por plan + puntaje por 4 objetivos + `objetivo` param) | 0,5 h | Response tiene `por_que`, `bueno[]`, `riesgos[]`, `falta_saber[]`, `evidencia[]` |

### Fase 4 — Móvil offline-first (día 2, 5–7 h, paralelo) — *según mockup Figma + FLUJO-APP.md*
> **Referencia:** [`FLUJO-APP.md`](FLUJO-APP.md) define las 9 pantallas y los flujos.
> [`API-CONTRACT.md`](API-CONTRACT.md) define los endpoints que la app consume.
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 4.1 | Pantallas (FLUJO-APP §1): **onboarding** (GPS + fuente agua + **prioridad: agua/tierra/forraje/vender**), Hoy, Calendario, Sembrar, Mi cultivo, Rotaciones, Mi zona, Avisos | 3 h | 9 pantallas del mockup; flujo demo completo |
| 4.2 | **Sync**: al conectar a internet → descarga crops + forecasts + rotaciones de la comuna → SQLite local | 1 h | La app funciona 100 % sin internet tras el primer sync |
| 4.3 | **Scoring en dispositivo** (misma función que 2.4) → ventana óptima (fecha inicio/fin + guía) | 1 h | Resultado idéntico al servidor (test) |
| 4.4 | **Notificaciones locales** 1–2 semanas antes (eventos previstos por patrón) + aviso de eventos de otros usuarios cercanos | 1 h | Notificación push local con la ventana de riesgo |
| 4.5 | **Retroalimentación + reportes comunitarios**: cosecha (buena/regular/mala) + "avisar algo" (sin_agua, helada, granizo, inundación, plaga) → cola offline → `POST /reportes` | 1 h | Registro funcional; reportes aparecen en mapa de zona (sin nombre) |
| 4.6 | **Rotaciones en UI**: pantalla "¿Qué sembrar después?" con selector de objetivo + 3+ planes con los 5 campos (por qué, evidencia, beneficios, brechas, riesgos) + "Quiero este plan" | 0,5 h | Estructura visual coincide con API-CONTRACT §6 |
| 4.7 | Recordatorio visible: "apoya, no reemplaza" + dónde cuenta el juicio local + **tooltips de términos científicos** (ET, humedad suelo, helada) | 0,5 h | Texto en pantalla de resultado + tooltips funcionales |

### Fase 5 — Demo y pitch (cierre día 2, 3 h)
| ID | Tarea | Est. | Criterio de aceptación |
|---|---|---|---|
| 5.1 | Demo: onboarding (GPS + prioridad) → Hoy → Sembrar → fecha óptima → **Rotaciones (3 planes con 5 campos)** → alerta + mapa GAMC | 1 h | Flujo sin errores en vivo; rotaciones visibles con evidencia |
| 5.2 | Pitch alineado al reto: NASA (POWER/SMAP/GPM/GEOS) + **GAMC (zonas, presión urbana, drenaje)** + **ET₀ + humedad suelo** + rotaciones (≥3 con 5 campos) + **armonización de datasets** + incertidumbre + **apoyo-no-reemplazo** + **prioridades del agricultor** | 1 h | Guion 5 min que cubre todos los puntos del reto |
| 5.3 | Video 3–5 min | 1 h | Grabado |

## 7. Cortes de MVP (si falta tiempo, en orden de descarte)

1. **Móvil → PWA web** (si el nativo no cierra a tiempo; el scoring local funciona igual).
2. **Eventos/alertas → 1 regla + 5 eventos** (helada o lluvia).
3. **Rotaciones → tabla estática** de 3 estrategias con los 5 campos (sin scoring dinámico por objetivo).
4. **Zonas → 5 comunas** en vez de 12 (Itocta, Molle, A. Zamudio, Tiquipaya, Valle Hermoso).
5. **SMAP → descartar** (quedan POWER + GPM; humedad de suelo se menciona como "próximamente").
6. **GEOS 28 d → descartar** (solo modelo estacional 365 d; sin pronóstico corto).
7. **Landsat/Sentinel-2 → descartar** (sin NDVI; bare fields se infiere del calendario de cultivos).
8. **SRTM → descartar** (pendiente/erosión se toma de la capa drenaje GAMC).
9. **GPM → solo POWER** (una sola fuente de clima).
10. **Reportes comunitarios → descartar** (sin mapa de zona colaborativo).
11. **La Angostura → descartar** (sin nivel de represa; agua solo por lluvia/SMAP).

## 8. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Claves de acceso (CDS/Earthdata) | Bajo | **POWER sin token** ✅ y **token Earthdata verificado en vivo** ✅ (CMR + descarga SMAP). Queda CDS (ERA5) opcional |
| SMAP 9 km grueso + tamaño de granules (~1,3 GB/día) | Medio | Brecha 2026-05/07 ya cubierta ✅; tratar como "valle" no comunal; histórico completo no viable → ventana reducida o P1 descartable |
| EULA GPM/IMERG no aceptado (403) | ~~Bajo~~ **RESUELTO** ✅ | EULA aceptado 14/11/2026. Descarga IMERG desbloqueada |
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

## 10. Alineación con el reto (auditoría 14/11)

> Verificación contra el enunciado oficial: <https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/>

| Requisito del reto | Dónde lo cubrimos | Estado |
|---|---|---|
| **Decision-support tool** (app/modelo/mapa) | App móvil offline-first + API + modelo estacional | ✅ |
| **Datos NASA + info local** (suelos, cultivos, prioridades) | POWER + SMAP + GPM + SRTM + GEOS + **GAMC** + `crops.json` + La Angostura | ✅ |
| **≥3 rotaciones incl. la actual** con 5 campos | Tarea 2.6 + API-CONTRACT §6 (`por_que`, `evidencia[]`, `bueno[]`, `riesgos[]`, `falta_saber[]`) | ✅ |
| **Apoya, no reemplaza** | Tarea 4.7 (texto + tooltips) | ✅ |
| T, lluvia, **humedad suelo**, **evaporación (ET₀)**, heladas, precip. extrema | POWER (T, pmm, RH, SW) + SMAP (sm) + **ET₀ Hargreaves** (tarea 2.2) | ✅ |
| Prioridades: agua, forraje, fixN, erosión, materia orgánica, mercado | `crops.json` + scoring 4 dimensiones (API-CONTRACT §6) | ✅ |
| Bare fields / campo desnudo | `meses_sin_cultivo` en rotaciones + calendario de cultivos | ✅ |
| Pest cycle disruption | `breaks_pest_cycle` en crops + `riesgos: ["mas_gusano"]` en rotaciones | ✅ |
| **Farmer input: prioridades/restricciones** | Onboarding: `PUT /perfil` con `prioridad` (API-CONTRACT §1) | ✅ |
| Incertidumbre + validación local | Banda de incertidumbre + backtest + `confianza` por respuesta | ✅ |
| Armonización de datasets (explicar) | Nota §3 (malla 1 km / 30 m) + pitch | ✅ |
| Mapas interactivos (tendencias, vulnerabilidades) | GAMC WMS en app + capa drenaje + heladas por zona | ✅ |
| Explicar términos científicos | Tooltips en UI (tarea 4.7): ET, humedad suelo, helada | ✅ |
| Cultivos fixN, cobertura, raíz profunda, tolerantes a sequía | `crops.json`: `fix_n`, `deep_rooting`, `drought_tolerant`, `forage_value` | ✅ |

**Datasets NASA no usados** (opcionales, "you may explore"): ECOSTRESS, Landsat/MODIS/VIIRS, GRACE/GRACE-FO, GEDI.
No bloquean; se mencionan como "próximamente" si el jurado pregunta.

## 11. Referencias

- Reto oficial: <https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/> · [CHALLENGE.md](./CHALLENGE.md)
- **API Contract (equipo app):** [API-CONTRACT.md](./API-CONTRACT.md) · **Flujo de app:** [FLUJO-APP.md](./FLUJO-APP.md)
- SMAP v8: <https://nsidc.org/data/spl4smgp/versions/8> (DOI 10.5067/T5RUATAQREF8)
- POWER API: <https://power.larc.nasa.gov/api/documents/>
- Series temporales (ref. equipo): <https://www.ibm.com/mx-es/think/topics/time-series-model>
- Cultivos y condiciones óptimas: [CROPS.md](./CROPS.md) · Contexto local: [LOCAL-CONTEXT.md](./LOCAL-CONTEXT.md)
- Acceso GAMC (live): [GAMC-ACCESS.md](./GAMC-ACCESS.md) · Datos descargados: [data/gamc/04/](../data/gamc/04/README.md)
- Mockup: Figma "Field Shift — App Agricultor (mobile)"
