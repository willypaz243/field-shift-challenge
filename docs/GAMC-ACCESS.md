# Acceso a datos GAMC — análisis exploratorio en vivo

> Sondeo realizado el **14/11/2026** contra el endpoint real del proxy municipal.
> Catálogo oficial (claves, UUIDs, guía del portal): ver [`docs/recursosgamc/`](../../docs/recursosgamc/)
> y las claves en [`DATA-SOURCES.md`](./DATA-SOURCES.md).
> **Contexto de uso:** app "Turnos del Valle" (reto 04 Field Shift).

---

## 1. Resumen ejecutivo

| Hallazgo | Veredicto |
|---|---|
| Endpoint del proxy | `https://serviciosgamc.cochabamba.bo/api/gs/wms` — **WMS 1.1.1 real de GeoServer** detrás de un proxy con API key |
| Autenticación | Por query param `key` **o** cabecera HTTP `X-Api-Key` (ambas funcionan) |
| Autorización | **Estricta por `service_id`**: la key solo abre los UUID de su catálogo (403 si no) |
| Parámetro `LAYERS` | **Completamente ignorado por el proxy** (vacío, con nombre, o basura → misma imagen, idéntico md5). La capa la decide el `service_id` |
| `GetCapabilities` | ✅ **Funciona y atraviesa el proxy** → expone el inventario completo del GeoServer (15 capas reales del GAMC + 3 capas demo), incluidas capas NO autorizadas para la key |
| `GetFeatureInfo` | ✅ JSON GeoJSON. Verificado con atributos reales en Periurbanos y Limite Distritos. En Drenaje devuelve vacío en **12 puntos** (4 faldeos + eje Rocha + centro del valle) → probable que no esté habilitado para esa capa |
| Datos descargados | ✅ Leyendas, mapas y featureinfo de las 3 capas guardados en [`data/gamc/04/`](../data/gamc/04/README.md) |
| Rate limit | **Existe y es agresivo** (HTTP 429 global). Con ráfagas de 8 requests seguidos todos fallan; separando ~10–15 s pasan normal |
| Backend directo | `serviciosgamcgeo.cochabamba.bo/geoserver/app/wms` **no accesible** (TLS "unrecognized name" → servidor interno, solo vía proxy) |
| Formatos | `image/png`, `image/png8` y `image/jpeg` funcionan en GetMap |
| SRS | `EPSG:3857` y `EPSG:4326` ambos funcionan en GetMap |

---

## 2. Autenticación y errores (verificados)

Ejemplos reales de respuesta del proxy:

| Caso | HTTP | Cuerpo |
|---|---|---|
| Sin key | `401` | `{"error":"Falta la API key (parámetro key o cabecera X-Api-Key)."}` |
| Key inválida/revocada | `401` | `{"error":"API key inválida o revocada."}` |
| Key válida + `service_id` de otro proyecto | `403` | `{"error":"La API key no tiene acceso a este servicio."}` |
| Sin `service_id` | `400` | `{"error":"Falta service_id."}` |
| Demasiadas solicitudes | `429` | `{"error":"Demasiadas solicitudes. Inténtalo de nuevo en unos minutos."}` |

**Dos formas de autenticar** (las dos comprobadas con HTTP 200):

```text
# Query param
https://serviciosgamc.cochabamba.bo/api/gs/wms?key={KEY}&service_id={UUID}&...

# Cabecera (mejor: la key no queda en la URL ni en logs de tiles)
X-Api-Key: {KEY}
```

> ⚠️ La cabecera `X-Api-Key` es preferible para la app: en Leaflet las URLs de teselas con la key
> acaban visibles en el código fuente del navegador.

---

## 3. Reglas del proxy (comportamiento medido)

1. **`service_id` manda.** El proxy valida la key contra su catálogo y **resuelve internamente qué
   capa real de GeoServer corresponde al UUID**. Enviarlo vacío o falso → error o capa equivocada.
