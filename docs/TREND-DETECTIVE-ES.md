# Be An Earth System Trend Detective! — Transcripción fiel al español

> Fuente oficial: https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective
> Evento: NASA Space Apps Challenge 2026 · Dificultad: **Advanced** · Temas: Earth Science, Software
> Traducción de referencia del equipo (no oficial de NASA).

## Enunciado del reto

El cambio ocurre siempre en el sistema ambiental interconectado de la Tierra, y cuando se
desarrolla en una dirección consistente —que aumenta o disminuye, que se eleva o cae, que
se engrosa o adelgaza— las variables medidas lo reflejan. Pero una variable de datos de
ciencias de la Tierra puede presentar una tendencia en un sentido en una región y en el
sentido opuesto en otra, **incluso cuando el mismo proceso impulsa ambas**. La multitud de
variables de datos de ciencias de la Tierra hace difícil seleccionar variables que puedan
indicar cambio, y luego realizar un análisis sobre las variables seleccionadas.

**Vuestro reto es crear una herramienta que pueda:** seleccionar variables medidas por
misiones de ciencias de la Tierra o producidas por modelos de ciencias de la Tierra,
visualizar cómo cambian con el tiempo, y determinar **qué** está cambiando, **dónde** está
cambiando, **cuánto** está cambiando, y si estos cambios son lo que los científicos llaman
«significativos».

## Antecedentes (Background)

Los instrumentos en satélites observan muchos aspectos diferentes del sistema terrestre:
en la tierra, en la atmósfera y en los océanos. Los modelos globales también utilizan
datos de instrumentos satelitales y otros tipos de datos para examinar y analizar el
sistema terrestre. Una razón importante para hacer esto es observar y caracterizar los
cambios en el sistema terrestre. Los cambios —especialmente los que avanzan en una
dirección particular a lo largo del tiempo, es decir, una **tendencia**— indican tanto los
procesos que causan dichos cambios como los procesos que responderán a ellos.

Un factor que complica este trabajo es la gran variedad de variables que se pueden
estudiar. Otro es que los cambios en una variable concreta pueden avanzar en una dirección
en una región y en la dirección opuesta en otra, ¡incluso cuando ambas tendencias son
provocadas por el mismo proceso! Por lo tanto, hay dos partes importantes en este
problema:

1. **Encontrar variables que presenten tendencias**, desde las simples como temperatura y
   precipitación hasta otras más complejas como evaporación o caudal (streamflow).
2. **Analizar las tendencias en regiones particulares** de la tierra, el océano, o incluso
   niveles de la atmósfera.

Instrumentos como **MODIS** (Moderate Resolution Imaging Spectroradiometer), **OMI**
(Ozone Monitoring Instrument), **AIRS** (Atmospheric Infrared Sounder) y **GPM** (Global
Precipitation Measurement) proporcionan variables analizables. Los modelos globales —en
particular **MERRA-2** (Modern Era Retrospective analysis for Research and Applications,
Version 2) y **GLDAS** (Global Land Data Assimilation System)— proporcionan muchas más.
Encontrar, analizar y relacionar tendencias significativas con los procesos que las causan
es uno de los usos más importantes de los datos de las ciencias de la Tierra de la NASA.

## Objetivos

Una respuesta exitosa a este reto reunirá varios elementos importantes:

1. **Identificar variables de interés** de las ciencias de la Tierra que puedan
   investigarse en busca de tendencias potenciales. Como señalan los Antecedentes, la
   NASA y otras agencias espaciales ofrecen numerosas variables, algunas familiares y
   otras más especializadas para usos de ramas particulares de la ciencia.
2. **Adquirir las variables de datos para una región particular**, ya que la mayoría de
   las tendencias en los datos no serán globales —aunque algunas pueden serlo—.
3. **Generar y visualizar una serie temporal** para la variable y la región de interés
   durante un periodo suficientemente largo que permita el análisis estadístico.
4. **Realizar un análisis estadístico básico** de esa serie temporal, indicando la **tasa
   de cambio en el tiempo**, y **probar la significancia de la tendencia** usando métodos
   como la prueba t, la prueba de Mann-Kendall, o intervalos de confianza.

Los sitios de datos ofrecen herramientas que generan series temporales, y los paquetes de
análisis estadístico proporcionan pruebas de significancia básicas. **Una respuesta que
haga tanto la visualización como el análisis cubre el alcance completo de este reto.**

## Consideraciones potenciales

*(Puedes —pero no estás obligado a— considerar lo siguiente:)*

### Público

* Este reto involucra datos científicos y análisis estadístico, por lo que el público
  probablemente sean estudiantes de secundaria y universitarios, junto con personas con
  algún bagaje científico.
* Proporcionar definiciones simples de las variables ayudaría considerablemente a estos
  usuarios.
