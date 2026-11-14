# Contexto local — zona agrícola del área GAMC (Cercado, Cochabamba)

> Investigación: **14/11/2026**. Fuentes: capas WMS GAMC (proyecto 04), NASA POWER, OpenStreetMap (Nominatim), prensa y estudios locales.
> Objetivo: saber **dónde hay cultivos** dentro del área de los datos GAMC, **qué se cultiva**, **qué pérdidas** hay y qué implica para el reto.
> Coordenadas en **WGS84 (lat, lon)**, grados decimales.

---

## 1. Área de los datos GAMC

| Capa | Service ID | BBOX (lon_min, lat_min, lon_max, lat_max) |
|---|---|---|
| Periurbanos | `c52066a1-32fd-4925-81e0-c2dcb8f4238f` | `-66.275711, -17.525117, -66.072201, -17.326109` |
| Drenaje e Influencia | `d4cea6e3-fc7f-482a-94ad-bd377df78886` | `-66.269936, -17.530591, -66.045853, -17.260142` |
| Límite Distritos | `7eb13092-bf0e-493b-aae6-03c43eedda2c` | `-66.280703, -17.531190, -66.069520, -17.257306` |

**Método:** `GetFeatureInfo` sobre una malla regular de la imagen 800×900 px del bbox `-66.28,-17.53,-66.04,-17.26` (paso ≈ 0,018° ≈ 2 km). Centroide = promedio de los puntos de la malla que caen en cada clase, así que es **aproximado** (sirve para ubicar, no para geometría exacta).

> ⚠️ El proxy GAMC aplica **rate limit** ("Demasiadas solicitudes. Inténtalo de nuevo en unos minutos."). Con más de 1 req/s en paralelo bloquea varios minutos. En la app conviene cachear y no hacer barridos.

### 1.1 Capa Periurbanos — clases y centroides

| Periurbano | Detalle (cobertura) | Puntos | Centroide (lat, lon) | Rango lon | Rango lat |
|---|---|---|---|---|---|
| Periurbanos consolidados | Periurbano | 57 | -17.4307, -66.1949 | -66.256 … -66.094 | -17.491 … -17.329 |
| Periurbanos en crecimiento | Herbazales ralos con intervención urbana | 17 | -17.4666, -66.2274 | -66.274 … -66.094 | -17.491 … -17.428 |
| Periurbanos en crecimiento | Arbustales ralos con herbazales e intervención urbana | 12 | -17.4782, -66.2050 | -66.247 … -66.076 | -17.518 … -17.446 |
| Periurbanos en crecimiento | Herbazales ralos con alta intervención urbana | 6 | -17.4700, -66.2005 | -66.256 … -66.112 | -17.500 … -17.428 |

- Leyenda: verde = *en crecimiento*, salmón = *consolidados*, gris = *otros*.
- **No hay una clase "cultivo"**: la capa describe presión urbana sobre la cobertura natural o agrícola. Sirve como **máscara de tierra agrícola en riesgo de urbanización**.
- Los periurbanos "en crecimiento" se concentran en el **suroeste (D9)**, alrededor de `-17.47, -66.22`.

### 1.2 Capa Límite Distritos — centroides aproximados

| Distrito | Comuna | Puntos | Centroide (lat, lon) |
|---|---|---|---|
| D1 | Tunari | 3 | -17.3680, -66.1300 |
| D2 | Tunari | 5 | -17.3452, -66.1840 |
| D3 | Molle | 11 | -17.3707, -66.1922 |
| D4 | Molle | 5 | -17.3938, -66.1984 |
| D5 | Alejo Calatayud | 5 | -17.4172, -66.1786 |
| D6 | Valle Hermoso | 2 | -17.4100, -66.1390 |
| D7 | Valle Hermoso | — | (no capturado en el segundo barrido) |
| D8 | Alejo Calatayud | 9 | -17.4560, -66.1060 |
| **D9** | **Itocta** | **97** | **-17.4611, -66.2185** (lon -66.274 … -66.148, lat -17.518 … -17.401) |
| D10 | Adela Zamudio | 1 | -17.3920, -66.1660 |
| D11 | Adela Zamudio | 2 | -17.3920, -66.1390 |
| D12 | Adela Zamudio | 2 | -17.3740, -66.1570 |
| D13 | Tunari | 15 | -17.3140, -66.1444 |
| D14 | Valle Hermoso | 2 | -17.4370, -66.1120 |
| D15 | Tamborada | 9 | -17.4880, -66.1340 |