2. **`LAYERS` se descarta.** Test decisivo: 4 GetMap idénticos (mismo BBOX/tamaño) con
   `LAYERS=""`, `LAYERS=areas_verdes`, `LAYERS=centros_de_salud`, `LAYERS=capa_inexistente_xyz`
   → **las 4 imágenes son byte-idénticas** (md5 `9302da47fb`, 48.5 KB). En GetFeatureInfo pasa lo mismo
   (con `LAYERS=poblacion_por_mazanas` devolvió el dato de Periurbanos del `service_id`).
3. **Estilos y filtros del servidor.** No se puede pedir `STYLES`/CQL alternativos; el proxy
   inyecta el estilo propio (`svc_<capa>`).
4. **GetCapabilities es la excepción**: pasa sin filtrar al GeoServer y **no requiere capas
   autorizadas** — devolvió el XML completo (221 KB) con la key del proyecto 04.
5. **Rate limit global por IP.** Una ráfaga corta (8 requests) agota la cuota → 429 en todo,
   incluso sin key. Con pausas de ~10–15 s funciona sin problemas. La ventana parece de ~1 minuto.

---

## 4. Operaciones verificadas (con parámetros exactos)

### GetMap ✅

```text
GET https://serviciosgamc.cochabamba.bo/api/gs/wms
    key={KEY} & service_id={UUID}
    SERVICE=WMS & VERSION=1.1.1 & REQUEST=GetMap
    LAYERS=                        (vacío, obligatorio pero ignorado)
    FORMAT=image/png | image/png8 | image/jpeg
    TRANSPARENT=true|false
    SRS=EPSG:3857 | EPSG:4326
    BBOX=minX,minY,maxX,maxY       (metros 3857 o grados 4326)
    WIDTH=n & HEIGHT=n             (256/512/800/1024 probados OK)
```

- `VERSION=1.3.0` **también funciona** (el proxy no lo bloquea), aunque la guía dice 1.1.1.
- Las teselas del visor oficial son 256×256 en EPSG:3857.

### GetLegendGraphic ✅

```text
GET ...?key={KEY}&service_id={UUID}&REQUEST=GetLegendGraphic
    VERSION=1.0.0 (guía) — 1.1.1 también aceptado
    FORMAT=image/png
```

- Capa *Categorizada* (Periurbanos): leyenda de 1.360 B con las clases.
- Capa *Simple* (Drenaje): leyenda de 183 B (un solo símbolo).

### GetFeatureInfo ✅ (con matices)

```text
GET ...?key={KEY}&service_id={UUID}&REQUEST=GetFeatureInfo
    SERVICE=WMS & VERSION=1.1.1
    SRS=EPSG:3857 & BBOX=... & WIDTH=n & HEIGHT=n
    X=px & Y=px                    (píxel dentro de la imagen del BBOX)
    INFO_FORMAT=application/json & FEATURE_COUNT=5
```

Respuesta: **GeoJSON `FeatureCollection`**; si no hay elemento bajo el píxel → `features: []`.

### GetCapabilities ✅ (sin filtrar)

```text
GET ...?key={KEY}&service_id={UUID}&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities
```

---

## 5. Inventario completo del GeoServer (vía GetCapabilities)

El XML filtrado lista **15 capas reales del GAMC** (workspace `app`) + 3 capas demo de GeoServer
(`spearfish`, `tasmania`, `tiger-ny`). BBOX geográficos reales (WGS84):

| Capa | Tipo (portal) | BBOX WGS84 (minLon, minLat, maxLon, maxLat) | En catálogo de… |
|---|---|---|---|
| `periurbanos` | Categorizado | −66.2757, −17.5251, −66.0722, −17.3261 | p04 ✅ |
| `drenaje_e_influencia` | Simple | −66.2699, −17.5306, −66.0459, −17.2601 | p04 ✅ |
| `limite_distritos` | Simple | −66.2807, −17.5312, −66.0695, −17.2573 | p04 ✅ |
| `limite_cercado` | Simple | −66.2807, −17.5312, −66.0695, −17.2573 | — (p02?) |
| `limite_urbano` | Simple | −66.2514, −17.5085, −66.0842, −17.3328 | p05 |
| `cota_2750` | — | −66.1938, −17.3671, −66.1039, −17.2573 | p02 |
| `emergencias` | — | −66.2047, −17.4569, −66.1245, −17.3500 | p02 |
| `cuencas_de_influencia` | — | −66.2782, −17.5312, −66.0648, −17.2466 | p02 |
| `cuencas_principales` | — | −66.5364, −17.8700, −65.5746, −17.2312 | p02 |
| `cuencas_uh_8` | — | −66.4336, −17.6779, −65.8441, −17.1869 | p02 |
| `areas_verdes` | — | −66.2493, −17.5029, −66.0855, −17.3358 | p05 |
| `areas_de_equipamiento` | — | −66.2528, −17.5053, −66.0844, −17.2716 | p05 |
| `centros_de_salud` | — | −66.2190, −17.4916, −66.1055, −17.3461 | p05 |
| `poblacion_por_mazanas` | — | −66.2636, −17.5157, −66.0726, −17.3257 | p05 |
| `unidades_educativas` | — | −66.2239, −17.4949, −66.1009, −17.3430 | p05 |

