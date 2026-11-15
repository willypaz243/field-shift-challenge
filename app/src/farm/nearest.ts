import type { Point, Zone } from "./types";

const EARTH_KM = 6371;

function distanceKm(a: Point, b: Point) {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLon = (b.lon - a.lon) * rad;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_KM * Math.asin(Math.sqrt(h));
}

export function nearestZone(zones: Zone[], point: Point): Zone | null {
  let best: Zone | null = null;
  let bestKm = Infinity;
  for (const zone of zones) {
    const km = distanceKm(zone, point);
    if (km < bestKm) [best, bestKm] = [zone, km];
  }
  return best;
}
