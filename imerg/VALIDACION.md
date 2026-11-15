# Estado de validación — 14 de noviembre de 2026

## Evidencia real de NASA

Consultado el catálogo CMR mediante HTTPS, con producto, colección 07, periodo y
BBOX aproximado de Cochabamba. Se guardaron manifiestos reducidos, sin credenciales:

- `samples/catalog-final-2025-01.json`: 31 archivos Final, sin fechas faltantes.
- `samples/catalog-final-2025-01-01.json`: primer día para probar con ~27 MB.
- `samples/catalog-late-2025-01-01.json`: un archivo Late; confirma la nomenclatura
  `3B-DAY-L.MS.MRG.3IMERG...V07B.nc4`.

Estos manifiestos son metadatos reales, no contienen valores de lluvia ni prueban
la cobertura del recorte. Los archivos catalogados son globales.

## Pruebas del programa

Entorno local `.venv` instalado y probado con Python 3.13, earthaccess 0.19.0,
xarray 2026.9.0, netCDF4 1.7.5.1.post1 y shapely 2.2.0.

Cinco pruebas automatizadas con NetCDF **sintéticos**:

1. Intersección de celdas cuyos centros caen fuera del polígono; repetición sin
   duplicados, lluvia cero, nulos y conteo de observaciones.
2. Prioridad de Final válido y uso de Late cuando Final es nulo.
3. Rechazo de unidades inesperadas, para evitar errores de mm/h frente a mm/día.
4. Rechazo de geometrías no poligonales.
5. Dos ejecuciones del flujo de actualización con catálogo y descarga simulados,
   comprobando que no se duplican las filas.

## Pendientes que impiden declarar terminada la entrega de datos

- Enero de 2025 descargado: **31 de 31 archivos**, sin fechas faltantes ni archivos
  inválidos en la comprobación. Se verificaron fecha interna, unidad mm/day y
  lectura de valores no negativos o nulos en celdas cercanas a Cochabamba.
  Evidencia: `samples/validation-final-2025-01.json`. Esto no valida todavía el
  recorte territorial oficial ni la exactitud frente a estaciones meteorológicas.
- Primer archivo real descargado y abierto correctamente tras aceptar EULA.
- Validado: fecha 2025-01-01 UTC, Final V07B, variable `precipitation` en
  `mm/day`, malla de 3600 longitudes y 1800 latitudes (0.1°).
- Calidad real disponible: `precipitation_cnt`, `precipitation_cnt_cond`,
  `randomError` (mm/day) y `randomError_cnt`, entre otras variables.
- Ejemplo real de celda: centro lat -17.45, lon aproximadamente -66.15;
  precipitación aproximadamente 0.74 mm/day, con 48 intervalos válidos.
  No es una medición de parcela ni un promedio municipal.
- Willy debe proporcionar el polígono oficial WGS84 con su procedencia.
- Validar juntos un mes recortado; luego ejecutar el histórico 2016–2025.
- Ejecutar dos actualizaciones con NASA real y revisar sus informes de cobertura.
- Decidir descarga global frente a subsetting remoto según conexión y espacio.

No se ha entrenado un modelo ni se ha activado un proceso semanal automático.
