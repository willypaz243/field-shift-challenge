# Contexto local a fondo — Valle de Cochabamba y datos GAMC

> Exploración del 14/11/2026. Incluye pruebas en vivo del servicio WMS del GAMC y verificación
> web de la actividad agrícola en las zonas cubiertas.

## 1. El reto + enfoque local

El reto pide una **herramienta de apoyo a la decisión** para que los agricultores exploren
**rotaciones de cultivos** que mejoren salud del suelo y resiliencia climática, combinando:
observaciones NASA + suelos/cultivos locales + prioridades del agricultor, y comparando
**≥3 estrategias (incluida la actual)** con evidencia, brechas y riesgos de revisión local.

**Enfoque local elegido:** el GAMC (Gobierno Autónomo Municipal de Cochabamba) asignó al
proyecto 04 del su portal la capa territorial del **municipio de Cochabamba (Cercado)** con
foco en sus **zonas periurbanas** — justo la interfaz donde la agricultura del valle está
siendo presionada por la expansión urbana. Ese es el ángulo diferenciador.

## 2. Datos que nos dan (verificados en vivo, WMS 1.1.1 del GAMC)

Endpoint: `https://serviciosgamc.cochabamba.bo/api/gs/wms` · API key del proyecto 04 en
[DATA-SOURCES.md](./DATA-SOURCES.md). Acceso: solo lectura · GetMap, GetLegendGraphic y GetFeatureInfo probados con HTTP 200.

### Capa 1 — Periurbanos (`c52066a1-…238f`, categorizada)
Clases confirmadas por leyenda y GetFeatureInfo:
- **«Periurbanos en crecimiento»** (verde) — detalle: *«Herbazales ralos con intervención
  urbana»*, *«Arbustales ralos con herbazales e intervención urbana»*
- **«Periurbanos consolidados»** (salmón) — detalle: *«Periurbano»*

El mapa muestra la mancha periurbana del valle: consolidada en el corredor oeste-centro y
sectores noroeste; **en crecimiento** en parches al sur, suroeste y bordes este. Es
efectivamente el registro de la **frontera urbano-agrícola**.

### Capa 2 — Drenaje e Influencia (`d4cea6e3-…886`)
Red hidrográfica con atributos `Tipo` y `Clasificación`:
- `Tipo 1` — río principal (sistema del río **Rocha**)
- `Tipo 2` — **Principales Tributarios**
- `Tipo 3` — **Quebradas** (flujo estacional desde la cordillera Tunari)

Útil para: contexto de riego, riesgo de erosión/encajonamiento, y zonas de recarga.

### Capa 3 — Límite Distritos (`7eb13092-…da2c`)
Polígonos con `Distrito` (D1–D15) y `Comuna`. Comunas detectadas por sondeo: **Itocta,
Tunari, Molle, Valle Hermoso, Tamborada** (son los distritos periurbanos/rurales del Cercado,
al norte y oeste del núcleo urbano).

### Limitaciones (para no prometer de más)
- Solo 3 capas municipales, **no hay capa de cultivos ni de suelos** en el catálogo GAMC.
- Raster PNG + GetFeatureInfo puntual: sin descarga vectorial de polígonos.
- La API key viaja en la URL (evitar publicarla; ofuscarla al desplegar la demo).

## 3. Geografía y clima de la zona de análisis

- **Valle de Cochabamba**: ~2.500–2.700 m s.n.m., rodeado por la **cordillera Tunari** (norte,
  hasta ~4.500 m) y serranías al sur. Clima **semiárido subhúmedo**.
- **NASA POWER (punto 17.40°S, 66.15°O, celda ~3.100 m que cubre valle + faldeos)** —
  climatology:

| Mes | T mín (°C) | Lluvia (mm/mes) |
|---|---|---|
| Ene | 2,6 | 102 |
| Feb | 3,1 | 104 |
| Mar | −0,9 | 54 |
| Abr | −0,7 | 20 |
| May | −3,2 | 6 |
| Jun | −3,5 | 44 |
| Jul | −4,3 | 5 |
| Ago | −3,6 | 8 |
| Sep | −1,3 | 12 |
| Oct | −0,8 | 24 |
| Nov | 1,8 | 36 |
| Dic | 2,5 | 85 |

**Patrón confirmado:** estación húmeda dic–feb (~100 mm/mes), **estación seca y de heladas
may–sep** (T mín medias bajo cero en la celda; en el piso del valle la frecuencia real de
heladas es menor, pero May–Ago es el periodo crítico y conocido de heladas del valle).
Nota metodológica: la celda POWER mezcla piso de valle y faldeos de la Tunari; para la app,
POWER da la señal regional y el refinamiento por zona lo aportan ECOSTRESS/Landsat o los
relatos locales. Los "veranos de invierno" (olas de calor + sequía de mayo–ago) y El Niño
(alerta roja declarada sep-2026) acentúan el estrés hídrico.

## 4. ¿Hay cultivos en estas zonas? — verificación web

**Sí, y es una agricultura de proximidad significativa.** Evidencia:

### Estadísticas oficiales — SITAP (Min. Producción, municipio Cercado Cochabamba)
Fuente: <https://siip.produccion.gob.bo/atlas/COCHABAMBA.php?cod_mun=31201> — principales
cultivos del municipio:
- **Papa**: 26.544 Tm en 2.396 ha (el cultivo líder)
- **Trigo**: 5.320 Tm en 4.341 ha
- **Maíz en grano**: 2.240 Tm en 1.197 ha
- **Papaliza**: 1.134 Tm (cultivo altoandino de altura, típico de zonas Tunari/Itocta)