> Cada capa tiene además un estilo `svc_<nombre>` (el proxy lo inyecta él mismo).
> XML completo guardado en `/tmp/opencode/gamc_capabilities.xml` durante la sesión de sondeo.

**Interpretación:** el catálogo autorizado por key sigue mandando (403 verificado), pero el
GetCapabilities revela **qué existe en total** — útil para pedir al GAMC ampliar el catálogo
de la key 04, o para usar keys de otros proyectos si el equipo consigue más de una.

---

## 6. Esquema de atributos obtenidos por GetFeatureInfo

| Capa | Atributos observados | Ejemplo |
|---|---|---|
| `periurbanos` | `Detalle`, `Periurbano` | `{"Detalle":"Periurbano","Periurbano":"Periurbanos consolidados"}` y `{"Detalle":"Herbazales ralos con intervenión urbana","Periurbano":"Periurbanos en crecimiento"}` |
| `limite_distritos` | `Distrito`, `Comuna` | `{"Distrito":"D4","Comuna":"MOLLE"}`, `{"Distrito":"D12","Comuna":"ADELA ZAMUDIO"}`, `{"Distrito":"D9","Comuna":"ITOCTA"}` |
| `drenaje_e_influencia` | ⚠️ vacío en **12 puntos** probados (centro del valle, eje Rocha, 4 faldeos) | `features: []` — probable que el FeatureInfo no esté habilitado para esa capa. Usar como contexto visual; confirmar con GAMC |

Comunas confirmadas en vivo: **D4 = MOLLE**, **D12 = ADELA ZAMUDIO**, **D9 = ITOCTA** (además
Itocta, Tunari, Valle Hermoso, Tamborada del sondeo previo en LOCAL-CONTEXT.md).

---

## 7. Archivos descargables del portal

| URL | Contenido | Estado |
|---|---|---|
| `https://recursosgamc.cochabamba.bo/assets/geo/red_monica.zip` | 2 CSV sin autenticación: `red_monica.kanata (1).csv` (54.712 filas) y `red_monica.semapa (1).csv` (71.155 filas), columnas `estacion,pm10,fecha_medicion` (mediciones PM10 desde 2022, cada 30 min) | ✅ HTTP 200, `application/zip` |
| `https://recursosgamc.cochabamba.bo/assets/geo/lineas_de_transporte.rar` | RAR de transporte | no probado hoy |

> Las series MÓNICA (Kanata + SEMAPA) son del proyecto 01, pero sirven de contexto de calidad
> del aire si el pitch lo menciona. Son CSV simples, fácilmente parseables.

---

## 8. Implicaciones para "Turnos del Valle" (reto 04)

1. **Carga de capas:** usar `L.tileLayer.wms` con la key del proyecto 04 y los 3 UUID del catálogo.
   `LAYERS` vacío; `version: '1.1.1'`; `format: 'image/png'; transparent: true`.
2. **Click en el mapa:** implementar GetFeatureInfo manual (el plugin WMS de Leaflet no lo maneja
   con este proxy): al hacer click, pedir un BBOX pequeño (±200 m) centrado en el punto con
   `X=W/2, Y=H/2` y parsear el GeoJSON → mostrar «Periurbanos consolidados / en crecimiento»,
   «Distrito D4 · Comuna MOLLE».
