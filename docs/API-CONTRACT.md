# Choclito — Contrato de API (para el equipo de datos)

Versión del contrato: **v1 (borrador)** · Fecha: 2026-11-14

Este documento dice **qué datos necesita la app y en qué forma**. El equipo de datos produce estos datos desde NASA y fuentes locales; el equipo de la app los consume. Cada endpoint indica de qué pantalla sale y qué fuentes sugerimos.

Flujo de la app: [`FLUJO-APP.md`](FLUJO-APP.md) · Fuentes: [`DATA-SOURCES.md`](DATA-SOURCES.md) · Contexto: [`CONTEXTO-LOCAL.md`](CONTEXTO-LOCAL.md)

---

## 0. Reglas generales

| Tema | Regla |
|---|---|
| Base | `https://api.choclito.example/v1` (dominio por definir) |
| Formato | JSON UTF-8. Nombres de campo en `snake_case` y en español. |
| Fechas | ISO 8601. Fechas sin hora: `2026-11-16`. Con hora: `2026-11-16T06:00:00-04:00`. Zona horaria **America/La_Paz (UTC−4)**. |
| Coordenadas | WGS84, grados decimales, 5 decimales como máximo. GeoJSON para geometrías. |
| Unidades | Temperatura °C · lluvia mm · humedad del suelo m³/m³ · nivel de represa % · distancias m. |
| Textos | La API devuelve **códigos**, no frases. La app traduce a español y quechua. Ej.: `"tipo": "helada"`, no `"¡Cuidado con la helada!"`. |
| Fuente | Todo dato derivado lleva `fuente` (lista de códigos, ver §10). |
| Frescura | Toda respuesta lleva `actualizado_en`. La app muestra "actualizado 16 nov, 6:00". |
| Confianza | Pronósticos y recomendaciones llevan `confianza`: `alta` · `media` · `baja`. |
| Caché | `ETag` y `Cache-Control: max-age`. La app funciona sin señal con la última respuesta. |
| Peso | Celulares baratos y pocos datos: respuestas **< 50 KB** (gzip). Sin imágenes en JSON. |
| Errores | Ver §9. |
| Privacidad | Los reportes van al mapa **sin nombre**. Nunca devolver datos personales de otros agricultores. |

---

## 1. Parcela y perfil

### `GET /parcelas/cercanas?lat=&lon=`
Pantalla: **Paso 1 · ¿Tu parcela está aquí?**

Devuelve las parcelas alrededor del GPS y la más probable.

```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "zona": { "id": "itocta", "nombre": "Itocta", "distrito": 9 },
  "sugerida_id": "p-1042",
  "parcelas": {
    "type": "FeatureCollection",
    "features": [
      { "type": "Feature", "id": "p-1042", "properties": { "area_m2": 7200 },
        "geometry": { "type": "Polygon", "coordinates": [[[-66.2195, -17.4612], [-66.2188, -17.4612], [-66.2188, -17.4618], [-66.2195, -17.4618], [-66.2195, -17.4612]]] } }
    ]
  },
  "fuente": ["gamc_wms", "sentinel2"]
}
```

> Si no hay polígonos de parcelas, aceptable en v1: una malla de celdas de ~30 m (Landsat) alrededor del punto.

### `POST /parcelas`
```json
{ "parcela_ref": "p-1042", "lat": -17.4615, "lon": -66.2191 }
```
Respuesta `201`: `{ "parcela_id": "par_8f2c", "zona_id": "itocta", "distrito": 9 }`

### `PUT /parcelas/{parcela_id}/perfil`
Pantalla: **Paso 2 · Tu parcela**
```json
{
  "fuente_agua": "angostura",
  "prioridad": "agua"
}
```
- `fuente_agua`: `angostura` · `misicuni` · `pozo` · `rio_canal` · `solo_lluvia` · `no_se`
- `prioridad`: `agua` · `tierra` · `forraje` · `vender`

---

## 2. Clima

