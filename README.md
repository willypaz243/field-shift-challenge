# Choclito · Field Shift (NASA Space Apps 2026)

App para agricultores del Cercado de Cochabamba que combina datos NASA con información local para decidir cuándo sembrar, qué rotar y cómo protegerse de heladas, granizo y falta de agua.

## Stack

**Mobile-first con un solo código para Android y web.** La app se diseña para celular. Si el APK no llega a tiempo, el mismo código se publica como web (PWA) para la demo.

### App (`app/`)

| Pieza | Tecnología | Por qué |
|---|---|---|
| Framework | **Expo** (React Native + TypeScript) | Android nativo y, con el mismo código, web vía `react-native-web`. Se prueba al instante en el celular con Expo Go. |
| Navegación | **Expo Router** | Tabs Hoy / Calendario / Sembrar / Mi zona y ventanas (bottom sheets) por archivo. |
| Datos offline | **expo-sqlite** | Base local con el paquete de `/sync`; la app funciona sin señal. |
| Notificaciones | **expo-notifications** (locales) | Alertas y recordatorios de cosecha a las 6:00 sin depender del servidor. |
| Ubicación | **expo-location** | GPS para encontrar la zona. |
| Voz | **expo-speech** | Botón "Escuchar". |
| Mapas y gráficos | **react-native-svg** | Mapas de parcela y zona dibujados en SVG: funcionan igual en Android y web. |
| Estado | **Zustand** | Simple y liviano para un celular de gama baja. |
| Textos | **i18next** | Español y quechua desde el inicio. |
| Diseño | Tokens de `mockups/app.css` | Colores, fuente Atkinson Hyperlegible Next, texto ≥ 17 px, toques ≥ 56 px. |

### API (`api/`)

| Pieza | Tecnología | Por qué |
|---|---|---|
| Framework | **FastAPI** (Python 3.12) | OpenAPI automático y el mismo lenguaje que el ETL y los modelos. |
| ORM | **SQLModel** | Modelos que sirven a la vez como tablas y como esquemas de respuesta. Las tablas se crean con `SQLModel.metadata.create_all()`. |
| Base de datos | **SQLite** (un archivo) | Cero configuración. |
| Contrato | `api/openapi.yaml` desde [`docs/API-CONTRACT.md`](docs/API-CONTRACT.md) | Front y back trabajan en paralelo. |
| Mock | **Prism** (`prism mock api/openapi.yaml`) | El front arranca contra el mock antes de que exista la API. |
| Tareas programadas | cron + scripts de `src/` | Regenerar la proyección y el pronóstico. |

### Datos y modelos (`src/`, `imerg/`, `data/`)

| Pieza | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Acceso NASA | `earthaccess` (Earthdata), API de NASA POWER |
| Archivos | `xarray` + `netCDF4` (IMERG), `h5py` (SMAP) |
| Geometría | `shapely` |
| Análisis | `pandas`, `numpy` |
| Series de tiempo | `statsmodels` (SARIMA) o `prophet` |
| Scoring de ventana | Referencia en Python + vectores de prueba en JSON que la app (TypeScript) debe reproducir |

### Herramientas

| Uso | Herramienta |
|---|---|
| Python | `uv` (entornos y dependencias) |
| JS | `npm` + Expo CLI |
| Tests | `pytest` (API y datos), `jest` (app) |
| Formato | `ruff` (Python), `prettier` + `eslint` (TS) |

## Estructura

```
app/        App Expo (Android + web)
api/        FastAPI + SQLModel + openapi.yaml
src/etl/    ETL de NASA POWER y otras fuentes
imerg/      Pipeline de lluvia GPM IMERG
data/       Datos procesados (catálogo de cultivos, POWER, GAMC)
docs/       Contrato de API, flujos, contexto local, backlog
mockups/    Mockups HTML de referencia
```
