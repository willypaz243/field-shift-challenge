# Catálogo de cultivos — vector de condiciones óptimas

> Base: [`docs/CROPS.md`](../../docs/CROPS.md) (investigación 14/11/2026: PROINPA, SITAP/MDRyT,
> CIPCA, SIIP, EcoRural, prensa local). Zona: Cercado de Cochabamba.
>
> Este JSON es el **catálogo que sincroniza el móvil** (tarea 0.4 del backlog) y el que
> alimenta el scoring de ventana (tarea 2.4). La proyección usa **las mismas variables**
> (§ "Variables comunes"), con dimensión de tiempo: 1 vector por día.

## Variables comunes (cultivo ↔ proyección)

| Variable | Unidad | Proviene de |
|---|---|---|
| `tmin`, `tmax`, `tmean` | °C | POWER (diario) |
| `pmm` | mm/día | POWER (PRECTOT) / GPM |
| `rh` | % | POWER (RH2M) |
| `sw` | W/m² | POWER (ALLSKY_SFC_SW_DWN) |
| `ws` | m/s | POWER (WS2M) |
| `sm_surface`, `sm_root` | m³/m³ | SMAP SPL4SMGP v8 (2015+, promedio diario) |

En el MVP, el scoring solo usa `tmean`, `tmin` y `pmm` (las variables con evidencia local
por cultivo). Las demás se cargan pero puntúan **neutro** (sin evidencia no se penaliza).

## Esquema por cultivo

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | clave única (usa también la URL de la API) |
| `nombre` / `cientifico` / `tipo` | string | display; tipo: tuberculo, cereal, hortaliza, leguminosa, forrajero, frutal, flor |
| `tipo_ciclo` | `anual` \| `perenne` | perenne: el motor usa época de siembra, no ventana fija |
| `ciclo_dias` | [min, max] | duración siembra→cosecha (ventana L del scoring) |
| `temp.tmean_opt` | [min, max] \| null | rango óptimo de temperatura media (°C); `null` = neutro |
| `temp.fuente` | `local` \| `estimado` | **estimado** = valor agronómico general (no fuente local) → validar con experto |
| `helada.tolerancia` | `alta` \| `media` \| `baja` | peso de penalización por días de helada (`tmin < 0 °C`): 0 / 0.5 / 1.0 |
| `helada.etapa_critica` | string \| null | etapa sensible (floración, espigazón, granos, todo el ciclo) |
| `agua.demanda` | `muy alta` \| `alta` \| `media` \| `media-baja` | ranking de necesidad hídrica |
| `agua.deficit_tol` | `alta` \| `media` \| `baja` | tolerancia a déficit (baja = penaliza fuerte las ventanas secas) |
| `altitud` | `valle` \| `alta` \| `ambas` | `alta` = sobre cota 2750 m (zona agrícola-forestal GAMC) |
| `erosion_sens` | `alta` \| `media` \| `baja` | penalización si `zones.cerca_drenaje` < 200 m |
| `fix_n` | bool | fija nitrógeno (módulo de rotaciones) |
| `mercado` / `siembra_local` / `rotacion` | string | contexto para el pitch y el módulo de rotaciones |
| `fuente` | string | trazabilidad de los valores |

## Reglas de scoring (espec para el motor, tarea 2.4)

Para cada ventana de L días (L ∈ `ciclo_dias`) sobre la proyección:

1. **Helada:** días con `tmin < 0 °C` → penalización = `días_helada / L` × peso(`tolerancia`).
   Si hay `etapa_critica`, el peso se aplica al sub-rango estimado de la etapa (MVP: ciclo completo).
2. **Agua:** `pmm_cum` = suma de `pmm` en la ventana → fit = posición del cum. frente al
   ranking de `demanda` (muy alta=4 … media-baja=1.5), atenuado por `deficit_tol`.
3. **Temperatura:** fit por día = 1 − |`tmean` − centro(`tmean_opt`)| / (semiancho), truncado
   a [0,1]; promedio sobre la ventana. `null` → 1.0 (neutro).
4. **Erosión:** `erosion_sens ≠ baja` y zona con `cerca_drenaje < 200` → −10 pts fijos.
5. **Score final** = 100 × (0.5·fit_T + 0.3·fit_agua + 0.2·(1 − penal_helada)) − erosión,
   clip [0,100]. **Confianza** = fracción de días de la ventana cuya banda de incertidumbre
   de la proyección no cruza el límite de helada/rango óptimo.

## Cultivos del catálogo (13)

| id | Ciclo (días) | T óptima media | Helada | Agua | FixN |
|---|---|---|---|---|---|
| papa | 120–180 | 15–20 °C (local) | baja | alta | ❌ |
| choclo | 120–240 | 18–27 °C (estimado) | baja | alta | ❌ |
| trigo | 120–150 | 12–22 °C (estimado) | media (espigazón) | media | ❌ |
| papaliza | 180–210 | 8–14 °C (local) | alta | media | ❌ |
| lechuga | 28–42 | 10–18 °C (local, derivado) | baja | muy alta | ❌ |
| hortalizas | 30–90 | 10–20 °C (local) | baja | muy alta | ❌ |
| alfalfa | perenne (sep–mar) | 15–25 °C (estimado) | media | muy alta | ✅ |
| haba | 150–180 | 8–18 °C (estimado) | alta | media | ✅ |
| tarwi | 180–240 | 10–20 °C (estimado) | alta | media-baja | ✅ (50+ kg N/ha) |
| quinua | 150–180 | 12–22 °C (estimado) | media (post-floración) | media | — |
| avena | 90–120 | 8–18 °C (estimado) | alta | media | — |
| durazno | perenne (plantar invierno) | 12–24 °C (estimado) | media (floración) | media | ❌ |
| flores | 60–180 | 12–22 °C (estimado) | baja | alta | ❌ |

> Los valores marcados **estimado** son agronómicos generales (FAO/tipos de cultivo), no
> fuentes locales: validarlos con un agrónomo local si hay tiempo (o descartar el fit_T para
> ese cultivo y basarse en helada+agua, que sí tienen evidencia local).
