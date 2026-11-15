import grid from "../../../data/gamc/04/zonas/grid.json";
import type { Point } from "./types";

type Entry = {
  bbox: number[];
  cols: number;
  rows: number;
  paso_m: number;
  drenaje: string;
  periurbano: string;
};

export type ParcelFacts = {
  canal_m: number;
  periurbano: "consolidado" | "crecimiento" | null;
};

// The scoring and the zone flags use 200 m as "near a channel".
export const NEAR_CHANNEL_M = 200;
const URBAN = [null, "consolidado", "crecimiento"] as const;

// Reads the grid made by src/etl/gamc_parcel_grid.py (cells of about 100 m, so
// distances are good to roughly 100 m). The GAMC has no plot layer: this is
// the cell where the farmer's point falls.
export function parcelFacts(zoneId: string, plot: Point): ParcelFacts | null {
  const entry = (grid.zonas as Record<string, Entry>)[zoneId];
  if (!entry) return null;
  const [west, south, east, north] = entry.bbox;
  if (
    plot.lon < west ||
    plot.lon > east ||
    plot.lat < south ||
    plot.lat > north
  )
    return null;
  const col = Math.min(
    entry.cols - 1,
    Math.floor(((plot.lon - west) / (east - west)) * entry.cols),
  );
  const row = Math.min(
    entry.rows - 1,
    Math.floor(((north - plot.lat) / (north - south)) * entry.rows),
  );
  const i = row * entry.cols + col;
  return {
    canal_m: parseInt(entry.drenaje[i], 36) * entry.paso_m,
    periurbano: URBAN[Number(entry.periurbano[i])],
  };
}

export function nearChannel(facts: ParcelFacts | null) {
  return facts !== null && facts.canal_m <= NEAR_CHANNEL_M;
}
