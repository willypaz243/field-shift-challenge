# Database schema

One SQLite file: `data/db/valle.db`. Tables are defined only by SQLModel models in the module that owns them (`api/modules/<module>/models.py`, `sync_version` in `api/core/models.py`) and created with `SQLModel.metadata.create_all()` through `api.core.db.init_db()`. No migrations.

- `src/etl/load_db.py` creates the tables with `init_db()` and fills the ETL tables (`zones`, `climate_history`, `crops`, `events`, `reservoir`, `sync_version`) with upserts. It never touches `reports`, `feedback` or `plans`.
- The API writes `reports`, `feedback` and `plans`.
- `DATABASE_URL` overrides the default `sqlite:///./data/db/valle.db`. SQLite foreign keys are enabled on every connection.
- Dates are stored as `YYYY-MM-DD`; datetimes must be timezone-aware.

```bash
make db-init   # create missing tables in data/db/valle.db
make db-load   # run the ETL loader (same as: bash etl.sh db)
make test      # pytest
```

## Tables

### `zones` (modules.zones)

| Column | Type | Notes |
|---|---|---|
| `id` | varchar | PK |
| `nombre` | varchar |  |
| `comuna` | varchar |  |
| `distrito` | varchar |  |
| `lat` | float | required |
| `lon` | float | required |
| `elev_m` | float |  |
| `pendiente` | float |  |
| `es_agricola` | boolean | required |
| `cerca_drenaje` | integer |  |
| `altitud_alta` | boolean | required |

### `climate_history` (modules.climate)

| Column | Type | Notes |
|---|---|---|
| `zone_id` | varchar | PK, FK `zones.id` |
| `fecha` | date | PK |
| `tmin` | float |  |
| `tmax` | float |  |
| `tmean` | float |  |
| `pmm` | float |  |
| `rh` | float |  |
| `sw` | float |  |
| `ws` | float |  |
| `et0` | float |  |
| `sm_surface` | float |  |
| `sm_root` | float |  |
| `pmm_sat` | float |  |
| `t2mdew` | float |  |
| `ps` | float |  |
| `sw_clear` | float |  |
| `lw` | float |  |

### `forecasts` (modules.climate)

| Column | Type | Notes |
|---|---|---|
| `zone_id` | varchar | PK, FK `zones.id` |
| `fecha` | date | PK |
| `anio` | integer | required |
| `tmin` | float |  |
| `tmax` | float |  |
| `tmean` | float |  |
| `pmm` | float |  |
| `et0` | float |  |
| `rh` | float |  |
| `sw` | float |  |
| `ws` | float |  |
| `sm_surface` | float |  |
| `sm_root` | float |  |
| `tmin_min` | float |  |
| `tmin_max` | float |  |
| `pmm_min` | float |  |
| `pmm_max` | float |  |
| `creado_en` | datetime | required |

### `weather` (modules.climate)

Short-range forecast (14 days). Filled by the T11 ingestion (#17); empty until then.

| Column | Type | Notes |
|---|---|---|
| `zone_id` | varchar | PK, FK `zones.id` |
| `fecha` | date | PK, civil day America/La_Paz |
| `tmin` | float | required, °C |
| `tmax` | float | required, °C |
| `pmm` | float | required, mm/day |
| `granizo` | boolean |  |
| `confianza` | varchar | required: `alta` · `media` · `baja` |
| `fuente` | varchar | required, source code (§10 of the contract) |
| `actualizado_en` | datetime | required, UTC |

### `crops` (modules.crops)

| Column | Type | Notes |
|---|---|---|
| `id` | varchar | PK |
| `nombre` | varchar | required |
| `t_opt_min` | float |  |
| `t_opt_max` | float |  |
| `tol_helada` | varchar |  |
| `demanda_agua` | varchar |  |
| `deficit_tol` | varchar |  |
| `ciclo_min_dias` | integer |  |
| `ciclo_max_dias` | integer |  |
| `fix_n` | boolean | required |
| `mercado` | varchar |  |
| `breaks_pest_cycle` | boolean | required |
| `forage_value` | varchar |  |
| `drought_tolerant` | varchar |  |
| `deep_rooting` | boolean | required |
| `erosion_sens` | varchar |  |
| `kc_inicial` | float |  |
| `kc_medio` | float |  |
| `kc_final` | float |  |
| `altitud` | varchar |  |
| `rotacion` | varchar |  |
| `foto_url` | varchar |  |

### `events` (modules.alerts)

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `tipo` | varchar | required |
| `fecha` | date | required |
| `zone_id` | varchar |  |
| `descripcion` | varchar |  |
| `fuente` | varchar |  |

### `reservoir` (modules.water)

| Column | Type | Notes |
|---|---|---|
| `id` | varchar | PK |
| `nombre` | varchar | required |
| `nivel_pct` | float |  |
| `volumen_hm3` | float |  |
| `estado` | varchar |  |
| `actualizado_en` | date |  |

### `reports` (modules.reports)

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `idempotency_key` | varchar | unique, required |
| `tipo` | varchar | required |
| `zone_id` | varchar | FK `zones.id`, required |
| `lat` | float |  |
| `lon` | float |  |
| `ocurrido_en` | datetime | required |
| `creado_en` | datetime | required |
| `foto` | blob |  |
| `audio` | blob |  |

### `feedback` (modules.feedback)

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `zone_id` | varchar | FK `zones.id`, required |
| `crop_id` | varchar | FK `crops.id`, required |
| `siembra` | date |  |
| `cosecha` | date | required |
| `resultado` | varchar | required |
| `creado_en` | datetime | required |

### `plans` (modules.feedback)

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `zone_id` | varchar | FK `zones.id`, required |
| `rotacion_id` | varchar | required |
| `siembra` | date | required |
| `creado_en` | datetime | required |

### `sync_version` (core)

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `creado_en` | datetime | required |
| `hash` | varchar | required |

