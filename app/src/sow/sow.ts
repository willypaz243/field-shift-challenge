import { scoreWindow, type Crop, type Veredicto } from "../scoring/scoring";

type ForecastDay = {
  fecha?: string;
  tmean?: number;
  tmin?: number;
  pmm?: number;
  et0?: number;
};
type Snapshot = {
  crops?: { crops?: Crop[] };
  zone?: { cerca_drenaje?: number | null };
  forecast?: { dias?: ForecastDay[] };
};

// "Mejor época": a good sowing day inside the next month.
const BEST_NOW_DAYS = 30;

export function addDays(iso: string, n: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return date.toISOString().slice(0, 10);
}

export function cycleDays(crop: Pick<Crop, "ciclo_dias">) {
  return Math.round((crop.ciclo_dias[0] + crop.ciclo_dias[1]) / 2);
}

export function findCrop(snapshot: unknown, cropId: string) {
  return (
    (snapshot as Snapshot | null)?.crops?.crops?.find((c) => c.id === cropId) ??
    null
  );
}

function series(snapshot: Snapshot | null, today: string) {
  const days: Required<ForecastDay>[] = [];
  for (const d of snapshot?.forecast?.dias ?? []) {
    if (!d.fecha || d.fecha <= today) continue;
    if (d.tmean == null || d.tmin == null || d.pmm == null || d.et0 == null)
      break;
    days.push(d as Required<ForecastDay>);
  }
  return days;
}

// Same scoring as src/model/scoring.py, one window per possible sowing day.
export function dayVerdicts(
  snapshot: unknown,
  cropId: string,
  today: string,
  limit?: number,
) {
  const data = snapshot as Snapshot | null;
  const crop = findCrop(data, cropId);
  const verdicts = new Map<string, Veredicto>();
  if (!crop) return verdicts;
  const days = series(data, today);
  const L = cycleDays(crop);
  const zone = { cerca_drenaje: data?.zone?.cerca_drenaje ?? null };
  const last = Math.min(days.length - L, limit == null ? Infinity : limit - 1);
  for (let s = 0; s <= last; s++) {
    const w = days.slice(s, s + L);
    const result = scoreWindow(
      crop,
      zone,
      w.map((d) => d.tmean),
      w.map((d) => d.tmin),
      w.map((d) => d.pmm),
      w.map((d) => d.et0),
      { horizon: days.length, pos: s },
    );
    verdicts.set(days[s].fecha, result.veredicto);
  }
  return verdicts;
}

export function bestNow(snapshot: unknown, cropId: string, today: string) {
  for (const verdict of dayVerdicts(
    snapshot,
    cropId,
    today,
    BEST_NOW_DAYS,
  ).values())
    if (verdict === "bueno") return true;
  return false;
}

export function monthGrid(year: number, month: number): (string | null)[] {
  const first = new Date(Date.UTC(year, month - 1, 1));
  const lead = (first.getUTCDay() + 6) % 7;
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const cells: (string | null)[] = Array(lead).fill(null);
  for (let d = 1; d <= days; d++)
    cells.push(
      `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
    );
  while (cells.length < 42) cells.push(null);
  return cells;
}

export function scoreFrom(
  snapshot: unknown,
  cropId: string,
  today: string,
  start: string,
) {
  const data = snapshot as Snapshot | null;
  const crop = findCrop(data, cropId);
  if (!crop) return null;
  const days = series(data, today);
  const s = days.findIndex((d) => d.fecha === start);
  const L = cycleDays(crop);
  if (s < 0 || s + L > days.length) return null;
  const w = days.slice(s, s + L);
  return scoreWindow(
    crop,
    { cerca_drenaje: data?.zone?.cerca_drenaje ?? null },
    w.map((d) => d.tmean),
    w.map((d) => d.tmin),
    w.map((d) => d.pmm),
    w.map((d) => d.et0),
    { horizon: days.length, pos: s },
  );
}
