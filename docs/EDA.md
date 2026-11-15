# EDA — validación de series (valle de Cochabamba)

- Serie: D1_tunari (DB consolidada `valle.db`), 2016-01-01 → 2025-12-31
- `pmm` = IMERG `pmm_sat` (primaria); POWER como fallback.

## Climatología mensual (2016–2025)

| Mes | pmm (mm) | tmean (°C) | tmin (°C) |
|---|---|---|---|
| 01 | 5.5 | 14.7 | 9.1 |
| 02 | 5.8 | 14.2 | 8.8 |
| 03 | 4.1 | 14.0 | 8.5 |
| 04 | 1.5 | 13.9 | 7.4 |
| 05 | 1.0 | 12.7 | 5.2 |
| 06 | 0.5 | 10.8 | 2.9 |
| 07 | 0.4 | 11.1 | 3.1 |
| 08 | 0.7 | 11.9 | 3.6 |
| 09 | 1.0 | 13.8 | 6.5 |
| 10 | 1.9 | 15.2 | 8.2 |
| 11 | 4.0 | 15.7 | 9.0 |
| 12 | 5.5 | 15.3 | 9.4 |

## Verificación contra conocimiento local

- ✅ Lluvia concentrada dic–feb (>2× mensual anual) — 5.6 vs 2.7 mm/mes
- ✅ Sequía may–sep (<25% de la época lluviosa) — 0.7 vs 5.6 mm/mes
- ✅ Heladas may–ago (mínimo diario tmin < 0°C) — meses: [5, 6, 7, 8] (mínimos: 05 -1.6, 06 -3.5, 07 -3.9, 08 -2.8)
- ✅ Valle templado (tmean anual 10–20 °C) — tmean anual 13.6 °C

## ET₀ Hargreaves (FAO-56 Ec. 52)

- Fórmula: `ET₀ = 0.0023·(Tmean+17.8)·√(Tmax−Tmin)·Ra` con Ra en mm/día (0.408×MJ/m²).

## Armonización de fuentes (decisiones)

1. **pmm**: IMERG 967 mm/año vs POWER 449 mm/año (2016–2025). POWER (celda 0.5°) subestima la lluvia convectiva andina; IMERG (0.1°) es la fuente primaria y POWER queda como validación de patrón.
2. **tmin**: POWER llega a -3.9 °C (may–ago), coherente con heladas locales. El scoring sigue aplicando `FROST_OFFSET = -2.0` como heurística documentada hasta calibrar con estaciones locales.
3. **Outliers pmm > 100 mm/día**: descartados como error de dato (NaN).
