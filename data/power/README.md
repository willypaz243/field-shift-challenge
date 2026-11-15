# Datos NASA POWER descargados (ETL tarea 1.1)

> Generados el **14/11/2026** con [`src/etl/power_etl.py`](../../src/etl/power_etl.py)
> (API v2.10.3, **sin token**, `community=ag`).

## Contenido

Por cada zona de [`src/etl/points.json`](../../src/etl/points.json) (10 zonas):

- `{zone_id}_daily.csv` — serie diaria 1984-01-01 → 2025-12-31 (15,342 filas)
- `{zone_id}_meta.json` — lat/lon/elev_m, rangos, n.º de filas

Columnas CSV: `fecha, tmean, tmin, tmax, t2mdew, rh, ws, ps, pmm, sw, sw_clear, lw, ts`

| Columna | Fuente API | Nota |
|---|---|---|
| `tmean` | T2M | completo 1984+ |
| `tmin`, `tmax` | derivado de hourly T2M | **solo 2010+** (nulo antes) |
| `pmm` | PRECTOTCORR | lluvia diaria (mm) |
| `rh`, `ws`, `ps`, `t2mdew`, `ts` | RH2M, WS2M, PS, T2MDEW, TS | |
| `sw`, `lw`, `sw_clear` | ALLSKY_SFC_SW_DWN, ALLSKY_SFC_LW_DWN, CLRSKY_SFC_SW_DWN | radiación; `lw` nulo 1984–87 |

## Verificación (14/11)

- 10 zonas × 15,342 filas; `tmean` 100% completo; `tmin/tmax` sin huecos 2010+.
- **Heladas 2010–25: 194 días, pico may–sep** (may 22, jun 53, jul 75, ago 38) →
  coherente con CROPS.md (estación de heladas may–ago).
- ⚠️ **Los 10 puntos caen en la misma celda POWER 0.5°** → serie idéntica; solo difiere
  `elev_m` (3126 m). El refinamiento por zona lo aportan GAMC + SRTM/pendiente.

## Regenerar

```bash
python3 src/etl/power_etl.py --points src/etl/points.json \
  --start 1984 --end 2025 --hstart 2010 --hend 2025 --out data/power
```
