type Point = { lat: number; lon: number };
type View = { width: number; height: number };
type Feature = {
  geometry?: { type?: string; coordinates?: unknown };
  properties?: { reportes?: number };
};
type ZoneMap = {
  resumen?: { sin_agua_vecinos?: number; direccion?: string };
  capas?: Record<string, { features?: Feature[] } | undefined>;
};
export type HistoryItem = {
  fecha: string;
  tipo: string;
  descripcion?: string;
  nivel_pct?: number;
};

// About 4 km across the screen: the plot and its neighbours, not the whole valley.
const SPAN_DEG = 0.04;

function projector(center: Point, view: View) {
  const scale = view.width / SPAN_DEG;
  const shrink = Math.cos((center.lat * Math.PI) / 180);
  return ([lon, lat]: number[]) => ({
    x: view.width / 2 + (lon - center.lon) * shrink * scale,
    y: view.height / 2 - (lat - center.lat) * scale,
  });
}

// Keeps the visible window inside the georeferenced image: the map pans only as
// far as the GAMC picture goes instead of showing empty margins.
export function clampCenter(center: Point, view: View, bbox: number[]): Point {
  const [west, south, east, north] = bbox;
  const halfLon =
    view.width /
    2 /
    (view.width / SPAN_DEG) /
    Math.cos((center.lat * Math.PI) / 180);
  const halfLat = view.height / 2 / (view.width / SPAN_DEG);
  const clamp = (v: number, lo: number, hi: number) =>
    lo > hi ? (lo + hi) / 2 : Math.min(hi, Math.max(lo, v));
  return {
    lat: clamp(center.lat, south + halfLat, north - halfLat),
    lon: clamp(center.lon, west + halfLon, east - halfLon),
  };
}

export function projectPoint(center: Point, view: View, point: Point) {
  return projector(center, view)([point.lon, point.lat]);
}

// Inverse of the projection: where the farmer tapped, in coordinates.
export function unproject(
  center: Point,
  view: View,
  x: number,
  y: number,
): Point {
  const scale = view.width / SPAN_DEG;
  const shrink = Math.cos((center.lat * Math.PI) / 180);
  return {
    lat: center.lat - (y - view.height / 2) / scale,
    lon: center.lon + (x - view.width / 2) / (shrink * scale),
  };
}

// Screen rectangle of a georeferenced image ([west, south, east, north]).
export function imageRect(center: Point, view: View, bbox: number[]) {
  const [west, south, east, north] = bbox;
  const project = projector(center, view);
  const topLeft = project([west, north]);
  const bottomRight = project([east, south]);
  return {
    left: topLeft.x,
    top: topLeft.y,
    width: bottomRight.x - topLeft.x,
    height: bottomRight.y - topLeft.y,
  };
}

function features(map: unknown, layer: string) {
  return (map as ZoneMap | null)?.capas?.[layer]?.features ?? [];
}

export function projectCells(map: unknown, center: Point, view: View) {
  const project = projector(center, view);
  return features(map, "sin_agua").flatMap((f) => {
    const ring = (f.geometry?.coordinates as number[][][] | undefined)?.[0];
    if (f.geometry?.type !== "Polygon" || !ring?.length) return [];
    const points = ring.map(project);
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    const x = Math.min(...xs);
    const y = Math.min(...ys);
    return [
      {
        x,
        y,
        w: Math.max(...xs) - x,
        h: Math.max(...ys) - y,
        reportes: f.properties?.reportes ?? 0,
      },
    ];
  });
}

export function floodMarks(map: unknown, center: Point, view: View) {
  const project = projector(center, view);
  return features(map, "inundable").flatMap((f) => {
    if (f.geometry?.type !== "Point") return [];
    const { x, y } = project(f.geometry.coordinates as number[]);
    return [{ cx: Math.round(x), cy: Math.round(y) }];
  });
}

export function notice(map: unknown) {
  const resumen = (map as ZoneMap | null)?.resumen;
  const vecinos = resumen?.sin_agua_vecinos ?? 0;
  if (vecinos <= 0) return null;
  return {
    vecinos,
    ...(resumen?.direccion ? { direccion: resumen.direccion } : {}),
  };
}

export function historyItems(historial: unknown): HistoryItem[] {
  const rows = (Array.isArray(historial) ? historial : []) as (HistoryItem & {
    valor?: { nivel_pct?: number };
  })[];
  return rows
    .filter((r) => r.fecha && r.tipo)
    .map(({ fecha, tipo, descripcion, valor }) => ({
      fecha,
      tipo,
      ...(descripcion ? { descripcion } : {}),
      ...(valor?.nivel_pct == null ? {} : { nivel_pct: valor.nivel_pct }),
    }))
    .sort((a, b) => b.fecha.localeCompare(a.fecha));
}