**D9 es el distrito más grande**: abarca alrededor de un tercio del área muestreada y coincide con la mayor mancha periurbana.

### 1.3 Capa Drenaje e Influencia
Red de torrenteras: abanicos desde la cordillera del Tunari (norte, D13) y red densa en las serranías del sur (D9, D15). Sirve para riesgo de erosión, escorrentía y acceso a agua de riego. `GetFeatureInfo` devuelve vacío porque las líneas son finas y es difícil acertar un píxel.

---

## 2. Lugares clave (coordenadas)

### 2.1 Dentro del área GAMC (Cercado)

| Lugar | Lat, Lon | Fuente coord. | Relevancia |
|---|---|---|---|
| Centroide D9 Itocta | -17.4611, -66.2185 | GAMC (malla) | Zona agrícola-lechera principal |
| Itocta | -17.4627, -66.2009 | OSM | Subalcaldía D9 |
| Pucarita Chica | -17.4522, -66.2060 | OSM | Sindicato agrario; ~25.000 L leche/día (2013) |
| Río La Tamborada | -17.4418, -66.1574 | OSM | Río contaminado usado para riego |
| Laguna Pampa / PTAR Alba Rancho | -17.4418, -66.2313 | OSM | Efluente de aguas residuales usado para riego |
| Laguna Alalay | -17.4080, -66.1389 | OSM | Cuerpo de agua urbano (referencia) |
| Centroide D13 Tunari (norte) | -17.3140, -66.1444 | GAMC (malla) | Floricultura, piedemonte |
| Centroide D15 Tamborada | -17.4880, -66.1340 | GAMC (malla) | Zona lechera Tamborada A/B |
| Punto NASA POWER usado | -17.46, -66.17 | — | Climatología §5 |

### 2.2 Fuera del área GAMC (pérdidas climáticas del departamento)

Centroides de municipio según OSM; son aproximados y no corresponden al casco urbano.

| Municipio | Lat, Lon | Región |
|---|---|---|
| Mizque | -18.0376, -65.5119 | Cono Sur |
| Aiquile | -18.2002, -65.1806 | Cono Sur |
| Pasorapa | -18.3215, -64.6775 | Cono Sur |
| Totora | -17.5914, -65.1662 | Cono Sur |
| Vacas | -17.6000, -65.5983 | Valle Alto / andina |
| Anzaldo | -17.8192, -65.9383 | Valle Alto |
| Sacabamba | -17.7688, -65.7970 | Valle Alto |
| Santiváñez | -17.5697, -66.2123 | Valle Bajo |
| Sipe Sipe | -17.4535, -66.3575 | Valle Bajo |
| Colomi | -17.3383, -65.8683 | Andina / trópico |

---

## 3. ¿Existen cultivos en la zona? Sí, sobre todo en D9 y el sur de Cercado

