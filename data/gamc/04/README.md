# Datos GAMC — Proyecto 04 (Field Shift) descargados de la API WMS

> Descargados el **14/11/2026** (API recuperada; había estado en 502 del 11/11 al 13/11).
> Endpoint: `https://serviciosgamc.cochabamba.bo/api/gs/wms` · WMS 1.1.1 · key proyecto 04.
> Análisis completo del acceso: [`docs/GAMC-ACCESS.md`](../../../docs/GAMC-ACCESS.md)

## Contenido

```
04/
├── README.md
├── leyendas/          ← GetLegendGraphic (VERSION=1.0.0)
│   ├── periurbanos.png
│   ├── drenaje_e_influencia.png
│   └── limite_distritos.png
├── mapas/             ← GetMap 800×512, EPSG:4326, BBOX −66.2807,−17.5312,−66.0459,−17.2573
│   ├── periurbanos.png
│   ├── drenaje_e_influencia.png
│   └── limite_distritos.png
└── featureinfo/       ← GetFeatureInfo (JSON), BBOX ~1,2 km centrado, X=Y=128
    ├── periurbanos_centro.json   (−66.1700, −17.3900)
    ├── periurbanos_oeste.json    (−66.2300, −17.4300)
    ├── distritos_centro.json
    ├── distritos_oeste.json
    ├── drenaje_rocha_1.json
    ├── drenaje_rocha_2.json
    ├── drenaje_faldeo_1.json
    └── drenaje_faldeo_2.json
```

## Capas

### 1. Periurbanos (`c52066a1-32fd-4925-81e0-c2dcb8f4238f`) — Categorizado

Leyenda (3 clases):

| Color | Clase |
|---|---|
| Verde | **Periurbanos en crecimiento** |
| Naranja | **Periurbanos consolidados** |
| Gris | **otros** |

Mapa: franja de expansión urbana sobre el fondo del valle (naranja dominante al este/centro,
verde en frentes de crecimiento).

Atributos por `GetFeatureInfo` (`Detalle`, `Periurbano`):

| Punto | Respuesta |
|---|---|
| −66.1700, −17.3900 (centro del valle) | `features: []` (no es periurbano) |
| −66.2300, −17.4300 (oeste) | `{"Detalle":"Herbazales ralos con intervenión urbana","Periurbano":"Periurbanos en crecimiento"}` |

> Útil para el reto: delimitar el frente de expansión urbana sobre tierras agrícolas
> (presión urbanística = variable de "shift" de uso de suelo).

### 2. Drenaje e Influencia (`d4cea6e3-fc7f-482a-94ad-bd377df78886`) — Simple

Mapa: red de quebradas/cauces (líneas azules) en faldeos y fondo de valle, con polígonos
de "zona de influencia" alrededor de los cauces principales.

`GetFeatureInfo`: **vacío en los 12 puntos probados** (4 nuevos el 14/11 + 8 de la sesión
anterior: centro del valle, eje Rocha, faldeos). Probablemente el FeatureInfo no está
habilitado para esta capa en el GeoServer, o los buffers no cubren los puntos. → Usar la
capa **solo como contexto visual** en el MVP; confirmar con GAMC.

### 3. Límite Distritos (`7eb13092-bf0e-493b-aae6-03c43eedda2c`) — Simple

Mapa: polígono del área municipal (estilo único, púrpura).

Atributos por `GetFeatureInfo` (`Distrito`, `Comuna`):

| Punto | Respuesta |
|---|---|
| −66.1700, −17.3900 | `{"Distrito":"D12","Comuna":"ADELA ZAMUDIO"}` |
| −66.2300, −17.4300 | `{"Distrito":"D9","Comuna":"ITOCTA"}` |

> Útil para el reto: segmentar el valle por distrito/comuna y asociar recomendaciones
> agrícolas a jurisdicción municipal.

## Cómo regenerar

```bash
# Leyenda (capa periurbanos; cambiar service_id para las otras)
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=37f574a3292eafd287024269399aafa51b7cf55932603e2f" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "REQUEST=GetLegendGraphic" --data-urlencode "VERSION=1.0.0" \
  --data-urlencode "FORMAT=image/png" -o leyenda.png

# Mapa
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=37f574a3292eafd287024269399aafa51b7cf55932603e2f" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "SERVICE=WMS" --data-urlencode "VERSION=1.1.1" --data-urlencode "REQUEST=GetMap" \
  --data-urlencode "LAYERS=" --data-urlencode "FORMAT=image/png" --data-urlencode "TRANSPARENT=true" \
  --data-urlencode "SRS=EPSG:4326" \
  --data-urlencode "BBOX=-66.280703,-17.531190,-66.045853,-17.257306" \
  --data-urlencode "WIDTH=800" --data-urlencode "HEIGHT=512" -o mapa.png
```

> ⚠️ **Rate limit**: máximo ~1 petición cada 10–15 s (ráfagas de 8 → HTTP 429 global).
> Script de descarga completo (con pausas): `/tmp/opencode/gamc_dl_04.sh` (sesión 14/11).
> Para los 5 proyectos completos: [`data/recursosgamc/descargar_api.sh`](../../../data/recursosgamc/descargar_api.sh).
