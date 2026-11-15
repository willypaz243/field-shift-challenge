# Fuentes de datos — Field Shift: Adapting Farms with NASA Data

> Reto: [spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/)
> Registro local de los recursos GAMC: [`docs/recursosgamc/`](../../docs/recursosgamc/README.md)
> Área de análisis local (GAMC): **valle de Cochabamba, Bolivia** — bbox aprox. `-66.28, -17.53, -66.05, -17.26` (WGS84).

---

## 1. Datos NASA (núcleo del reto)

### Portal de búsqueda general
| Recurso | Enlace | Uso |
|---|---|---|
| NASA Earthdata Search (búsqueda/descarga) | <https://search.earthdata.nasa.gov/> | Descarga de casi todos los productos NASA |
| NASA Earthdata portal (documentación) | <https://www.earthdata.nasa.gov/> | Docs de plataformas e instrumentos |
| NASA Worldview (visualización rápida) | <https://worldview.earthdata.nasa.gov/> | Explorar capas; IMERG descargable como imagen |

### Misiones recomendadas por el enunciado
| Dataset | Enlace de acceso | Qué aporta al reto |
|---|---|---|
| **SMAP** (humedad de suelo, 3-h) | L4: <https://nsidc.org/data/spl4smgp/versions/8> (DOI 10.5067/T5RUATAQREF8) · CMR: `C3480440870-NSIDC_CPRD` | Humedad de superficie + zona radicular — **verificado 14/11: token Earthdata funciona (CMR + descarga directa ~148 MB/granule); brecha 14/05–28/07/2026 ya cubierta** |
| **GPM / IMERG** (precipitación) | IMERG diario: <https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary> · CMR: `C2723754859-GES_DISC` (diario) / `C2723754847-GES_DISC` (30-min) | Fiabilidad de lluvia, tormentas extremas, riesgo de erosión — ⚠️ **exige aceptar EULA una vez**: <https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ> |
| **Landsat 8/9** (30 m) | <https://earthexplorer.usgs.gov/> · <https://landsatlook.usgs.gov/> | NDVI, vigor vegetal, suelo desnudo, transiciones estacionales |
| **MODIS** (250–1000 m) | <https://lpdaac.usgs.gov/products/> (ej. MOD13Q1 NDVI: <https://lpdaac.usgs.gov/products/mod13q1v061/>) | NDVI/estrés vegetal a mayor frecuencia |
| **VIIRS** | <https://search.earthdata.nasa.gov/search?q=VIIRS> | Índices de vegetación alternativos a MODIS |
| **NASA POWER** (agroclimatología) | <https://power.larc.nasa.gov/> · API: `https://power.larc.nasa.gov/api/temporal/daily/point` | Temp, radiación, humedad, precipitación, viento — **verificado 14/11: funciona SIN token** (v2.10.3). `start`/`end` = int `YYYYMMDD` (desde 1984). `community=ag`. Parámetros válidos diario: `T2M, T2MDEW, RH2M, WS2M, PS, PRECTOT, TS, ALLSKY_SFC_SW_DWN, ALLSKY_SFC_LW_DWN, CLRSKY_SFC_SW_DWN`. **Sin T2MIN/T2MAX en diario** → derivar de `temporal/hourly/point?parameters=T2M` (verificado) o tomar de ERA5 |
| **SRTM** (elevación 30 m) | <https://www.earthdata.nasa.gov/data/instruments/srtm> · descarga: <https://dwtkns.com/srtm30m/> | Pendiente, escorrentía, riesgo de erosión, flujo de agua |
| **ECOSTRESS** (LST y ET, alta resolución) | <https://ecostress.jpl.nasa.gov/data> | Hotspots de estrés térmico/hídrico, microclima de campo |
| **GRACE / GRACE-FO** (almacenamiento de agua) | <https://gracefo.jpl.nasa.gov/data/> | Tendencias de agua a largo plazo |
| **GEDI** (biomasa, dosel) | <https://gedi.umd.edu/data/> · L4A: <https://daac.ornl.gov/CMS/guides/CMS_GEDI_FTP.html> | Contexto de vegetación/biomasa del paisaje |

> Para Cochabamba (nubes frecuentes en temporada húmeda): combinar **NASA POWER** (solo puntos, sin huecos) + **GPM** (lluvia) + **MODIS/VIIRS** (frecuencia) como base, y Landsat/Sentinel-2 cuando el cielo esté despejado.

---

## 2. Datasets complementarios

### Agronómicos / suelos
| Recurso | Enlace | Uso |
|---|---|---|
| FAO **GAEZ** (idoneidad agroclimática global) | <https://gaez.fao.org/> | Aptitud climática/suelo por cultivo — clave para rotaciones fuera de EE.UU. |
| **SoilGrids** (ISRIC, suelos global 250 m) | <https://soilgrids.org/> · API: <https://isric.org/explore-soil-grids/api-documentation> | Textura, materia orgánica, pH, drenaje en Cochabamba (SSURGO es solo EE.UU.) |
| **Harmonized World Soil Database v2** | <https://essd.copernicus.org/articles/16/563/2024/> | Alternativa global de propiedades de suelo |
| USDA Ag Data Commons | <https://www.nal.usda.gov/services/agdatacommons> | Contexto agronómico abierto |
| USDA Web Soil Survey / SSURGO / STATSGO2 | <https://websoilsurvey.nrcs.usda.gov/app/> · <https://www.nrcs.usda.gov/resources/data-and-reports/soils> | Suelos oficiales (solo EE.UU., útil para prototipar) |
| Cropland Data Layer (CropScape) | <https://nassgeodata.gmu.edu/CropScape/> | Clasificación de cultivos 30 m (solo EE.UU.) |
| USDA NASS QuickStats | <https://quickstats.nass.usda.gov/> | Estadísticas de rendimientos/superficie (EE.UU.) |
| USDA AMS Market News | <https://www.ams.usda.gov/market-news> | Precios y demanda de commodities |

