# Área de estudio acordada para IMERG

`cochabamba-estudio.geojson` es un Polygon GeoJSON WGS84 (longitud, latitud),
construido con la extensión espacial de la ficha **Límite Distritos** de GAMC
(service_id `7eb13092-bf0e-493b-aae6-03c43eedda2c`):
`[-66.280703, -17.531190, -66.069520, -17.257306]`.

Se adopta explícitamente como rectángulo de estudio para avanzar con la selección
de celdas IMERG. 
Incluye áreas fuera de los polígonos municipales y distintos usos de suelo.
Las fracciones de celda se refieren a este rectángulo, no a superficie cultivada.

Periurbano describe una transición ciudad–campo que puede mezclar cultivos,
viviendas y terrenos en urbanización. No se debe excluir automáticamente toda
esa clase ni considerar agrícola todo lo que queda fuera de ella. Las parcelas
deben confirmarse con el agricultor u otra fuente de cobertura validada.

Para recortar el mes descargado, desde `imerg/`:

```bash
.venv/bin/python imerg.py process --folder data/raw/final --polygon areas/cochabamba-estudio.geojson --database data/cochabamba-distritos-v2.sqlite --run final
.venv/bin/python imerg.py report --database data/cochabamba-distritos-v2.sqlite --start 2025-01-01 --end 2025-01-31 --output data/cochabamba-distritos-v2-coverage.json
.venv/bin/python imerg.py export --database data/cochabamba-distritos-v2.sqlite --output data/cochabamba-distritos-v2-2025-01.csv
```

Cuando cambie el polígono, usar una base nueva y volver a recortar. Conservar el
identificador del área junto al CSV al compartirlo con POWER y SMAP.
