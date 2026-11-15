# Choclito · Field Shift (NASA Space Apps 2026)

App for small farmers in Cercado, Cochabamba (Bolivia). It combines NASA data with local information to help them decide when to sow, which crop to rotate into, and how to prepare for frost, hail and water shortages.

## Stack

**Mobile-first, one codebase for Android and web.** The app is designed for phones. If the APK is not ready in time, the same code is published as a web app for the demo.

### App (`app/`)

| Part | Technology | Why |
|---|---|---|
| Framework | **Expo** (React Native + TypeScript) | Native Android and, from the same code, web via `react-native-web`. Instant testing on a phone with Expo Go. |
| Navigation | **Expo Router** | Hoy / Calendario / Sembrar / Mi zona tabs and bottom sheets, file-based. |
| Offline data | **expo-sqlite** | Local database with the `/sync` package; the app works without signal. |
| Notifications | **expo-notifications** (local) | Alerts and harvest reminders at 6:00 without depending on the server. |
| Location | **expo-location** | GPS to find the farmer's zone. |
| Voice | **expo-speech** | "Escuchar" (listen) button. |
| Maps and charts | **react-native-svg** | Plot and zone maps drawn in SVG: same result on Android and web. |
| State | **Zustand** | Simple and light for low-end phones. |
| Text | **i18next** | Spanish and Quechua from day one. |
| Design | Tokens from `mockups/app.css` | Colors, Atkinson Hyperlegible Next font, text ≥ 17 px, touch targets ≥ 56 px. |

### API (`api/`)

| Part | Technology | Why |
|---|---|---|
| Framework | **FastAPI** (Python 3.13) | Automatic OpenAPI and the same language as the ETL and models. |
| ORM | **SQLModel** | Models are both tables and response schemas. Tables are created with `SQLModel.metadata.create_all()`. |
| Database | **SQLite** (single file) | Zero setup. |
| Contract | `api/openapi.yaml` from [`docs/API-CONTRACT.md`](docs/API-CONTRACT.md) | Frontend and backend work in parallel. |
| Mock | **Prism** (`prism mock api/openapi.yaml`) | The frontend starts against the mock before the API exists. |
| Scheduled jobs | cron + scripts in `src/` | Regenerate the projection and the forecast. |

### Data and models (`src/`, `data/`)

| Part | Technology |
|---|---|
| Language | Python 3.13 (single `uv` project at the repo root: `pyproject.toml`) |
| NASA access | `earthaccess` (Earthdata), NASA POWER API |
| Files | `xarray` + `netCDF4` (IMERG), `h5py` (SMAP) |
| Geometry | `shapely` |
| Analysis | `pandas`, `numpy` |
| Time series | `statsmodels` (SARIMA) or `prophet` |
| Window scoring | Python reference + JSON test vectors that the app (TypeScript) must reproduce |

### Tooling

| Use | Tool |
|---|---|
| Python | `uv` (environments and dependencies) |
| JS | `npm` + Expo CLI |
| Tests | `pytest` (API and data), `jest` (app) |
| Formatting | `ruff` (Python), `prettier` + `eslint` (TS) |

## Database

One SQLite file, `data/db/valle.db`, with tables defined by the SQLModel models of each module. `make db-init` creates them, `make db-load` (or `bash etl.sh db`) loads the ETL data. Details in [`docs/db-schema.md`](docs/db-schema.md).

`make forecast` regenerates the 365-day forecast (`src.model.run_pipeline`) and replaces the `forecasts` table for every zone (`src.etl.load_forecast`). Run it weekly on the server, for example with cron (Mondays 03:00 La Paz time):

```
0 3 * * 1 cd /srv/field-shift-challenge && make forecast >> logs/forecast.log 2>&1
```

## Architecture

The API is a **modular monolith**: one FastAPI process and one SQLite database, split into modules by domain. Each module owns its tables and exposes a service; other modules only talk to it through that service.

```
api/
  main.py             App factory, mounts every module router
  core/               Config, DB engine/session, errors, shared utils
  modules/
    zones/            Agricultural zones (GAMC grid)
    crops/            Crop catalog
    climate/          Short forecast, yearly projection, climatology, history
    alerts/           Alert rules and active alerts
    rotations/        Rotation plans and scores
    reports/          Farmer reports and zone map
    feedback/         Harvest results and chosen plans
    sync/             /sync package for the app (composes other services)
```

Every module has the same files:

| File | Responsibility |
|---|---|
| `router.py` | HTTP only: parse the request, call the service, return the schema. No business logic, no queries. |
| `service.py` | Business logic. The only public entry point of the module. |
| `repository.py` | Database access with SQLModel sessions. Used only by its own service. |
| `models.py` | SQLModel tables owned by the module. |
| `schemas.py` | Request/response models that match `docs/API-CONTRACT.md`. |

Rules between modules:

- `router → service → repository`. Never skip a layer.
- A module may call another module's `service`, never its `repository` or `models`.
- `sync` only composes services; it owns no tables.
- Data jobs in `src/` write through the service of the module that owns the table.

## Structure

```
app/        Expo app (Android + web)
api/        FastAPI modular monolith + openapi.yaml
src/etl/    ETL scripts (NASA POWER, GPM IMERG, SMAP, GAMC, SRTM, load_db)
data/       Processed data (crop catalog, POWER, GAMC)
docs/       API contract, app flows, local context, backlog
mockups/    Reference HTML mockups
```