### `GET /clima/hoy?parcela_id=`
Pantalla: **Hoy** (tarjeta del día).
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "fecha": "2026-11-16",
  "icono": "sol",
  "t_max": 28, "t_min": 8,
  "lluvia_mm": 0,
  "humedad_suelo": { "valor": 0.12, "nivel": "seca" },
  "fuente": ["nasa_geos", "nasa_imerg", "nasa_smap"]
}
```

### `GET /clima/pronostico?parcela_id=&dias=28`
Pantallas: **Hoy**, **Calendario** (próximas 4 semanas, ventana de la semana).
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "dias": [
    { "fecha": "2026-11-21", "icono": "helada", "t_max": 24, "t_min": -2, "lluvia_mm": 0,
      "helada": true, "granizo": false, "confianza": "alta" },
    { "fecha": "2026-11-26", "icono": "granizo", "t_max": 23, "t_min": 10, "lluvia_mm": 8,
      "helada": false, "granizo": true, "confianza": "media" }
  ],
  "fuente": ["nasa_geos", "nasa_imerg"]
}
```
- 28 días. Días 15–28 con `confianza` `media` o `baja`: la app muestra "más lejos, puede cambiar".
- `icono`: `sol` · `nublado` · `lluvia` · `helada` · `granizo`.
- **Prioridad del icono** cuando coinciden: `granizo` > `helada` > `lluvia` > `nublado` > `sol`.

### `GET /clima/medido?parcela_id=&desde=&hasta=`
Pantalla: **Calendario → Ver semanas pasadas**. Mismo formato que `dias` del pronóstico, sin `confianza`. Fuente: `nasa_imerg`, `nasa_power`.

### `GET /clima/tipico?parcela_id=`
Pantallas: **Calendario → Próximos meses**, **Mi cultivo** (riesgos por mes). Climatología de 30 años por mes.
```json
{
  "actualizado_en": "2026-11-01T00:00:00-04:00",
  "periodo": "1995-2024",
  "meses": [
    { "mes": 1, "lluvia_mm": 118, "t_min": 10.4, "t_max": 24.8,
      "riesgos": ["granizo", "desborde"], "resumen": "lluvia_fuerte" },
    { "mes": 7, "lluvia_mm": 2, "t_min": -1.6, "t_max": 22.1,
      "riesgos": ["helada"], "resumen": "heladas" }
  ],
  "fuente": ["nasa_power", "nasa_imerg"]
}
```
- `riesgos`: `helada` · `granizo` · `desborde` · `poca_agua`
- `resumen`: `lluvia_fuerte` · `lluvias` · `primeras_lluvias` · `seco` · `frio` · `heladas` · `calor`

#### Reglas que la app espera que el equipo de datos aplique

| Concepto | Regla propuesta (a validar) |
|---|---|
| Helada (día) | `t_min ≤ 0 °C` |
| Lluvia (palabra) | `0` sin lluvia · `< 4 mm` débil · `< 15 mm` moderada · `≥ 15 mm` fuerte |
| Riesgo de helada en el mes | ≥ 20 % de los años con al menos 1 día `t_min ≤ 0` |
| Riesgo de granizo en el mes | Registro histórico local + días con convección fuerte (por definir con SENAMHI) |
| Riesgo de desborde | Lluvia del mes > percentil 80 + zonas de drenaje GAMC |
| Poca agua | Nivel de La Angostura < 40 % o lluvia acumulada < percentil 20 |

---

## 3. Agua

### `GET /agua/represas/la-angostura`
Pantallas: **Hoy** (tira), **Avisos**, **Rotaciones**.
```json
{
  "actualizado_en": "2026-11-15T18:00:00-04:00",
  "nivel_pct": 34,
  "volumen_hm3": 25.5,
  "estado": "bajo",
  "fuente": ["riego_n1"]
}
```
`estado`: `normal` · `bajo` · `critico`.

---

## 4. Cultivos

### `GET /cultivos`
Pantallas: **Sembrar**, **Detalle del cultivo**. Catálogo; cambia poco (caché de 7 días).
```json
{
  "actualizado_en": "2026-11-01T00:00:00-04:00",
  "cultivos": [
    { "id": "maiz", "nombre_codigo": "maiz_choclo", "duracion_dias": 110, "perenne": false,
      "kc": { "inicial": 0.3, "medio": 1.2, "final": 0.35 },
      "agua": "alta", "aguanta_helada": "no", "aguanta_granizo": "poco", "aguanta_sequia": "poco",
      "ventana_siembra": ["x","x","x","x","x","x","x","c","g","g","g","c"] }
  ],
  "fuente": ["fao56", "contexto_local"]
}
```
- `ventana_siembra`: 12 valores de enero a diciembre: `g` buena · `c` con cuidado · `x` mala.
- `agua`: `baja` · `media` · `alta`.