### Clima / agua / validación
| Recurso | Enlace | Uso |
|---|---|---|
| **ERA5** (ECMWF, reanálisis horario global) | <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview> | Series temporales continuas donde no hay estaciones |
| Copernicus **Sentinel-2** (10–20 m) | <https://dataspace.copernicus.eu/> | NDVI/EVI, bare-soil, estrés a nivel de campo (cubre Cochabamba) |
| OpenET (ET a escala de campo) | <https://openetdata.org/> | Evapotranspiración (solo oeste de EE.UU.) |
| PRISM Climate (EE.UU.) | <https://prism.oregonstate.edu/> | Normales climáticas de 30 años (EE.UU.) |
| NLDAS / GLDAS | <https://search.earthdata.nasa.gov/search?q=GLDAS> | Series de humedad/ET continuas (global GLDAS) |
| USGS NWIS (agua) | <https://waterdata.usgs.gov/nwis> | Niveles/caudales (EE.UU.) |
| CoCoRaHS (lluvia comunitaria) | <https://www.cocorahs.org/Maps> | Validación de IMERG (Norteamérica) |
| USFS LANDFIRE | <https://www.landfire.gov/> | Vegetación/paisaje (EE.UU.) |

---

## 3. Recursos GAMC — Gobierno Autónomo Municipal de Cochabamba

Portal oficial de servicios geoespaciales municipales asignados a los retos Space Apps:

| Recurso | Enlace |
|---|---|
| **Portal GAMC (inicio)** | <https://recursosgamc.cochabamba.bo/> |
| **API Doc (catálogo de servicios)** | <https://recursosgamc.cochabamba.bo/api-doc> |
| **Endpoint del proxy WMS** | `https://serviciosgamc.cochabamba.bo/api/gs/wms` |

- Protocolo: **WMS 1.1.1** (GetMap · GetLegendGraphic · GetFeatureInfo) — acceso solo lectura.
- **API key del proyecto 04** (Agrotecnología y Gestión del Agua): va en `.env` como `GAMC_API_KEY` (ver `.env.example`; pedirla al equipo).

### Capas del proyecto 04 (cobre del valle de Cochabamba)

| # | Capa | Service ID (UUID) | Tipo | BBOX WGS84 |
|---|---|---|---|---|
| 1 | **Periurbanos** | `c52066a1-32fd-4925-81e0-c2dcb8f4238f` | Categorizado | `-66.275711, -17.525117, -66.072201, -17.326109` |
| 2 | **Drenaje e Influencia** | `d4cea6e3-fc7f-482a-94ad-bd377df78886` | Simple | `-66.269936, -17.530591, -66.045853, -17.260142` |
| 3 | **Límite Distritos** | `7eb13092-bf0e-493b-aae6-03c43eedda2c` | Simple | `-66.280703, -17.53119, -66.06952, -17.257306` |

### Ejemplo de petición GetMap

```
https://serviciosgamc.cochabamba.bo/api/gs/wms
  ?key=$GAMC_API_KEY
  &service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f
  &REQUEST=GetMap
  &SERVICE=WMS
  &VERSION=1.1.1
  &LAYERS=
  &SRS=EPSG:4326
  &BBOX=-66.275711,-17.525117,-66.072201,-17.326109
  &WIDTH=256&HEIGHT=256
  &FORMAT=image/png
  &TRANSPARENT=true
```

Notas: `LAYERS` se envía vacío (el proxy resuelve la capa desde `service_id`); sin STYLES ni filtros custom. GetLegendGraphic usa `VERSION=1.0.0` y no requiere BBOX. GetFeatureInfo devuelve `application/json`.

- Documentación local completa: [`docs/recursosgamc/04-adapting-farms-with-nasa-data.md`](../../docs/recursosgamc/04-adapting-farms-with-nasa-data.md) y [`docs/recursosgamc/guia-integracion.md`](../../docs/recursosgamc/guia-integracion.md).

---

## 4. Cómo se combinan en el producto

- **GAMC WMS** → contexto territorial local: distritos, zonas periurbanas agrícolas, drenaje/cuencas del valle de Cochabamba (mapas base y consulta por punto).
- **NASA POWER + SMAP + GPM + MODIS/VIIRS + SRTM + ECOSTRESS** → indicadores ambientales del reto: estrés hídrico, heladas, erosión, ET, NDVI, bare-field.
- **SoilGrids + FAO GAEZ** → suelos y aptitud de cultivos en Bolivia (los datasets USDA son solo EE.UU.).
- Todo armonizado en una **malla común de análisis** (recomendado por el enunciado) sobre el bbox GAMC.
