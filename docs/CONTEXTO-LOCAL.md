# Contexto local — investigación previa al análisis de datos

> Investigación: **14/11/2026**. Reto local GAMC: *Field Shift — Agrotecnología y Gestión del Agua para Agricultores: Decision Support for Cochabamba*.
> Este documento reúne **lo que se sabe antes de analizar datos**: dónde se cultiva, qué, cuándo, con qué agua, qué suelos y qué eventos climáticos generan pérdidas.
> Coordenadas en **WGS84 (lat, lon)**. Fechas verificadas leyendo cada nota (los buscadores devolvían fechas erróneas).

---

## 0. Qué pide el reto local, y qué sección de este documento lo alimenta

| Requisito GAMC | Insumo previo | Sección |
|---|---|---|
| Riesgo hídrico por parcela (humedad de suelo + lluvia prevista) | Estacionalidad de lluvia, sequías, estado de represas, El Niño 2026–27 | §3, §4, §5 |
| Propiedades del suelo (textura, retención, drenaje) | Salinidad y suelos del D9, fuentes globales | §6 |
| Kc (FAO 56), tolerancia a sequía y helada, rendimiento | Tabla Kc + duración de etapas + tolerancias | §7 |
| Ventanas de siembra, costo de semilla, uso/mercado | Calendario local, dos campañas, costos | §8 |
| Pronóstico de lluvia a 7 y 14 días en el periurbano | Fuentes de pronóstico | §9 |
| Comparar ≥3 rotaciones, incluida la actual | Rotación actual + candidatas | §10 |

---

## 1. Área de los datos GAMC (proyecto 04)

| Capa | Service ID | BBOX (lon_min, lat_min, lon_max, lat_max) |
|---|---|---|
| Periurbanos | `c52066a1-32fd-4925-81e0-c2dcb8f4238f` | `-66.275711, -17.525117, -66.072201, -17.326109` |
| Drenaje e Influencia | `d4cea6e3-fc7f-482a-94ad-bd377df78886` | `-66.269936, -17.530591, -66.045853, -17.260142` |
| Límite Distritos | `7eb13092-bf0e-493b-aae6-03c43eedda2c` | `-66.280703, -17.531190, -66.069520, -17.257306` |

**Método:** `GetFeatureInfo` sobre una malla con paso ≈ 2 km. Los centroides son aproximados.
⚠️ El proxy tiene **rate limit** ("Demasiadas solicitudes…"): la app debe cachear y no hacer barridos.

### 1.1 Periurbanos (atributos `Periurbano`, `Detalle`)

| Clase | Detalle | Centroide (lat, lon) |
|---|---|---|
| Consolidados | Periurbano | -17.4307, -66.1949 |
| En crecimiento | Herbazales ralos con intervención urbana | -17.4666, -66.2274 |
| En crecimiento | Arbustales ralos con herbazales e intervención urbana | -17.4782, -66.2050 |
| En crecimiento | Herbazales ralos con alta intervención urbana | -17.4700, -66.2005 |

No hay una clase "cultivo". Las parcelas agrícolas están dentro o al borde de las zonas "en crecimiento" del sur.

### 1.2 Distritos (centroides aproximados)

| Distrito | Comuna | Centroide (lat, lon) | Nota |
|---|---|---|---|
| D1 | Tunari | -17.3680, -66.1300 | |
| D2 | Tunari | -17.3452, -66.1840 | |
| D3 | Molle | -17.3707, -66.1922 | |
| D4 | Molle | -17.3938, -66.1984 | |
| D5 | Alejo Calatayud | -17.4172, -66.1786 | |
| D6 | Valle Hermoso | -17.4100, -66.1390 | |
| D7 | Valle Hermoso | — | no capturado |
| D8 | Alejo Calatayud | -17.4560, -66.1060 | |
| **D9** | **Itocta** | **-17.4611, -66.2185** | Principal zona agrícola (lon -66.274…-66.148, lat -17.518…-17.401) |
| D10 | Adela Zamudio | -17.3920, -66.1660 | |
| D11 | Adela Zamudio | -17.3920, -66.1390 | |
| D12 | Adela Zamudio | -17.3740, -66.1570 | |
| D13 | Tunari | -17.3140, -66.1444 | Piedemonte norte; floricultura; torrenteras |
| D14 | Valle Hermoso | -17.4370, -66.1120 | |
| D15 | Tamborada | -17.4880, -66.1340 | Zona agrícola sur |