### `GET /cultivos/{cultivo_id}/fechas?parcela_id=&desde=&hasta=`
Pantalla: **Elegir fecha de siembra** (calendario con días buenos y malos).
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "dias": [
    { "fecha": "2026-11-20", "veredicto": "bueno", "cosecha_estimada": "2027-03-10",
      "motivos": ["poca_agua_angostura"] },
    { "fecha": "2027-05-10", "veredicto": "malo", "cosecha_estimada": "2027-08-28",
      "motivos": ["helada_jun_jul"] }
  ],
  "fuente": ["nasa_power", "nasa_imerg", "fao56"]
}
```
- `veredicto`: `bueno` · `cuidado` · `malo`
- `motivos` (códigos): `helada_jun_jul`, `granizo_nov_feb`, `desborde_ene_mar`, `poca_agua_angostura`, `lluvia_tardia`, …

---

## 5. Mis cultivos

### `GET /parcelas/{parcela_id}/cultivos`
Pantallas: **Hoy → Mis cultivos**, **Mi cultivo**, **Calendario** (eventos).
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "cultivos": [
    { "id": "pc-1", "cultivo_id": "maiz", "estado": "creciendo",
      "siembra": "2026-10-20", "cosecha": { "desde": "2027-02-01", "hasta": "2027-02-28" },
      "etapa": "creciendo", "avance_pct": 25 },
    { "id": "pc-2", "cultivo_id": "alfalfa", "estado": "creciendo", "perenne": true,
      "ultima_cosecha": "2026-10-25", "proximas_cosechas": ["2026-12-01", "2027-01-12"] },
    { "id": "pc-3", "cultivo_id": "haba", "estado": "pregunta_cosecha",
      "siembra": "2026-07-15", "cosecha": { "desde": "2026-11-15", "hasta": "2026-11-25" } },
    { "id": "pc-4", "cultivo_id": "avena", "estado": "planificado", "siembra": "2026-12-05", "origen": "rotacion" }
  ]
}
```
`estado`: `planificado` · `sembrado` · `creciendo` · `listo` · `pregunta_cosecha` · `calificado` (ver diagrama 8 en `FLUJO-APP.md`).

### `POST /parcelas/{parcela_id}/cultivos`
```json
{ "cultivo_id": "papa", "siembra": "2026-11-20" }
```
Respuesta `201` con el cultivo creado (mismo formato que arriba).

### `POST /parcelas/{parcela_id}/cultivos/{id}/cosecha`
Pantalla: **¿Cómo salió tu cosecha?**
```json
{ "resultado": "buena", "fecha": "2026-11-16" }
```
o, si todavía no cosechó: `{ "resultado": "todavia_no" }` → la API vuelve a preguntar en 3 días.

`resultado`: `buena` · `regular` · `mala` · `todavia_no`. **Sirve para validar el modelo** (ver §11).

---

## 6. Rotaciones

### `GET /rotaciones?parcela_id=&cultivo_actual=&cosecha=&objetivo=`
Pantalla: **¿Qué sembrar después?** Cumple el pedido del reto: **al menos 3 estrategias, incluida la actual**, cada una con por qué, evidencia, beneficios, lo que falta saber y riesgos.

Parámetros: `cultivo_actual` (id), `cosecha` (fecha), `objetivo` (`agua` · `tierra` · `forraje` · `vender`; opcional, por defecto el del perfil).