### Los municipios y distritos del valle metropolitano
- **Sacaba** — el municipio que más **papa** aporta; también maíz y hortalizas
  (Opinion.com.bo, 2018).
- **Tiquipaya** — **hortalizas** (lechuga, zanahoria, repollo), maíz, alfalfa y vocación
  **floricultora** (margaritas, claveles).
- **Sipe Sipe / Quillacollo** — maíz, verduras, trigo, avena; zonas Paucarpata, Illatacu y
  El Paso: hortalizas, papa y flores (Los Tiempos, 2017).
- **Distrito Tunari (Cercado)** — registro WOCAT de tecnologías agrícolas: uso de tierra
  **cultivos y pastoreo**, clima semiárido subhúmedo
  (<https://wocat.net/documents/119/SP_Part_2_donde_la_tierra_es_mas_verde.pdf>).
- **Valle Alto** (Punata, Tarata…) — maíz, papa, trigo y hortalizas, bajo estrés por
  sequías recurrentes (Cocha Abierta, mar-2026).

### El problema local que conecta con el reto
- Estudios **1962–2016** (Cabrera & De la Fuente, CIDES-UMSA): la huella urbana del valle
  central y Sacaba creció sobre tierras agrícolas, con **pérdida estimada >500 ha/año de
  tierras cultivables** en la región metropolitana (Diario Opinión/ANF).
- La expansión urbana ocupa **acuíferos y suelos agrícolas**, amenazando la
  sostenibilidad hídrica (Diario Opinión, 2023).
- Riesgos climáticos recurrentes del valle: **heladas, granizadas, sequía** (ReliefWeb 2018,
  CAC 2026) — el granizo daña maíz y papa (Quillacollo 2021).
- Potencial: Cochabamba tiene el **mayor potencial agrícola por ha del país** (~4.870 USD/ha,
  Andersen et al., SDSN Bolivia) — proteger y rotar bien estas tierras periurbanas tiene
  retorno alto.
- Marco nacional: *Guía Nacional para la Agricultura Urbana y Periurbana* (2025,
  oopp.gob.bo) reconoce las áreas agrícolas periurbanas como categoría de planificación.

## 5. Síntesis: qué significa esto para el producto

1. **Narrativa real, no hipotética:** el usuario objetivo es el productor periurbano del
   Cercado (Itocta, Tunari, Valle Hermoso, Tamborada, Mauma…) que ve cómo se urbaniza el
   valle y necesita que su chacra **siga siendo productiva y rentable**.
2. **Cultivos reales para la tabla de rotación:** papa, maíz, trigo, papaliza, hortalizas
   (lechuga, zanahoria, repollo), alfalfa, flores + candidatos de rotación: haba, quinua de
   valle, tarwi/chocho, avena forrajera, cebolla, durazno (agroforestería). Atributos:
   uso de agua, fijación de N (haba/tarwi/alfalfa), profundidad de raíz, ciclo, valor de
   mercado local.
3. **Datos GAMC como "capa de presión urbana + agua":** los campos sobre «periurbanos en
   crecimiento» son los más amenazados de conversión → la herramienta puede priorizar
   rotaciones que **maximicen productividad a corto plazo** ahí, y rotaciones de **salud de
   suelo a largo plazo** en zonas consolidadas con menos presión.
4. **Datos NASA como evidencia climática:** POWER (heladas may–ago, lluvia dic–feb),
   GPM (granizadas/extremos), SRTM (faldeos erosionables hacia las quebradas Tipo 3),
   ECOSTRESS/Landsat (estrés térmico e NDVI por campo).
5. **Restricción honesta para el pitch:** los suelos finos no están en el catálogo GAMC ni
   SSURGO (EE.UU.) → usar **SoilGrids/FAO GAEZ** + conocimiento local declarado por el
   agricultor en la app (inputs manuales de su suelo), alineado con el enunciado del reto
   ("farmer priorities and constraints").

## Fuentes web principales

- SITAP Cochabamba (Cercado): <https://siip.produccion.gob.bo/atlas/COCHABAMBA.php?cod_mun=31201>
- Expansión urbana y pérdida de tierras agrícolas (valle central + Sacaba, 1962–2016): <https://www.researchgate.net/publication/343237010>
- >500 ha/año perdidas (región metropolitana): Diario Opinión / ANF (2021–2023)
- WOCAT Tunari: <https://wocat.net/documents/119/SP_Part_2_donde_la_tierra_es_mas_verde.pdf>
- Sacaba papa / Tiquipaya flores: <https://www.opinion.com.bo/cochabamba/sacaba-es-municipio-ofrece-m-aacute-s-cantidad-papa/20180416195400610713.html>
- Quillacollo productivo: <https://www.lostiempos.com/actualidad/local/20170912/quillacollo-productivo-pujante>
- Potencial agrícola Bolivia (SDSN): <https://sdsnbolivia.org/wp-content/uploads/2024/01/AgriculturalPotentialBolivia.pdf>
- Guía Nacional AUP 2025: <https://www.oopp.gob.bo/wp-content/uploads/2025/10/WEB-GUIA-NACIONAL-PARA-LA-AGRICULTURA.pdf>
