# Lluvia diaria GPM IMERG

## Área y periodo confirmados

Se creó el área aproximada
[`areas/cochabamba-estudio.geojson`](areas/cochabamba-estudio.geojson) a partir del
BBOX de la ficha Límite Distritos GAMC (área v2). Permite avanzar sin esperar
un límite oficial; no identifica terrenos agrícolas. Véanse los comandos y
limitaciones en [`areas/README.md`](areas/README.md). Los pasos que usan
`area-oficial.geojson` más abajo corresponden a la alternativa con límite oficial.

## Estado real del trabajo

- Investigación y programa preparados para IMERG Final y Late diarios, colección 07.
- Catálogo público real consultado: enero de 2025 tiene 31 archivos Final, revisión V07B.
- El manifiesto de esos archivos está en `samples/catalog-final-2025-01.json`.
- Primer archivo NASA descargado y validado: 2025-01-01, Final V07B, lluvia en
  mm/day y conteo de intervalos válidos. Falta el polígono oficial compartido para
  validar el recorte territorial y ejecutar el histórico. No se inventaron precipitaciones.
- No se incluyó un rectángulo como supuesto perímetro oficial.

## Ficha de investigación

| Campo | Descripción |
|---|---|
| Fuente | NASA GPM, algoritmo IMERG; distribución GES DISC |
| Histórico | `GPM_3IMERGDF`, colección `07`, Final diario |
| Reciente | `GPM_3IMERGDL`, colección `07`, Late diario |
| Periodo solicitado | 2016-01-01 a 2025-12-31, 3653 días |
| Variable principal | `precipitation`, mm/day; el programa verifica las unidades internas |
| Interpretación V07 | Tasa media de las observaciones válidas expresada para un día; con observaciones incompletas no equivale necesariamente a un total observado completo |
| Resolución | 0.1° × 0.1°, aproximadamente 11 km; no es una medición de cada parcela |
| Día | UTC. No se convierte a día civil boliviano: hacerlo requiere datos subdiarios |
| Formato | NetCDF4, coordenadas lat/lon originales |
| Calidad | Conserva `precipitation_cnt` y otros indicadores presentes, con sus unidades; no inventa los ausentes |
| Autenticación | Catálogo CMR público; descarga protegida con NASA Earthdata Login |
| Versionado | Colección 07; revisión real del archivo, por ejemplo V07B, almacenada en cada fila |

IMERG estima precipitación mediante observaciones satelitales. Final incorpora
ajustes con pluviómetros y se publica con mayor demora; Late prioriza actualidad.
No son pronósticos. La lluvia por sí sola no determina inundación, germinación,
disponibilidad de riego ni qué cultivo conviene.

## Instalación y primer uso

Desde la carpeta `field-shift-challenge/imerg`:

En este equipo ya quedó instalado `.venv`. Para probar primero un solo día (~27 MB):

```bash
.venv/bin/python imerg.py download --manifest samples/catalog-final-2025-01-01.json --folder data/raw/final
```