```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "siguiente_siembra": "2027-04-05",
  "epoca": "seca",
  "objetivo": "agua",
  "objetivo_motivo": { "codigo": "seca_angostura_baja", "valores": { "desde_mes": 4, "hasta_mes": 8, "nivel_pct": 34 } },
  "planes": [
    { "id": "actual", "actual": true, "cultivos": ["maiz", null],
      "siembra": null, "cosecha": null, "meses_sin_cultivo": 6,
      "puntaje": { "agua": 3, "tierra": 1, "forraje": 2, "vender": 2 },
      "etiquetas": [["poco_riego", "bien"], ["tierra_se_cansa", "mal"], ["meses_sin_cultivo", "mal"]],
      "por_que": "sin_cambio",
      "bueno": ["poco_riego", "conocido"],
      "riesgos": ["mas_gusano", "erosion_viento"],
      "falta_saber": ["rendimiento_parcela"],
      "evidencia": [
        { "codigo": "lluvia_dic_mar", "fuente": "nasa_imerg" },
        { "codigo": "campo_sin_cultivo_abr_sep", "fuente": "landsat" }
      ],
      "confianza": "media" },
    { "id": "maiz-haba", "cultivos": ["maiz", "haba"],
      "siembra": "2027-04-05", "cosecha": "2027-08-03", "meses_sin_cultivo": 1,
      "puntaje": { "agua": 1, "tierra": 3, "forraje": 1, "vender": 3 },
      "etiquetas": [["abona_tierra", "bien"], ["vende_haba", "bien"], ["mas_riego", "mal"]],
      "por_que": "fija_nitrogeno",
      "bueno": ["tierra_fertil", "menos_gusano", "vende_haba_verde"],
      "riesgos": ["helada_julio_flor", "riego_invierno"],
      "falta_saber": ["precio_haba"],
      "evidencia": [
        { "codigo": "heladas_may_ago", "fuente": "nasa_power" },
        { "codigo": "poca_lluvia_abr_sep", "fuente": "nasa_imerg" },
        { "codigo": "angostura_34", "fuente": "riego_n1" }
      ],
      "confianza": "media" }
  ],
  "mejor_id": "maiz-avena"
}
```
- Siempre incluir el plan `actual` + **mínimo 3 alternativas**. `mejor_id` nunca es el actual.
- `puntaje`: 1 (peor) a 3 (mejor) por objetivo. El orden lo decide `objetivo` **y la época** de `siguiente_siembra`: en época de lluvias, `agua` pesa menos.
- `epoca`: `seca` (abr–sep) · `lluvias` (oct–mar).
- `etiquetas`: `[codigo, "bien" | "mal" | "neutro"]`, máximo 3.

### `POST /parcelas/{parcela_id}/rotacion`
Pantalla: **Quiero este plan**.
```json
{ "plan_id": "maiz-haba", "siembra": "2027-04-05" }
```
Crea un cultivo `planificado` (§5), que aparece en el Calendario.

---

## 7. Avisos