- El **Distrito 9 es la última reserva agrícola del municipio**: los medios lo llaman "la única zona agrícola de la provincia Cercado". Comunidades: Tamborada A/B, Pucarita Chica, Primero de Mayo, Challacaba, Alba Rancho y San José de la Banda.
  - Aporta **~80 % de la leche del municipio** ([Los Tiempos vía CEDIB, 17/03/2013](https://www.cedib.org/noticias/alerta-en-zonas-agrarias-por-ampliacion-urbana-los-tiempos-17-03-13)).
- **Norte (D13)**: flores; quedan restos de choclo y alfalfa en "las Maicas" ([Opinión, 03/02/2019](https://www.opinion.com.bo/cochabamba/aacute-reas-cultivo-redujeron-28-ciento-d-eacute-cadas-cercado/20190203182300640113.html)).

### Qué se cultiva (Cercado, ~2.600 ha cultivadas en 2019)

| Cultivo | % superficie | Rol |
|---|---|---|
| **Alfalfa** | ~50 % | Forraje para lechería (perenne, 4–6 años) |
| **Maíz** (choclero y forrajero) | ~46 % | Choclo para venta/humintas + ensilaje |
| Avena, tubérculos, hortalizas, haba | ~4 % | Forraje de invierno / consumo familiar |

Fuente: Asociación de Usuarios del Sistema Nacional de Riego N°1 La Angostura, citada en [Opinión, 03/02/2019](https://www.opinion.com.bo/cochabamba/aacute-reas-cultivo-redujeron-28-ciento-d-eacute-cadas-cercado/20190203182300640113.html).

**Rotación actual típica (inferida):** maíz en el verano lluvioso (nov–abr) → avena, haba o barbecho en el invierno seco → alfalfa varios años → maíz. Es un sistema **forraje–lechería**.

---

## 4. Línea de tiempo de noticias y pérdidas

Fechas verificadas leyendo cada nota; los motores de búsqueda devolvían fechas erróneas.

### 4.1 Cercado / área GAMC

| Fecha | Lugar (lat, lon) | Evento | Datos clave | Fuente |
|---|---|---|---|---|
| 17/03/2013 | D8–D9 (-17.46, -66.22) | Ampliación de la mancha urbana | +13.945 ha urbanizables en D8–D9 (polígonos A, B = La Tamborada/Pucarita Chica, C = Primero de Mayo); se proyectan 198 barrios y 150.000 habitantes | [Los Tiempos vía CEDIB](https://www.cedib.org/noticias/alerta-en-zonas-agrarias-por-ampliacion-urbana-los-tiempos-17-03-13) |
| 06/10/2017 | 34 municipios, **incluye parte de Cercado** | Sequía + heladas + granizo | 28.000 ha (20.000 por sequía, 8.000 por helada y granizo); sobre todo maíz, luego papa | [ABI vía ReliefWeb](https://reliefweb.int/report/bolivia-plurinational-state/cochabamba-28000-hect-reas-de-cultivos-fueron-afectados-por) |
| 03/02/2019 | Cercado | Pérdida de tierra agrícola | 3.600 → 2.600 ha (−28 %) en ~20 años; distritos 2, 3, 4 y 5 ya urbanizados | [Opinión](https://www.opinion.com.bo/cochabamba/aacute-reas-cultivo-redujeron-28-ciento-d-eacute-cadas-cercado/20190203182300640113.html) |
| 14/07/2023 | Departamento | Caída de la producción por avance urbano | 1,6 → 1,1 M t (2019-20 → 2021-22); leche 500 k → 320 k L/día; 90 granjas de cerdos cerradas; USD 20 M de pérdidas en 2022 | [Los Tiempos](https://www.lostiempos.com/actualidad/economia/20230714/produccion-agropecuaria-cochabamba-baja-20-avance-urbano) |
| s/f | La Maica, Villa Loreto, La Tamborada (Cercado) | Riego con agua del río Rocha | Canales con basura; agua de La Angostura mezclada con el Rocha; enfermedades gastrointestinales | [La Patria](https://lapatria.bo/enfoque-nacional/denuncia/en-cochabamba-contaminacion-en-canales-de-riego-genera-enfermedades-estomacales) |
| ~jun 2026 | Tamborada A (D15, -17.49, -66.13) | Bloqueos | Lecheros sin forraje tras 15 días de bloqueos (fecha aproximada, por publicaciones en redes) | [Red Uno (Facebook)](https://www.facebook.com/RedUnotv/videos/comunidad-productores-lecheros-de-tamborada-a-denuncian-que-tras-15-d%C3%ADas-de-bloq/1317951313772069) |

### 4.2 Resto del departamento (contexto climático)

| Fecha | Lugar (lat, lon) | Evento | Hectáreas / familias | Cultivos | Fuente |
|---|---|---|---|---|---|
| 27/02/2015 | 21 municipios, 97 comunidades | Granizo + lluvias (ene–feb) | ~1.400 ha / 3.300 familias | Papa, maíz, hortalizas, forraje | [ABI vía ReliefWeb](https://reliefweb.int/report/bolivia-plurinational-state/granizo-y-lluvias-afectan-1400-hect-reas-de-cultivos-en) |
| 02/02/2023 | Vacas (-17.60, -65.60) + 13 municipios del Cono Sur | Sequía + heladas | Vacas 1.397 ha / 2.000 familias; departamento 34.435 ha (oct 2022 – feb 2023, Seguro Agrario) | Papa (hasta −98 %), oca, maíz, trigo, avena | [Los Tiempos](https://www.lostiempos.com/actualidad/cochabamba/20230202/desastre-sequia-heladas-danan-98-cultivos-papa-cono-sur) |
| 08/07/2025 | Mizque (-18.04, -65.51), Aiquile, Bolívar | Heladas | 180 ha, 18 comunidades | Papa, arveja, tomate | [Unitel](https://unitel.bo/noticias/economia/heladas-en-cochabamba-18-comunidades-y-180-hectareas-de-cultivos-afectados-IF16571922) |
| 09/03/2026 | Santiváñez (-17.57, -66.21) | Sequía | 233 ha / 733 familias | Maíz | [Unitel](https://television.unitel.bo/portada/noticias/sequia-golpea-a-cultivos-y-ganado-de-cuatro-municipios-de-cochabamba-y-alistan-declaratoria-de-emergencia-AO19536710) |
| 09/03/2026 | Anzaldo (-17.82, -65.94) | Sequía | 955 ha / 1.180 familias | Maíz, papa, arveja | ídem |
| 09/03/2026 | Totora (-17.59, -65.17) | Sequía | 5.936 ha / 2.404 familias | Papa, maíz | ídem |
| 09/03/2026 | Pasorapa (-18.32, -64.68) | Sequía | ~2.100 ha / 943 familias | Maíz, papa, tomate | ídem |
| mar 2026 | 4 municipios | Preparación de la declaratoria de emergencia por sequía | — | Cultivos + ganado | [Publiagro](https://publiagro.com.bo/2026/03/cochabamba-alista-declaratoria-de-emergencia-por-sequia-en-cuatro-municipios) |
| 21, 22 y 26/06/2026 | Mizque (-18.04, -65.51) | Heladas | 320 ha / 520 familias; tomate −60 a −100 % | Tomate, papa, pimentón, arveja, chirimoya, durazno | [La Patria](https://lapatria.bo/enfoque-nacional/regiones/productores-enfrentan-crisis-frio-extremo) |
| 26/06/2026 | Cono Sur | Heladas | 270 ha / 550 familias | — | Gobernación, vía [Abya Yala TV (Facebook)](https://www.facebook.com/AbyaYalaTv/posts/cochabamba%EF%B8%8F-heladas-en-el-cono-sur-afectaron-270-hect%C3%A1reas-de-cultivos-y-perjudi/1631202592343221) |

> En Cercado, el único reporte de daño climático encontrado es la **helada de 2017** ("una parte de Cercado"). Las pérdidas recientes por clima se concentran en el Cono Sur y el Valle Alto. En Cercado las amenazas dominantes son la **urbanización** y la **calidad y escasez del agua**.

### 4.3 Estudios de referencia
- [La expansión urbana y la pérdida de tierras agrícolas en el valle central de Cochabamba y Sacaba (1962–2016)](https://www.researchgate.net/publication/343237010_La_expansion_urbana_y_la_perdida_de_tierras_agricolas_en_el_valle_central_de_Cochabamba_y_Sacaba)
- [Diagnóstico de contaminación de acuíferos en el Distrito 9 (UCB, 2008)](https://www.researchgate.net/publication/284327819_Diagnostico_Sobre_el_Nivel_de_Contaminacion_de_Acuiferos_en_el_Distrito_9_del_Municipio_del_Cercado_en_la_Ciudad_de_Cochabamba_y_Propuesta_para_su_Proteccion_y_Control)
- [Uso del agua en Challacaba, D9 (Aguatuya / Centro AGUA)](https://www.musgroup.net/node/264): riego con efluente de la PTAR municipal.
- [Caracterización productiva del Departamento de Cochabamba (SIIP, 2024)](https://siip.produccion.gob.bo/noticias/files/2024-a97c5-Caracterizacion-de-Cochabamba.pdf)

---

## 5. Clima del punto D9 (NASA POWER, climatología)

Consulta: `https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M_MIN,T2M_MAX,PRECTOTCORR,FROST_DAYS,EVPTRNS&community=AG&longitude=-66.17&latitude=-17.46&format=JSON`

| | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lluvia (mm/día) | 3,4 | 3,4 | 1,8 | 0,7 | 0,2 | 1,5* | 0,2 | 0,3 | 0,4 | 0,8 | 1,2 | 2,8 |
| Días de helada | 0 | 0 | 0,1 | 0,1 | 2,2 | 3,0 | **6,3** | 2,9 | 0,2 | 0,1 | 0 | 0 |
| T mín. (°C) | 2,6 | 3,1 | −1,0 | −0,7 | −3,3 | −3,5 | **−4,3** | −3,6 | −1,3 | −0,8 | 1,8 | 2,5 |
| T máx. (°C) | 27,6 | 27,7 | 27,5 | 26,5 | 26,6 | 25,8 | 25,3 | 26,3 | 29,0 | 29,0 | 30,1 | 29,3 |

- ~15 días de helada al año, concentrados en **may–ago**; la lluvia se concentra en **dic–mar**.
- *Valor anómalo en junio. La celda POWER (≈ 0,5°) incluye zonas de montaña, así que probablemente hay sesgo frío. Las temperaturas parecen extremos mensuales, no medias. Validar con SENAMHI (estación Aeropuerto Cochabamba).

---

## 6. Implicaciones para el reto

1. **Zona piloto clara: Distrito 9 (Itocta), centro `-17.46, -66.22`.** Usar la capa *Periurbanos* como máscara y *Distritos* para agregar resultados.
2. **Rotación actual a comparar:** maíz–alfalfa (forraje lechero). Alternativas candidatas:
   - Maíz → **avena/vicia** (cobertura invernal, forraje en la ventana seca, fija N).
   - Alfalfa → maíz → **haba/arveja** (leguminosa de invierno, corta ciclos de plaga).
   - Diversificar con **hortalizas de alto valor**, solo donde el agua de riego no sea residual.
3. **Campo desnudo:** may–oct (después de la cosecha de maíz, sin lluvia) → más erosión eólica y pérdida de materia orgánica. Se puede detectar con NDVI de MODIS o Sentinel-2.
4. **Vulnerabilidades por estación:** heladas en jun–jul (hortalizas, maíz tardío), déficit hídrico en ago–nov (siembra), granizo en dic–feb.
5. **Factores no NASA que el agricultor debe poder ingresar:** calidad del agua de riego (residual o limpia), presión de venta del terreno y demanda de forraje de su hato.
6. **Brechas de datos:**
   - No hay una capa de cultivos real en GAMC.
   - Las estadísticas municipales (SIIP/INE) no cargaron para Cercado.
   - La última cifra confiable de superficie cultivada en Cercado es de 2019.
