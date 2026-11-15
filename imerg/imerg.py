#!/usr/bin/env python3
"""IMERG diario: catálogo público, descarga autenticada y recorte a SQLite."""

import argparse
import csv
import datetime as dt
import json
import math
import re
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path

PRODUCTS = {"final": "GPM_3IMERGDF", "late": "GPM_3IMERGDL"}


def dates(start, end):
    start, end = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    if start > end:
        raise ValueError("La fecha inicial debe ser anterior a la final")
    return start, end


def catalog(start, end, run, bbox):
    dates(start, end)
    entries = []
    for page in range(1, 10000):
        params = dict(
            short_name=PRODUCTS[run],
            version="07",
            page_size=2000,
            page_num=page,
            sort_key="start_date",
            temporal=f"{start}T00:00:00Z,{end}T23:59:59Z",
        )
        if bbox:
            params["bounding_box"] = ",".join(map(str, bbox))
        url = "https://cmr.earthdata.nasa.gov/search/granules.json?" + urllib.parse.urlencode(
            params
        )
        with urllib.request.urlopen(url, timeout=90) as response:
            batch = json.load(response)["feed"]["entry"]
        entries.extend(batch)
        if len(batch) < 2000:
            break
    return entries


def manifest(entries, start, end, run, bbox):
    files = []
    for entry in entries:
        urls = [
            link["href"]
            for link in entry.get("links", [])
            if not link.get("inherited")
            and link.get("rel", "").endswith("/data#")
            and link["href"].startswith("https://")
        ]
        if not urls:
            raise ValueError(f"Sin enlace HTTPS: {entry['id']}")
        files.append(
            dict(
                id=entry["id"],
                name=entry["producer_granule_id"],
                date=entry["time_start"][:10],
                url=urls[0],
                updated=entry.get("updated"),
                size_mb=entry.get("granule_size"),
            )
        )
    start_d, end_d = dates(start, end)
    found = {item["date"] for item in files}
    missing = [
        (start_d + dt.timedelta(days=i)).isoformat()
        for i in range((end_d - start_d).days + 1)
        if (start_d + dt.timedelta(days=i)).isoformat() not in found
    ]
    return dict(
        product=PRODUCTS[run],
        version="07",
        run=run,
        timezone="UTC",
        start=start,
        end=end,
        bbox_search_only=bbox,
        created_at=dt.datetime.now(dt.UTC).isoformat(),
        files=files,
        missing_dates=missing,
        warning="Los archivos son globales. El BBOX de búsqueda no recorta los datos.",
    )


def download(path, folder):
    import earthaccess

    data = json.loads(Path(path).read_text())
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    auth = earthaccess.login(strategy="interactive", persist=False)
    if not auth.authenticated:
        raise RuntimeError("Earthdata no autenticó la cuenta")
    for item in data["files"]:
        target = folder / item["name"]
        stamp = target.with_suffix(target.suffix + ".json")
        if (
            target.exists()
            and stamp.exists()
            and json.loads(stamp.read_text()).get("updated") == item["updated"]
        ):
            continue
        # Descargar a staging evita considerar completo un archivo interrumpido.
        staging = folder / "staging"
        staging.mkdir(exist_ok=True)
        result = earthaccess.download([item["url"]], local_path=str(staging), threads=1)
        if len(result) != 1 or not Path(result[0]).is_file():
            raise RuntimeError(f"No se descargó {item['name']}")
        downloaded = Path(result[0])
        import xarray as xr

        with xr.open_dataset(downloaded) as ds:
            if "precipitation" not in ds:
                raise ValueError("El archivo no contiene precipitation")
        downloaded.replace(target)
        stamp.write_text(json.dumps(item, indent=2))
        print(target)