### `GET /avisos?parcela_id=`
Pantalla: **Avisos**. Dos grupos.
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "alertas": [
    { "id": "al-1", "tipo": "helada", "fecha_evento": "2026-11-21", "momento": "madrugada",
      "valor": { "t_min": -2 }, "confianza": "alta", "nuevo": true, "volver_a_avisar": "2026-11-20" },
    { "id": "al-2", "tipo": "granizo", "fecha_evento": "2026-11-26", "confianza": "baja", "nuevo": true,
      "confirmar_dias_antes": 2 },
    { "id": "al-3", "tipo": "represa_baja", "valor": { "nivel_pct": 34 }, "nuevo": false }
  ],
  "recordatorios": [
    { "id": "re-1", "tipo": "pregunta_cosecha", "cultivo_id": "haba", "fecha": "2026-11-16", "nuevo": true },
    { "id": "re-2", "tipo": "cosecha_hoy", "cultivo_id": "haba", "fecha": "2026-11-15" },
    { "id": "re-3", "tipo": "cosecha_1_dia", "cultivo_id": "haba", "fecha": "2026-11-14" },
    { "id": "re-4", "tipo": "cosecha_7_dias", "cultivo_id": "haba", "fecha": "2026-11-08" }
  ]
}
```
- `alertas[].tipo`: `helada` · `granizo` · `lluvia_fuerte` · `desborde` · `represa_baja` · `temporada`
- `recordatorios[].tipo`: `cosecha_7_dias` · `cosecha_1_dia` · `cosecha_hoy` · `pregunta_cosecha` · `siembra_planificada`
- Las notificaciones push salen a las **6:00**. Alertas: 7 días antes (si la confianza lo permite) y 1 día antes.

---

## 8. Mi zona

### `GET /zonas/{zona_id}/mapa`
Pantalla: **Mi zona**.
```json
{
  "actualizado_en": "2026-11-16T06:00:00-04:00",
  "resumen": { "sin_agua_vecinos": 8, "periodo": "semana", "direccion": "este" },
  "capas": {
    "sin_agua": { "type": "FeatureCollection", "features": [] },
    "inundable": { "type": "FeatureCollection", "features": [] },
    "mi_parcela": { "type": "Feature", "geometry": { "type": "Polygon", "coordinates": [] } }
  },
  "fuente": ["reportes", "gamc_wms"]
}
```
- `sin_agua`: parcelas con reportes "no llegó el agua" en 7 días, **sin datos personales**. Mínimo 3 reportes por celda para mostrarla.
- `inundable`: drenaje y zonas de desborde (GAMC WMS + histórico).

### `GET /zonas/{zona_id}/historial`
Pantalla: **Mi zona → Historial**.
```json
{
  "eventos": [
    { "fecha": "2026-10-24", "tipo": "sequia", "codigo": "poca_agua_3_meses" },
    { "fecha": "2024-03-10", "tipo": "inundacion", "lugar": "canal_valverde" },
    { "fecha": "2024-07-04", "tipo": "represa_baja", "valor": { "nivel_pct": 18 } },
    { "fecha": "2018-11-26", "tipo": "granizo", "cultivos": ["maiz", "papa", "haba"] }
  ],
  "fuente": ["contexto_local"]
}
```

### `POST /reportes`
Pantalla: **Avisar algo → Enviar aviso**. Debe aceptar envíos atrasados (cola sin señal).
```
Idempotency-Key: 0d3c1f7e-…   (id local generado en el celular)
Content-Type: multipart/form-data
```
| Campo | Tipo | Nota |
|---|---|---|
| `tipo` | texto | `sin_agua` · `helada` · `granizo` · `inundacion` · `plaga` |
| `parcela_id` | texto | |
| `ocurrido_en` | fecha-hora | Hora del celular, no del envío |
| `foto` | archivo opcional | JPEG ≤ 300 KB |
| `audio` | archivo opcional | AAC/Opus ≤ 60 s |

Respuesta `201`: `{ "id": "rep-551", "vecinos_mismo_tipo_semana": 7 }`

---

## 9. Errores

```json
{ "error": { "codigo": "parcela_no_encontrada", "mensaje_tecnico": "parcela_id par_xx no existe" } }
```
| HTTP | Cuándo |
|---|---|
| 400 | Parámetro inválido |
| 404 | No existe |
| 409 | Reporte duplicado (`Idempotency-Key` ya usada): devolver el original |
| 422 | Datos fuera de rango |
| 503 | Fuente NASA caída: devolver el último dato válido con `"desactualizado": true` |

---

## 10. Códigos de fuente

| Código | Dataset | Uso en la app |
|---|---|---|
| `nasa_power` | NASA POWER (diario + climatología) | Heladas, temperatura, clima típico, fechas buenas |
| `nasa_imerg` | GPM IMERG | Lluvia medida y típica |
| `nasa_smap` | SMAP L3/L4 | Humedad del suelo |
| `nasa_geos` | GEOS-FP / GEOS-S2S | Pronóstico 28 días |
| `landsat` | Landsat 8/9 (NDVI) | Campo sin cultivo, estrés |
| `sentinel2` | Copernicus Sentinel-2 | NDVI a 10 m, límites de parcelas |
| `gamc_wms` | GAMC WMS | Distritos, zonas, drenaje |
| `riego_n1` | Asociación de Riego N°1 La Angostura | Nivel de la represa |
| `fao56` | FAO-56 | Kc, duración de cultivos |
| `contexto_local` | `docs/CONTEXTO-LOCAL.md` | Eventos históricos |
| `reportes` | Reportes de agricultores | Mapa de la zona |

---

## 11. Lo que necesitamos del equipo de datos

1. **Malla común**: todos los datasets llevados a una misma celda (sugerido ~1 km para clima y 30 m para NDVI) sobre el Distrito 9 y el 15.
2. **Climatología 30 años** por celda y mes (`/clima/tipico`).
3. **Pronóstico 28 días** con `confianza` por día.
4. **Reglas de veredicto** de fechas de siembra por cultivo (`/cultivos/{id}/fechas`), documentadas y explicables.
5. **Puntajes de rotación** por objetivo y época, con su evidencia (`/rotaciones`).
6. **Validación**: comparar los resultados de cosecha (`buena`/`regular`/`mala`) con lo que el modelo predijo, y reportar el acierto.
7. **Incertidumbre**: decir dónde el modelo no alcanza y hace falta un técnico (alimenta `falta_saber` y `confianza`).

## 12. Pendiente de definir

- Dominio, autenticación (sugerido: token por dispositivo, sin cuenta con correo).
- Fuente oficial del granizo (¿SENAMHI?).
- Si hay polígonos de parcelas reales o se usa malla.
- Precios de mercado para el objetivo `vender` (hoy: `falta_saber`).