* El concepto es ayudar a los usuarios a **convertirse en detectives de datos**: encontrar
  variables de interés y luego determinar si esas variables muestran una tendencia y si
  esa tendencia es significativa.

### Enfoque

* Los usuarios podrían responder a una **breve serie de preguntas** sobre qué o dónde les
  gustaría investigar, y las respuestas permitirían buscar variables de datos
  relacionadas. Sería muy útil proporcionar **un par de ejemplos de demostración** que el
  usuario pueda observar y que le ayuden a entender cómo funciona la herramienta.
* Aunque no es obligatorio, la **IA podría ser útil aquí** para identificar datos con
  potencial de mostrar tendencias en áreas particulares, apoyándose en artículos de
  noticias y papers de investigación, o en las características de una región como un
  desierto, una selva tropical, un estuario de mareas, o la atmósfera sobre una gran
  ciudad.

### Trabajo con los datos

* Los datos de ciencias de la Tierra están disponibles en varias resoluciones temporales
  —horaria, cada 3 horas, diaria y mensual—. Para este reto, **los datos diarios y
  mensuales son probablemente los más fáciles de procesar**.
* Encontrar una tendencia es interesante incluso si no alcanza el nivel de
  significancia. A veces todo lo que necesita una tendencia para volverse significativa
  es **un periodo más largo** para adquirir los datos.
* Considera buscar herramientas públicas de graficación de datos hidrológicos ofrecidas
  por organizaciones externas como el **CUAHSI** (Consortium of Universities for the
  Advancement of Hydrologic Science, Inc.).
* El análisis de tendencias con datos de ciencias de la Tierra puede ser complejo. Las
  tendencias pueden ser **no lineales**, y algunas no son evidentes a menos que se
  eliminen los ciclos regulares, como el ciclo estacional. Los análisis de tendencias más
  complejos están más allá del alcance previsto para este reto; **detectar y analizar
  tendencias lineales sería un gran comienzo**.

## Recursos oficiales del reto (pestaña Resources)

### Datos y recursos NASA

- **Giovanni** — herramienta versátil con menús de numerosas variables de datos; permite
  generar y descargar series temporales. (https://giovanni.gsfc.nasa.gov/giovanni/)
- **Hydrology Time Series** — generación de series temporales con datos hidrológicos.
- **AppEEARS** — acceso y transformación simple de datos geoespaciales de varios
  archivos federales de EE.UU.; incluye generación de series temporales.
  (https://appeears.earthdatacloud.nasa.gov/)
- **Climate Data Online (CDO)** — acceso gratuito al archivo de NOAA/NCDC de datos
  históricos globales de clima y meteorología, con historial de estaciones y herramienta
  de mapas. (https://www.ncdc.noaa.gov/cdo-web/)
- **Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced
  Coastal Regions** — artículo de investigación que demuestra la creación de series
  temporales y pruebas de significancia.

### Recursos de agencias espaciales asociadas

- **KNMI Climate Explorer** (Instituto Meteorológico Real de los Países Bajos) —
  herramienta web científica para explorar, analizar y visualizar datos climáticos de una
  amplia gama de fuentes. (https://climexp.knmi.nl/)
- **Artículo: métodos de pruebas estadísticas para detectar tendencias en series
  temporales.**
- **Artículo: guía completa de significancia estadística.**
- **CSA (Agencia Espacial Canadiense):**
  - **RADARSAT Constellation Mission (RCM) — datos**: trío de satélites de observación
    terrestre (día/noche, cualquier clima); vigilancia marítima (hielo, viento
    superficial, contaminación por petróleo y monitoreo de barcos), gestión de
    desastres, y monitoreo de ecosistemas (agricultura, humedales, bosques y cambios
    costeros).
  - **Geo.ca** — fuente definitiva de información geoespacial abierta de Canadá.
  - **Misión SWOT — información**: misión NASA/CNES con CSA y UK Space Agency que
    releva el ~90 % del agua superficial de la Tierra, midiendo cambios en la elevación
    de la superficie del agua de lagos, ríos, embalses y océanos a lo largo del tiempo.
  - **Monitoreo y protección del ecosistema desde el espacio** — sitio informativo.
  - **Tutorial de Python para SAR (Radar de Apertura Sintética)** — pasos prácticos
    sencillos de acceso y visualización con Python y QGIS.

## Nota del equipo (contexto GAMC)

En el portal del GAMC, el **Proyecto 01 — «Microclimas Urbanos con IA»** es el asociado a
este reto: 5 servicios WMS (catalogados en `docs/recursosgamc/01-be-an-earth-system-trend-detective.md`)
más el descargable **Red MÓNICA** (datos continuos de 2 estaciones terrestres de tráfico/
ambiente en Av. 6 de Agosto y Av. Circunvalación). Ver:
<https://recursosgamc.cochabamba.bo/api-doc> — proyecto 01.