Para instalarlo desde cero en otro equipo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python imerg.py --help
```

En Debian/Ubuntu, si falta `venv`, instalar primero el paquete `python3-venv`
con el administrador del equipo. No guardar contraseñas en código, chats o Git.

### 1. Consultar un mes, sin iniciar sesión

```bash
python imerg.py catalog --start 2025-01-01 --end 2025-01-31 --run final --bbox -66.28 -17.53 -66.05 -17.26 --output data/sample-manifest.json
```

**Ese BBOX es únicamente un filtro de búsqueda aproximado**, obtenido del contexto
local. CMR devuelve archivos globales que lo intersectan; no recorta la descarga.
La muestra consultada indica unos 27 MB por día global: el mes ronda 0.8 GB y diez
años pueden rondar 100 GB. El recorte local reduce el resultado, no la transferencia.
Para conexiones limitadas conviene evaluar el subsetting remoto de GES DISC antes
de ejecutar la descarga completa. Este programa usa descargas globales reproducibles.

### 2. Descargar (inicio de sesión en tu terminal)

```bash
python imerg.py download --manifest data/sample-manifest.json --folder data/raw/final
```

Se solicitan las credenciales interactivamente, sin persistirlas. Si NASA solicita
autorizar la aplicación GES DISC, completar ese paso en Earthdata. La descarga
debe terminar con un NetCDF válido; archivos incompletos no se marcan como listos.

### 3. Recortar usando el archivo territorial de Willy

Guardar su polígono oficial como `data/area-oficial.geojson`, en WGS84, orden
**longitud, latitud**. Debe documentar su fuente y fecha. Se aceptan Polygon,
MultiPolygon, Feature o FeatureCollection de polígonos.

```bash
python imerg.py process --folder data/raw/final --polygon data/area-oficial.geojson --database data/rain.sqlite --run final
python imerg.py report --database data/rain.sqlite --start 2025-01-01 --end 2025-01-31 --output data/coverage-sample.json
python imerg.py export --database data/rain.sqlite --output data/rain.csv
```

Se conserva cada celda que intersecta el polígono, incluyendo intersecciones donde
su centro cae afuera. `area_fraction` es fracción de la celda dentro del área,
calculada en grados cuadrados: aproximación local, no hectáreas ni ponderación
geodésica exacta. No se interpola a parcelas ni se modifica la malla original.

### 4. Histórico, después de validar el mes

```bash
python imerg.py catalog --start 2016-01-01 --end 2025-12-31 --run final --bbox -66.28 -17.53 -66.05 -17.26 --output data/history-manifest.json
python imerg.py download --manifest data/history-manifest.json --folder data/raw/final
python imerg.py process --folder data/raw/final --polygon data/area-oficial.geojson --database data/rain.sqlite --run final
python imerg.py report --database data/rain.sqlite --start 2016-01-01 --end 2025-12-31 --output data/coverage-history.json
```

El manifiesto informa fechas ausentes del catálogo. El informe de la base informa
huecos por fecha/celda conocida, valores nulos y días con menos de 48 observaciones
de media hora. **No considera lluvia cero un dato faltante.** Revisar ambos informes;
una celda que nunca apareció no se puede inferir desde la base.

### 5. Actualización semanal

```bash
python imerg.py update --root data/updates --polygon data/area-oficial.geojson --database data/rain.sqlite
```

Reconsulta los últimos 14 días de Late y 210 de Final (ventanas ajustables), descarga
archivos nuevos o revisados y actualiza la base. La primera ejecución puede transferir
varios GB. Si hay interrupciones largas o una revisión anterior a esa ventana, volver
a consultar el periodo afectado. Puede solicitar login para cada ejecución/producto.
Para automatizar sin terminal, configurar localmente el método de autenticación de
earthaccess y adaptar `login`; no se instaló ningún cron ni se almacenaron credenciales.

La clave primaria evita duplicar una misma fecha/celda/producto/revisión. Late y Final
se conservan separados para auditoría. La vista `preferred_rain` y el CSV priorizan
Final válido sobre Late **de la misma revisión**; un Final nulo no oculta Late válido.
No se mezclan silenciosamente revisiones diferentes. Cambiar de perímetro requiere
una base nueva para no conservar celdas del perímetro anterior.

## Uso para el equipo

`rain.csv` contiene fecha UTC, fuente, producto, revisión, ejecución, celda, latitud,
longitud, fracción territorial, variable, valor, unidad, calidad, fecha de descarga y
archivo fuente. La aplicación puede relacionar estas celdas con zonas agrícolas.
El equipo debe acordar la agregación espacial con SMAP y POWER antes de entrenar.
Estos datos ambientales no aportan etiquetas de rendimiento o éxito de cultivos.

## Fuentes oficiales

- [IMERG y sus ejecuciones](https://gpm.nasa.gov/data/imerg).
- [Final diario V07: definición y variables](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary).
- [Late diario V07](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDL_07/summary).
- [Documentación técnica V07](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation).
- [Catálogo CMR: API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
- [earthaccess: acceso y descarga](https://earthaccess.readthedocs.io/en/stable/user/explanation/access/).
- [Crear o gestionar cuenta Earthdata](https://urs.earthdata.nasa.gov/).

## Verificación

```bash
python -m unittest discover -s tests -v
```

Las pruebas crean **datos sintéticos**, identificados como tales, para verificar
recorte, valores ausentes, calidad y repetición sin duplicados. No sustituyen una
validación con archivos NASA autenticados. Véase `VALIDACION.md` para el estado.