def open_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS rain (
      date TEXT, source TEXT, product TEXT, version TEXT, run TEXT,
      cell_id TEXT, lat REAL, lon REAL, area_fraction REAL,
      variable TEXT, value REAL, unit TEXT, quality TEXT,
      downloaded_at TEXT, filename TEXT,
      PRIMARY KEY(date, product, version, cell_id, variable));
    CREATE VIEW IF NOT EXISTS preferred_rain AS
      SELECT * FROM rain r WHERE (r.run='final' AND (r.value IS NOT NULL OR NOT EXISTS (
        SELECT 1 FROM rain l WHERE l.date=r.date AND l.cell_id=r.cell_id
          AND l.variable=r.variable AND l.version=r.version
          AND l.run='late' AND l.value IS NOT NULL))) OR (r.run='late' AND NOT EXISTS (
        SELECT 1 FROM rain f WHERE f.date=r.date AND f.cell_id=r.cell_id
          AND f.variable=r.variable AND f.version=r.version
          AND f.run='final' AND (f.value IS NOT NULL OR r.value IS NULL)));
    """)
    return con


def read_area(path):
    from shapely.geometry import shape
    from shapely.ops import unary_union

    raw = json.loads(Path(path).read_text())
    if raw["type"] == "FeatureCollection":
        geom = unary_union([shape(f["geometry"]) for f in raw["features"]])
    elif raw["type"] == "Feature":
        geom = shape(raw["geometry"])
    else:
        geom = shape(raw)
    if geom.is_empty or not geom.is_valid or geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError("Se necesita un polígono GeoJSON válido, WGS84 (lon, lat)")
    if not (
        -180 <= geom.bounds[0] <= geom.bounds[2] <= 180
        and -90 <= geom.bounds[1] <= geom.bounds[3] <= 90
    ):
        raise ValueError("Coordenadas fuera de WGS84")
    return geom


def process(folder, polygon, database, run):
    import xarray as xr
    from shapely.geometry import box

    area = read_area(polygon)
    con = open_db(database)
    files = sorted(Path(folder).glob("*.nc4"))
    if not files:
        raise ValueError("No hay archivos .nc4 en la carpeta")
    for path in files:
        match = re.search(r"\.(\d{8})-S.*\.(V07[^.]*)\.nc4$", path.name)
        if not match:
            raise ValueError(f"Nombre no reconocido: {path.name}")
        expected = "3B-DAY-L." if run == "late" else "3B-DAY."
        if not path.name.startswith(expected):
            raise ValueError(f"El archivo no corresponde a {run}: {path.name}")
        date = dt.datetime.strptime(match[1], "%Y%m%d").date().isoformat()
        with xr.open_dataset(path) as ds:
            rain = ds["precipitation"]
            unit = rain.attrs.get("units", "")
            if unit.replace(" ", "").lower() not in ("mm/day", "mmd-1", "mmday-1"):
                raise ValueError(f"Unidad inesperada {unit!r}; no se convierte silenciosamente")
            if "time" in ds and str(ds.time.values[0])[:10] != date:
                raise ValueError("La fecha interna no coincide con el nombre")
            quality_names = [
                n
                for n in (
                    "precipitation_cnt",
                    "randomError",
                    "randomError_cnt",
                    "PrecipitationQualityIndex",
                )
                if n in ds
            ]
            west, south, east, north = area.bounds
            # 0.1° es la malla original del producto diario, no resolución de parcela.
            lats = [
                (i, float(v))
                for i, v in enumerate(ds.lat.values)
                if south - 0.05 < v < north + 0.05
            ]
            lons = [
                (i, float(v)) for i, v in enumerate(ds.lon.values) if west - 0.05 < v < east + 0.05
            ]
            rows = []
            for yi, lat in lats:
                for xi, lon in lons:
                    cell = box(lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
                    overlap = cell.intersection(area).area
                    if overlap <= 0:
                        continue
                    index = dict(lat=yi, lon=xi)

                    def scalar(name):
                        a = ds[name].isel(**index)  # noqa: B023 (se usa en la misma iteración)
                        if a.size != 1:
                            raise ValueError(f"Dimensiones inesperadas en {name}")
                        v = float(a.values.reshape(-1)[0])
                        return v if math.isfinite(v) else None

                    value = scalar("precipitation")
                    if value is not None and value < 0:
                        raise ValueError("Precipitación negativa no enmascarada")
                    quality = {
                        n: {"value": scalar(n), "unit": ds[n].attrs.get("units")}
                        for n in quality_names
                    }
                    quality["status"] = "missing" if value is None else "available"
                    count = quality.get("precipitation_cnt", {}).get("value")
                    if count is not None and count < 48:
                        quality["status"] = "incomplete_half_hours"
                    downloaded = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.UTC).isoformat()
                    rows.append(
                        (
                            date,
                            "NASA GPM",
                            PRODUCTS[run],
                            match[2],
                            run,
                            f"imerg_0.1:{lat:.2f}:{lon:.2f}",
                            lat,
                            lon,
                            overlap / cell.area,
                            "precipitation",
                            value,
                            "mm/day",
                            json.dumps(quality),
                            downloaded,
                            path.name,
                        )
                    )
            if not rows:
                raise ValueError("Ninguna celda intersecta el área")
            with con:
                con.executemany(
                    "INSERT OR REPLACE INTO rain VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
                )
            print(f"{date}: {len(rows)} celdas")
    con.close()


def report(database, start, end, output):
    start_d, end_d = dates(start, end)
    con = open_db(database)
    rows = con.execute(
        "SELECT date,cell_id,value,quality FROM preferred_rain WHERE date BETWEEN ? AND ?",
        (start, end),
    ).fetchall()
    cells = sorted({r[1] for r in rows})
    expected = {
        (str(start_d + dt.timedelta(days=i)), c)
        for i in range((end_d - start_d).days + 1)
        for c in cells
    }
    found = {(r[0], r[1]) for r in rows}
    result = dict(
        start=start,
        end=end,
        cells=cells,
        records=len(rows),
        missing_records=sorted(expected - found),
        null_values=sum(r[2] is None for r in rows),
        incomplete_records=sum(json.loads(r[3])["status"] == "incomplete_half_hours" for r in rows),
        latest_observation=max((r[0] for r in rows), default=None),
        warning="Sin registros no se puede inferir la cobertura espacial esperada."
        if not cells
        else None,
    )
    Path(output).write_text(json.dumps(result, indent=2))
    con.close()


def export_csv(database, output):
    con = open_db(database)
    cursor = con.execute("SELECT * FROM preferred_rain ORDER BY date,cell_id,run")
    with Path(output).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([item[0] for item in cursor.description])
        writer.writerows(cursor)
    con.close()


def update(root, polygon, database, final_days=210, late_days=14):
    # Reconsultar la ventana recoge revisiones; los sidecars evitan descargas idénticas.
    area = read_area(polygon)
    today = dt.datetime.now(dt.UTC).date()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for run, days in (("late", late_days), ("final", final_days)):
        start = str(today - dt.timedelta(days=days))
        end = str(today - dt.timedelta(days=1))
        target = root / f"{run}-manifest.json"
        target.write_text(
            json.dumps(
                manifest(catalog(start, end, run, area.bounds), start, end, run, list(area.bounds)),
                indent=2,
            )
        )
        if json.loads(target.read_text())["files"]:
            download(target, root / run)
            process(root / run, polygon, database, run)
    report(database, str(today - dt.timedelta(days=final_days)), end, root / "coverage.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("catalog")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--run", choices=PRODUCTS, default="final")
    p.add_argument("--bbox", type=float, nargs=4)
    p.add_argument("--output", required=True)
    p = sub.add_parser("download")
    p.add_argument("--manifest", required=True)
    p.add_argument("--folder", required=True)
    p = sub.add_parser("process")
    p.add_argument("--folder", required=True)
    p.add_argument("--polygon", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--run", choices=PRODUCTS, default="final")
    p = sub.add_parser("report")
    p.add_argument("--database", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("export")
    p.add_argument("--database", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("update")
    p.add_argument("--root", required=True)
    p.add_argument("--polygon", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--final-days", type=int, default=210)
    p.add_argument("--late-days", type=int, default=14)
    args = parser.parse_args()
    if args.command == "catalog":
        data = manifest(
            catalog(args.start, args.end, args.run, args.bbox),
            args.start,
            args.end,
            args.run,
            args.bbox,
        )
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(data, indent=2))
        print(f"{len(data['files'])} archivos; {len(data['missing_dates'])} fechas faltantes")
    elif args.command == "download":
        download(args.manifest, args.folder)
    elif args.command == "process":
        process(args.folder, args.polygon, args.database, args.run)
    elif args.command == "report":
        report(args.database, args.start, args.end, args.output)
    elif args.command == "export":
        export_csv(args.database, args.output)
    else:
        update(args.root, args.polygon, args.database, args.final_days, args.late_days)


if __name__ == "__main__":
    main()