3. **Leyendas:** descargar GetLegendGraphic de las 2 capas visibles y montar un panel propio.
4. **Rate limit:** el visor genera 1–9 teselas por movimiento de mapa. Recomendaciones:
   - caché de teselas en el navegador (los PNG son estáticos y no cambian durante el hackathon);
   - limitar zoom (las capas cubren solo el valle: maxBounds del mapa al BBOX −66.28…−17.53…);
   - si salta 429, reintentar con backoff de 20–30 s (el error dice literalmente «en unos minutos»).
   - No precargar teselas de capas ocultas.
5. **FeatureInfo de Drenaje:** si no responde, el dato «¿estoy cerca de una quebrada?» puede
   resolverse dibujando la capa y calculando distancia a la imagen... o pidiendo al GAMC que
   habilite el servicio. Para el MVP: mostrar la capa como contexto visual y sancionar cultivos
   erosionables (papa en faldeos) solo con SRTM/pendiente.
6. **Claves:** usar `X-Api-Key` en producción de la demo, y pedir al GAMC restricción por dominio
   si se va a exponer (la guía lo ofrece).

---

## 9. Comandos de reproducción

```bash
# GetMap de Periurbanos (tesela 256px, Web Mercator)
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=$KEY04" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "SERVICE=WMS" --data-urlencode "VERSION=1.1.1" \
  --data-urlencode "REQUEST=GetMap" --data-urlencode "LAYERS=" \
  --data-urlencode "FORMAT=image/png" --data-urlencode "TRANSPARENT=true" \
  --data-urlencode "SRS=EPSG:3857" \
  --data-urlencode "BBOX=-7373000,-1970000,-7355000,-1952000" \
  --data-urlencode "WIDTH=512" --data-urlencode "HEIGHT=512" -o periurbanos.png

# Leyenda de Periurbanos
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=$KEY04" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "REQUEST=GetLegendGraphic" \
  --data-urlencode "VERSION=1.0.0" --data-urlencode "FORMAT=image/png" -o leyenda.png

# GetFeatureInfo (X/Y en píxeles del BBOX pedido)
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=$KEY04" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "SERVICE=WMS" --data-urlencode "VERSION=1.1.1" \
  --data-urlencode "REQUEST=GetFeatureInfo" \
  --data-urlencode "SRS=EPSG:3857" \
  --data-urlencode "BBOX=-7364484,-1966971,-7364084,-1966571" \
  --data-urlencode "WIDTH=256" --data-urlencode "HEIGHT=256" \
  --data-urlencode "X=128" --data-urlencode "Y=128" \
  --data-urlencode "INFO_FORMAT=application/json" \
  --data-urlencode "FEATURE_COUNT=5"

# GetCapabilities (inventario completo del GeoServer)
curl -G "https://serviciosgamc.cochabamba.bo/api/gs/wms" \
  --data-urlencode "key=$KEY04" \
  --data-urlencode "service_id=c52066a1-32fd-4925-81e0-c2dcb8f4238f" \
  --data-urlencode "SERVICE=WMS" --data-urlencode "VERSION=1.1.1" \
  --data-urlencode "REQUEST=GetCapabilities" -o capabilities.xml
```

---

## 10. Pendientes / limitaciones

- [ ] GetFeatureInfo de `drenaje_e_influencia` — 12 puntos probados (todas las zonas: centro,
  eje Rocha, faldeos) → todos vacíos. Probablemente no está habilitado para esa capa;
  confirmar con GAMC. MVP: capa solo como contexto visual.
- [x] Descarga de leyendas/mapas/featureinfo de las 3 capas → [`data/gamc/04/`](../data/gamc/04/README.md) (14/11).
- [ ] No hay endpoint de descarga vectorial (GeoJSON/WFS) en el catálogo: los datos llegan solo
  como PNG renderizado + FeatureInfo puntual. Si se necesitan geometrías (p. ej. para calcular
  distancias a quebradas), hay que digitalizar o pedir WFS al GAMC.
- [ ] Ventana exacta del rate limit (medido: ráfaga de 8 → 429; pausas 10–15 s → OK).
- [ ] `lineas_de_transporte.rar` sin probar (requiere unrar).
