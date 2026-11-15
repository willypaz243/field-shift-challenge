#!/usr/bin/env bash
# ETL orquestador (tarea 1.6): reconstruye todo desde cero o reanuda lo pendiente.
#
# Todos los ETLs son resumibles/idempotentes (saltan lo ya procesado), así
# `bash etl.sh` sirve tanto para un run completo como para reintentar fallos.
#
# Orden:
#   1. POWER   — clima diario 1984+ (base, sin token)
#   2. IMERG   — precipitación satelital 2016+ (token Earthdata)
#   3. SMAP    — humedad de suelo 2015+ (token Earthdata)
#   4. GAMC    — zonas: comuna/distrito/periurbano/drenaje (WMS municipal)
#   5. SRTM    — elevación/pendiente (Open-Meteo DEM)
#   6. DB      — carga consolidada a data/db/valle.db
#
# Uso:
#   bash etl.sh              # todo
#   bash etl.sh imerg smap   # solo los ETLs nombrados
#   bash etl.sh db           # solo re-cargar la DB
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

run() {
    local name="$1"; shift
    echo ""
    echo "════════ $name ════════"
    "$PY" "$@"
}

STEPS="${*:-power imerg smap gamc srtm db}"
for step in $STEPS; do
    case "$step" in
        power)
            run POWER src/etl/power_etl.py --start 1984 --end 2025 --hend 2025 ;;
        imerg)
            run "IMERG (GPM)" src/etl/imerg_etl.py \
                --start 2016-01-01 --end 2025-12-31 --workers 3 \
                --out data/imerg/imerg_valle_daily.csv ;;
        smap)
            run "SMAP L4" src/etl/smap_etl.py \
                --start 2015-04-01 --end 2025-12-31 --workers 5 \
                --out data/smap/smap_valle_daily.csv ;;
        gamc)
            run "GAMC (WMS)" src/etl/gamc_etl.py --out data/gamc/zones_gamc.json ;;
        srtm)
            run "SRTM/DEM" src/etl/srtm_etl.py --out data/srtm/srtm_zones.json ;;
        db)
            run "LOAD DB" src/etl/load_db.py --db data/db/valle.db ;;
        *)
            echo "Paso desconocido: $step (power|imerg|smap|gamc|srtm|db)" >&2
            exit 1 ;;
    esac
done

echo ""
echo "✅ ETL terminado. DB: data/db/valle.db"
