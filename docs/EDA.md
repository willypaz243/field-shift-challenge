# EDA — validación de series POWER (valle de Cochabamba)

- Serie: D1 Tunari (celda POWER 0.5°), 1984-01-01 → 2026-01-01
- Fila válida de tmin/tmax: 2010-01-01

## Climatología mensual (2000–2025)

| Mes | pmm (mm) | tmean (°C) | tmin (°C) |
|---|---|---|---|
| 01 | 3.3 | 14.3 | 8.9 |
| 02 | 3.3 | 13.9 | 8.6 |
| 03 | 2.0 | 13.8 | 8.3 |
| 04 | 0.6 | 13.4 | 7.2 |
| 05 | 0.2 | 12.2 | 4.9 |
| 06 | 0.3 | 10.9 | 3.1 |
| 07 | 0.1 | 10.6 | 2.8 |
| 08 | 0.2 | 11.7 | 3.5 |
| 09 | 0.4 | 13.4 | 6.2 |
| 10 | 0.8 | 14.8 | 8.0 |
| 11 | 1.2 | 15.5 | 8.8 |
| 12 | 2.8 | 15.1 | 9.4 |

## Verificación contra conocimiento local

- ✅ Lluvia concentrada dic–feb (>2× mensual anual) — 3.1 vs 1.3 mm/mes
- ✅ Sequía may–sep (<25% de la época lluviosa) — 0.2 vs 3.1 mm/mes
- ❌ Heladas may–ago (tmin < 0°C) — meses: []
- ✅ Valle templado (tmean anual 10–20 °C) — tmean anual 13.3 °C

## ET₀ Hargreaves (FAO-56 Ec. 52)

- Fórmula: `ET₀ = 0.0023·(Tmean+17.8)·√(Tmax−Tmin)·Ra` con Ra en mm/día (0.408×MJ/m²).
- ⚠️ La fórmula del BACKLOG v2 (`0.0023·(Tmean+15)·√RA`) es incompleta y da ~10× menos; corregida en `src/model/et0.py`.

## Limitaciones de POWER detectadas (armonización)

1. **pmm absoluto muy bajo**: 15 mm/año vs ~700 mm/año esperados en el valle. La celda 0.5° de POWER subestima la precipitación convective andina. **IMERG (GPM) se usa como fuente primaria de pmm** y POWER como validación de patrón estacional.
2. **tmin nunca < 0 °C** en POWER (mínimo jul ≈ 2.8 °C), pero el valle tiene heladas may–ago (conocimiento local). El scoring aplica un offset de helada documentado (`FROST_OFFSET`) hasta calibrar con estaciones locales.
3. **Outliers pmm > 100 mm/día** (2 casos, máx 704 mm): descartados como error de dato en el ETL.