### 1.3 Drenaje e Influencia
Red de torrenteras: abanicos desde el Tunari (norte) y red densa en las serranías del sur (D9, D15). Sirve para riesgo de **escorrentía, erosión e inundación** de parcelas.

### 1.4 Lugares clave

| Lugar | Lat, Lon | Relevancia |
|---|---|---|
| Itocta (D9) | -17.4627, -66.2009 | Subalcaldía D9 |
| Pucarita Chica (D9) | -17.4522, -66.2060 | Comunidad agrícola |
| Río La Tamborada | -17.4418, -66.1574 | Río usado para riego; desbordes |
| PTAR Alba Rancho / Laguna Pampa | -17.4418, -66.2313 | Efluente usado para riego |
| Laguna Alalay | -17.4080, -66.1389 | Cuerpo de agua urbano |
| Punto NASA POWER | -17.46, -66.17 | Climatología §5 |

---

## 2. Qué se cultiva en el área

Cercado tenía **~2.600 ha cultivadas** (2019) según la Asociación de Usuarios del Sistema de Riego N°1 La Angostura ([Opinión, 03/02/2019](https://www.opinion.com.bo/cochabamba/aacute-reas-cultivo-redujeron-28-ciento-d-eacute-cadas-cercado/20190203182300640113.html)):

| Cultivo | % superficie | Uso |
|---|---|---|
| **Alfalfa** | ~50 % | Forraje (perenne, 4–6 años) |
| **Maíz** (choclero y forrajero) | ~46 % | Choclo (venta) + forraje |
| Avena, tubérculos, hortalizas, haba | ~4 % | Forraje de invierno, consumo y venta |

- **D13 (norte)**: flores.
- **Valle Central y Bajo** (vecinos al área): papa, haba, arveja, cebolla, zanahoria, lechuga, remolacha, maíz, frutales ([Opinión 27/11/2018](https://www.opinion.com.bo/cochabamba/tiquipaya-quillacollo-granizo-da-ntilde-cultivos-23-comunidades/20181127200800633962.amp.html); [Los Tiempos 30/03/2018](https://www.lostiempos.com/actualidad/economia/20180330/se-inicia-siembra-seis-cultivos-preven-subir-rendimiento-30)).

---

## 3. Eventos climáticos y pérdidas

### 3.1 En el área GAMC y el Valle Central (lo más relevante)

| Fecha | Lugar (lat, lon) | Evento | Impacto | Fuente |
|---|---|---|---|---|
| 15/02/2012 | Río Rocha, Cercado | Crecida; se prevé desborde | Riesgo para cultivos y viviendas ribereñas | [Los Tiempos](https://www.lostiempos.com/actualidad/local/20120215/aumenta-caudal-del-rio-rocha-se-preve-desborde-cultivos-viviendas) |
| 25/01/2014 | Colcapirhua, Valle Bajo | Desborde del río Rocha | 50 personas evacuadas | [ReliefWeb](https://reliefweb.int/report/bolivia/cochabamba-trasladan-50-personas-afectadas-por-desborde-de-r-o-rocha-en-colcapirhua) |
| 18/09/2016 | Represa La Angostura | Sequía | Solo 2,5 Mm³ acumulados (capacidad 75 Mm³); conflicto por agua | [Los Tiempos vía ReliefWeb](https://reliefweb.int/report/bolivia-plurinational-state/la-angostura-se-seca-y-sube-disputa-por-agua) |
| 06/10/2017 | 34 municipios, **incluye parte de Cercado** | Sequía + heladas + granizo | 28.000 ha (20.000 por sequía, 8.000 por helada y granizo); sobre todo maíz, luego papa | [ABI vía ReliefWeb](https://reliefweb.int/report/bolivia-plurinational-state/cochabamba-28000-hect-reas-de-cultivos-fueron-afectados-por) |
| 26/11/2018 | Tiquipaya (D3, D6) y Quillacollo, 23 comunidades | **Granizada** (~2 h) | Maíz, papa, haba, arveja, cebolla, lechuga y espinaca perdidos; 40 familias en Bruno Mokho; 100 % en la cordillera | [Opinión 27/11/2018](https://www.opinion.com.bo/cochabamba/tiquipaya-quillacollo-granizo-da-ntilde-cultivos-23-comunidades/20181127200800633962.amp.html) |
| 11/03/2023 | La Angostura → Valle Central y Bajo | Sequía | Represa con 9 Mm³ (2,4 m), solo 2 turnos de riego; productores de la Maica piden desfogue | [Los Tiempos](https://www.lostiempos.com/actualidad/cochabamba/20230311/angostura-solo-tiene-agua-dos-desfogues) |
| **10/03/2024** | Cercado: río Rocha, torrentera Taquiña (norte), **zona sur** | **Lluvia intensa / inundación** | Rocha "al tope"; desborde de la torrentera Taquiña; inundaciones en el sur; **canal Valverde desbordado → cultivos anegados** | [Opinión](https://www.opinion.com.bo/cochabamba/lluvias-dan-tregua-rocha-tope-desbordes-inundaciones-sur-norte/20240310113846939411.html) |
| 04/07/2024 | La Angostura → 6 municipios | Represa baja | 18 % de capacidad (3,1 m, 16 Mm³), "no va a ser suficiente" para Valle Central y parte del Bajo | [Unitel](https://unitel.bo/noticias/economia/bajo-nivel-del-agua-de-la-represa-de-la-angostura-preocupa-a-regantes-de-cochabamba-CH12515052) |
| s/f | La Maica, La Tamborada | Sequía → riego con agua del Rocha | Ante la falta de agua de La Angostura se riega con agua contaminada del Rocha (hortalizas, forraje) | [La Patria](https://lapatria.bo/enfoque-nacional/denuncia/en-cochabamba-contaminacion-en-canales-de-riego-genera-enfermedades-estomacales) |
| **24/10/2026** | Departamento | **Sequía actual** | La Cámara Agropecuaria prevé **3 meses de escasez de agua** y pide un plan contra la sequía | [Bolivisión](https://redbolivision.tv.bo/noticia/productores-de-cochabamba-advierten-tres-meses-de-escasez-de-agua) |

### 3.2 Resto del departamento (patrones regionales)

| Fecha | Lugar (lat, lon) | Evento | Hectáreas / familias | Cultivos | Fuente |
|---|---|---|---|---|---|
| 27/02/2015 | 21 municipios | Granizo + lluvias (ene–feb) | ~1.400 ha / 3.300 fam. | Papa, maíz, hortalizas, forraje | [ABI vía ReliefWeb](https://reliefweb.int/report/bolivia-plurinational-state/granizo-y-lluvias-afectan-1400-hect-reas-de-cultivos-en) |
| 02/02/2023 | Vacas (-17.60, -65.60) + Cono Sur | Sequía + heladas | Vacas 1.397 ha; departamento 34.435 ha (oct 2022 – feb 2023) | Papa (hasta −98 %), oca, maíz, trigo, avena | [Los Tiempos](https://www.lostiempos.com/actualidad/cochabamba/20230202/desastre-sequia-heladas-danan-98-cultivos-papa-cono-sur) |
| 08/07/2025 | Mizque (-18.04, -65.51) | Heladas | 180 ha, 18 comunidades | Papa, arveja, tomate | [Unitel](https://unitel.bo/noticias/economia/heladas-en-cochabamba-18-comunidades-y-180-hectareas-de-cultivos-afectados-IF16571922) |
| 18/11/2025 | Villa Tunari, Pojo, Puerto Villarroel, Totora | Riadas / inundaciones | 4.000 familias; 1.400 ha bajo el agua en Villa Tunari | Banano, yuca, piña, cítricos, arroz | [Opinión](https://www.opinion.com.bo/cochabamba/desborde-rios-riadas-inundaciones-dejan-4000-familias-cochabamba/20251118145745983797.html) |
| 06/01/2026 | Arque, Tapacarí, Cocapata, Toco | Granizadas | Arque 519 fam.; Toco ~700 fam.; Tapacarí >200 fam. | Papa (en floración), haba, trigo, maíz, cebada, avena | [Asamblea Leg. Dptal. 08/01/2026](https://asambleacochabamba.gob.bo/2026/01/08/granizadas-afectan-a-cuatro-municipios-del-departamento-de-cochabamba) |
| 09/03/2026 | Santiváñez (-17.57, -66.21) | Sequía | 233 ha / 733 fam. | Maíz | [Unitel](https://television.unitel.bo/portada/noticias/sequia-golpea-a-cultivos-y-ganado-de-cuatro-municipios-de-cochabamba-y-alistan-declaratoria-de-emergencia-AO19536710) |
| 09/03/2026 | Anzaldo (-17.82, -65.94) | Sequía | 955 ha / 1.180 fam. | Maíz, papa, arveja | ídem |
| 09/03/2026 | Totora (-17.59, -65.17) | Sequía | 5.936 ha / 2.404 fam. | Papa, maíz | ídem |
| 09/03/2026 | Pasorapa (-18.32, -64.68) | Sequía | ~2.100 ha / 943 fam. | Maíz, papa, tomate | ídem |
| 21–26/06/2026 | Mizque (-18.04, -65.51) | Heladas | 320 ha / 520 fam.; tomate −60 a −100 % | Tomate, papa, pimentón, arveja, durazno | [La Patria](https://lapatria.bo/enfoque-nacional/regiones/productores-enfrentan-crisis-frio-extremo) |

### 3.3 Patrones que se desprenden (hipótesis para validar con datos NASA)
- **Inundación y anegamiento**: dic–mar, por lluvias intensas concentradas; las torrenteras del Tunari y el río Rocha desbordan. La capa *Drenaje* permite marcar las parcelas expuestas.
- **Granizo**: nov–feb (inicio y pleno de la campaña de verano). El riesgo es mayor en el piedemonte (Tiquipaya, Tunari).
- **Heladas**: may–ago; afectan la papa temprana, las hortalizas y el maíz tardío.
- **Sequía**: (a) retraso en el inicio de las lluvias (oct–dic) que impide sembrar y (b) veranillos en ene–mar. Depende del nivel de **La Angostura**.
- La infraestructura de riego (represas y canales) no se coordina con el pronóstico: desborda en lluvias (canal Valverde, 2024) y falta agua en los meses críticos. **Es justo la necesidad que describe el reto.**

---

## 4. Agua de riego: infraestructura

| Sistema | Datos clave | Fuente |
|---|---|---|
| **Represa La Angostura** (Sistema Nacional de Riego N°1), Valle Alto | Inaugurada en 1945; capacidad de diseño 75 Mm³, reducida por sedimentación; riega Cercado, Quillacollo, Tiquipaya, Colcapirhua y Vinto (~4.500 productores); 430 km de canales. Niveles: 2,5 Mm³ (2016), 9 Mm³ (03/2023), 16 Mm³ = 18 % (07/2024), 60 % tras lluvias (12/2021) | [ReliefWeb 2016](https://reliefweb.int/report/bolivia-plurinational-state/la-angostura-se-seca-y-sube-disputa-por-agua) · [Unitel 2024](https://unitel.bo/noticias/economia/bajo-nivel-del-agua-de-la-represa-de-la-angostura-preocupa-a-regantes-de-cochabamba-CH12515052) · [Los Tiempos 2021](https://www.lostiempos.com/actualidad/cochabamba/20211229/fin-sequia-angostura-se-llena-al-60-su-capacidad) |
| **Proyecto Múltiple Misicuni** | En operación desde 2017. Fase II: 3.100 L/s (1.100 L/s para riego) → **2.837 ha** (zona Este 887, Central 1.166, Oeste 667) en Tiquipaya, Quillacollo y Colcapirhua. Fase III (en estudio): 2.100 L/s → 5.907 ha (+ Vinto, Sipe Sipe). Expertos UMSS lo ven como el respaldo ante El Niño | [Opinión 05/10/2022](https://www.opinion.com.bo/articulo/cochabamba/misicuni-asegura-que-atiende-agua-riego-mas-demanda/20221005222935882685.html) · [Opinión 07/09/2026](https://www.opinion.com.bo/cochabamba/nino-cochabamba-expertos-umss-explican-riesgo-sequias-falta-lluvias/20260907000222995810.html) |
| **Aguas residuales** (PTAR Alba Rancho, ríos Rocha y Tamborada) | En el D9 se riega con efluente y agua de río contaminados → riesgo sanitario en hortalizas de consumo crudo | [Aguatuya / Challacaba D9](https://www.musgroup.net/node/264) · [La Patria](https://lapatria.bo/enfoque-nacional/denuncia/en-cochabamba-contaminacion-en-canales-de-riego-genera-enfermedades-estomacales) |

**Implicación para el DSS:** el agricultor debe poder indicar su **fuente de agua** (Angostura, Misicuni, pozo, residual o solo lluvia) y su **turno de riego**. Esto cambia qué cultivos son viables, por ejemplo, nada de hortalizas de hoja con agua residual.

---

## 5. Clima base del punto D9 (NASA POWER, climatología)

Consulta: `https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M_MIN,T2M_MAX,PRECTOTCORR,FROST_DAYS,EVPTRNS&community=AG&longitude=-66.17&latitude=-17.46&format=JSON`

| | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lluvia (mm/día) | 3,4 | 3,4 | 1,8 | 0,7 | 0,2 | 1,5* | 0,2 | 0,3 | 0,4 | 0,8 | 1,2 | 2,8 |
| Días de helada | 0 | 0 | 0,1 | 0,1 | 2,2 | 3,0 | **6,3** | 2,9 | 0,2 | 0,1 | 0 | 0 |
| T mín. (°C) | 2,6 | 3,1 | −1,0 | −0,7 | −3,3 | −3,5 | **−4,3** | −3,6 | −1,3 | −0,8 | 1,8 | 2,5 |
| T máx. (°C) | 27,6 | 27,7 | 27,5 | 26,5 | 26,6 | 25,8 | 25,3 | 26,3 | 29,0 | 29,0 | 30,1 | 29,3 |

*Valor anómalo. La celda POWER (~0,5°) mezcla valle y montaña, así que probablemente hay sesgo frío; las temperaturas parecen extremos, no medias. Validar con SENAMHI (estación Aeropuerto Cochabamba).

### 5.1 Contexto climático actual: El Niño 2026–2027 ⚠️
- **UMSS (07/09/2026):** "100 % de certeza" de El Niño en ene–mar 2027, con probabilidad alta de que sea muy intenso. Históricamente trae **menos lluvia y sequía en los valles interandinos** ([Opinión](https://www.opinion.com.bo/cochabamba/nino-cochabamba-expertos-umss-explican-riesgo-sequias-falta-lluvias/20260907000222995810.html)).
- **Informe UMSS "El Niño 2026–2027 y riesgo de sequía en Bolivia" (21/10/2026):** déficit de lluvias y temperaturas sobre lo normal; los mayores impactos serán en **valles interandinos** y altiplano ([Los Tiempos](https://www.lostiempos.com/actualidad/pais/20261021/pronostican-riesgo-sequia-extrema-fenomeno-nino-2026-2027)).
- **CIPCA (31/07/2026):** pico de El Niño entre oct y dic de 2026; anomalías del Pacífico de hasta +3,5 °C. El Reporte Nacional de Sequías del SENAMHI (jun 2026) reporta **suelos extremadamente secos en los valles** ([CIPCA](https://cipca.org.bo/analisis-y-opinion/cipca-notas/bolivia-bajo-el-impacto-de-el-nino-2026-sequia-incendios-y-los-desafios-de-un-plan-de-prevencion-que-aun-no-despega)).

→ La campaña 2026–27 es un **caso de uso real** para el DSS: recomendar cultivos y rotaciones tolerantes a sequía y fechas de siembra según la humedad de suelo de SMAP y el pronóstico.

---

## 6. Suelos del área

| Tema | Hallazgo | Fuente |
|---|---|---|
| **Salinidad en el D9** | La salinización predomina en la parte central del D9; material parental **calcáreo** y **arcillas** | [Padilla Suárez, 1998](https://pesquisa.bvsalud.org/portal/resource/pt/biblio-1319054) |
| Salinidad por teledetección en el D9 | Tesis UMSS: conductividad eléctrica + **Sentinel-2** en el D9 → método replicable en el reto | [Vallejos Guzmán, UMSS](http://ddigital.umss.edu/handle/123456789/18852?mode=full) (el servidor no respondió; revisar) |
| Acuífero sur del valle | Vulnerable a contaminación por riego con aguas residuales | [Ghielmi 2008, UCB](https://investigacion.ucb.edu.bo/documentos/681cec6a5afe3d4f3517ed0e) |
| Hidrogeología del Valle Central | Abanicos aluviales del Tunari (gruesos, buen drenaje) → llanura central y sur (finos, drenaje lento) | [BGR](https://www.bgr.bund.de/EN/Themen/Grundwasser/Downloads/geology_hydrogeology_cochabamba_pdf.pdf?__blob=publicationFile&v=2) · [López 2023](https://www.researchgate.net/publication/373226391_MODELACION_HIDROGEOLOGICA_EN_EL_VALLE_CENTRAL_DE_COCHABAMBA-BOLIVIA) |

**Fuentes globales para el análisis (pendiente):** SoilGrids 250 m (textura, carbono orgánico, pH, densidad aparente y retención a 33 y 1500 kPa → agua disponible) y HWSD v2.
**Hipótesis previa:** norte (D13) con suelos más gruesos y buen drenaje; sur (D9, D15) con suelos finos, drenaje lento, riesgo de **salinidad y anegamiento**.

---

## 7. Caracterización de cultivos

### 7.1 Kc según FAO 56, Tabla 12 (clima subhúmedo estándar: HRmín ≈ 45 %, u2 ≈ 2 m/s)

| Cultivo | Kc ini | Kc mid | Kc end | Altura máx. (m) |
|---|---|---|---|---|
| Maíz grano | 0,30 | 1,20 | 0,60–0,35 | 2,0 |
| Maíz dulce (choclo) | 0,30 | 1,15 | 1,05 | 1,5 |
| Alfalfa (promedio de temporada) | 0,40 | 0,95 | 0,90 | 0,7 |
| Alfalfa (cada corte) | 0,40 | 1,20 | 1,15 | 0,7 |
| Papa | 0,50 | 1,15 | 0,75 | 0,6 |
| Haba (verde) | 0,50 | 1,15 | 1,10 | 0,8 |
| Haba (seca) | 0,50 | 1,15 | 0,30 | 0,8 |
| Arveja (verde) | 0,50 | 1,15 | 1,10 | 0,5 |
| Arveja (seca) | 0,50 | 1,15 | 0,30 | 0,5 |
| Avena / cebada | 0,30 | 1,15 | 0,25 | 1,0 |
| Trigo | 0,30 | 1,15 | 0,25–0,40 | 1,0 |
| Cebolla (seca) | 0,70 | 1,05 | 0,75 | 0,4 |
| Zanahoria | 0,70 | 1,05 | 0,95 | 0,3 |
| Lechuga | 0,70 | 1,00 | 0,95 | 0,3 |
| Repollo | 0,70 | 1,05 | 0,95 | 0,4 |
| Tomate | 0,60 | 1,15 | 0,70–0,90 | 0,6 |

Fuente: [FAO 56, Cap. 6](https://www.fao.org/4/x0490e/x0490e0b.htm). Las filas de hortalizas y leguminosas se verificaron contra la página. Las de cereales y forrajes se tomaron de la Tabla 12 y deben revisarse en el PDF ([x0490s](https://www.fao.org/3/x0490s/x0490s.pdf)).
Ajustar Kc mid con la Ec. 62 de FAO 56 según la HRmín y el viento locales; en Cochabamba el aire es seco en invierno, lo que eleva Kc.

### 7.2 Duración de etapas, FAO 56 Tabla 11 (días: inicial / desarrollo / media / final = total)

| Cultivo | Etapas | Total | Referencia FAO |
|---|---|---|---|
| Maíz grano | 30 / 50 / 60 / 40 | 180 | Abril, tierras altas de África oriental (la más parecida a valle andino) |
| Papa | 30 / 35 / 50 / 30 | 145 | Ene/Nov, clima semiárido |
| Haba / arveja | 20 / 30 / 35 / 15 | 100 | Mar/Abr, Mediterráneo |
| Cebada / avena / trigo | 15 / 30 / 65 / 40 | 150 | Julio, África oriental |
| Alfalfa | 10 / 20 / 20 / 10 (primer corte); 5 / 10 / 10 / 5 (cortes siguientes) | 60 / 30 | — |
| Cebolla seca | 20 / 35 / 110 / 45 | 210 | Oct, región árida |
| Zanahoria | 30 / 40 / 60 / 20 | 150 | Feb/Mar, Mediterráneo |
| Lechuga | 25 / 35 / 30 / 10 | 100 | Oct/Nov, región árida |

⚠️ Valores guía. Ajustar con observación local o curvas NDVI (MODIS/Sentinel-2).

### 7.3 Tolerancia a helada y sequía (referencial; validar con agrónomos o INIAF)

| Cultivo | Helada | Sequía | Fija N | Notas para la rotación |
|---|---|---|---|---|
| Maíz | Sensible | Media | No | Demanda alta de agua en floración (ene–feb); granizo |
| Papa | Sensible | Baja | No | Heladas tempranas y tardías; alto valor |
| Alfalfa | Tolerante (latencia) | Media-alta (raíz profunda) | **Sí** | Mejora la estructura del suelo; sensible a salinidad media |
| Haba | **Tolerante** | Media | **Sí** | Leguminosa de invierno ideal |
| Arveja | Moderada | Media | **Sí** | Ciclo corto |
| Avena / cebada | **Tolerante** | **Alta** | No | Cobertura invernal + forraje; cebada tolera salinidad |
| Vicia (con avena) | Tolerante | Media | **Sí** | Mezcla forrajera de cobertura |
| Tarwi | Moderada | **Alta** | **Sí** | Andino, suelos pobres |
| Quinua | Moderada | **Alta** | No | Tolera salinidad |
| Cebolla, zanahoria, lechuga | Moderada | Baja | No | Requieren riego fiable y **agua no residual** |
| Tomate | Muy sensible | Baja | No | Pérdidas de 60–100 % por helada (Mizque 2026) |

---

## 8. Calendario y prioridades del productor

### 8.1 Ventanas de siembra en el valle (dos campañas)

| Campaña | Siembra | Cosecha | Cultivos | Agua | Fuente |
|---|---|---|---|---|---|
| **Grande (verano)** | sep – nov (temporal: con las primeras lluvias, oct – dic) | feb – may | Maíz, papa, hortalizas | Lluvia + riego de apoyo | [PROINPA](https://www.proinpa.org/web/pdf/Papa/Abioticos/Conocimiento%20Local%20en%20el%20Cultivo%20de%20la%20Papa%20.pdf): papa oct–nov; papa de mediados de sep a inicios de oct según indicadores locales |
| **Chica / "mishka" (otoño-invierno)** | mar – abr (y jul–ago para papa temprana con riego) | jun – sep / nov–dic | Zanahoria, remolacha, papa, maíz, haba, cebolla; avena forrajera | **Riego obligatorio** | [Los Tiempos 30/03/2018](https://www.lostiempos.com/actualidad/economia/20180330/se-inicia-siembra-seis-cultivos-preven-subir-rendimiento-30) |

Riesgos por ventana: la siembra temprana (sep–oct) tiene riesgo de sequía si se retrasan las lluvias, como prevé El Niño 2026–27. La campaña chica tiene riesgo de helada (may–ago) y depende del turno de La Angostura o Misicuni.

### 8.2 Costos de semilla (pocos datos)
- **INIAF – Tarifario 2026** ([PDF](https://iniaf.gob.bo/wp-content/uploads/2026/01/TARIFARIO-2026.pdf)): costo de **certificación** en Bs (no es el precio de la semilla): haba, frejol, arveja y maní 250; maíz variedad 280; maíz híbrido 350; trigo y avena 200; otros 240. Sirve como proxy relativo.
- Semilla de papa: ofertas de hasta **Bs 450** (el doble de lo habitual) en El Alto ([F10 HD](https://www.facebook.com/F10HD/videos/elalto-la-semilla-de-papa-y-el-abono-suben-de-precio-en-el-mercado-boliviano-las/1271169080323717)); la unidad no está clara (¿quintal?).
- INIAF vende semilla prebásica y básica de papa (variedades Pinta Boca y otras).
- **Brecha:** no hay una tabla oficial de precios de semilla por cultivo en Cochabamba. Para el MVP, usar **costo relativo** (bajo, medio, alto), por ejemplo: avena y cebada bajo; haba, arveja y maíz medio; papa y hortalizas alto.

### 8.3 Uso y mercado
- Forraje (alfalfa, maíz forrajero, avena): demanda local estable.
- Choclo: venta en fresco (ene–mar).
- Hortalizas: mayor valor, pero requieren agua limpia y fiable.
- La Cámara Agropecuaria reporta problemas de diésel e insumos en 2026, lo que encarece la producción.

---

## 9. Pronóstico de lluvia a 7 y 14 días (módulo complementario)

| Fuente | Qué ofrece | Notas |
|---|---|---|
| **NASA GEOS-FP / GEOS-S2S** | Pronóstico global determinístico (~10 días) y subestacional | Fuente NASA; requiere procesar NetCDF |
| **NASA GPM IMERG Early/Late** | Lluvia observada casi en tiempo real (4–12 h de latencia) | Para el acumulado reciente; no es pronóstico |
| SENAMHI Bolivia | Pronóstico regional diario y boletines estacionales | [senamhi.gob.bo](https://senamhi.gob.bo/meteorologia/pronostico-regiones) · [Predicción JAS 2026](https://senamhi.gob.bo/meteorologia/boletines/tendencias/2026/07_BOLETIN_PREDICCION_JAS_2026.pdf) |
| Open-Meteo (GFS, ECMWF) | API JSON de 16 días por punto | No es NASA; fácil para el MVP |

---

## 10. Rotaciones a comparar (punto de partida)

| # | Rotación | Por qué | Riesgos y brechas |
|---|---|---|---|
| 1 | **Actual:** maíz (verano) → barbecho o avena (invierno) → alfalfa 3–5 años → maíz | Lo que hace hoy la mayoría (forraje) | Campo desnudo may–oct; maíz expuesto a sequía y granizo; alto consumo de agua |
| 2 | Maíz → **avena + vicia** (cobertura invernal) → **haba** → maíz | Cubre el suelo en la época seca, fija N, da forraje en invierno y corta ciclos de plaga | Necesita un riego en el establecimiento; helada en la vicia joven |
| 3 | **Cebada o quinua** → **tarwi o haba** → papa (solo con agua limpia) | Tolerancia a sequía y salinidad, adecuada para un año El Niño; las leguminosas restauran N | Mercado de quinua y tarwi; la papa exige agua fiable y es sensible a helada |
| 4 | Alfalfa → **hortalizas de ciclo corto** (cebolla, zanahoria) en la campaña chica | Mayor ingreso | Solo con riego fiable y **no residual**; demanda de agua alta |

Cada rotación debe evaluarse con: Kc × ET0 (demanda hídrica) frente a lluvia y humedad SMAP; días de helada en sus etapas sensibles; balance de N; meses de suelo desnudo (erosión); costo relativo de semilla; y adecuación al agua disponible.

---

## 11. Brechas de información
- No hay una capa GAMC de cultivos ni de parcelas: se necesitan NDVI o clasificación, o que el agricultor dibuje su parcela.
- No hay datos de rendimiento local por cultivo (SIIP/INE para Cercado no cargó; revisar el [SIIP municipal](https://siip.produccion.gob.bo/repSIIP2/formulario_mdryt2.php)).
- No hay estaciones in situ para validar POWER, SMAP e IMERG; pedir datos a SENAMHI o UMSS.
- Faltan precios de semilla y de venta por cultivo.
- No hay calendario oficial de turnos de riego de La Angostura ni de Misicuni.
