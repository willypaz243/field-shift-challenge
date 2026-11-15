import { scoreWindows, type Crop, type RankedWindow } from "./scoring";

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

// Runs on the phone over the synced forecast: windows start tomorrow and the
// series must be continuous, so it stops at the first incomplete day.
export function windowsFor(
  snapshot: unknown,
  cropId: string,
  today: string,
): RankedWindow[] {
  const data = snapshot as Snapshot | null;
  const crop = data?.crops?.crops?.find((c) => c.id === cropId);
  if (!crop) return [];
  const all = (data?.forecast?.dias ?? []).filter(
    (d) => d.fecha && d.fecha > today,
  );
  const days: Required<ForecastDay>[] = [];
  for (const d of all) {
    if (d.tmean == null || d.tmin == null || d.pmm == null || d.et0 == null)
      break;
    days.push(d as Required<ForecastDay>);
  }
  if (days.length === 0) return [];
  return scoreWindows(
    crop,
    { cerca_drenaje: data?.zone?.cerca_drenaje ?? null },
    days.map((d) => d.fecha),
    days.map((d) => d.tmean),
    days.map((d) => d.tmin),
    days.map((d) => d.pmm),
    days.map((d) => d.et0),
  );
}
