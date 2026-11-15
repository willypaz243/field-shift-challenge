import { nearChannel, parcelFacts } from "../farm/parcel";
import type { Point } from "../farm/types";
import type { Snapshot } from "./types";

// The synced zone says how near the zone centre is to a channel; the farmer's
// plot is a better answer. Everything that scores windows reads
// `zone.cerca_drenaje`, so overriding it here makes sowing and rotation advice
// follow the plot (the contract's meaning is kept: a value means within 200 m).
export function withParcel(
  data: Snapshot | null,
  zoneId: string,
  plot: Point | undefined,
): Snapshot | null {
  if (!data || !plot) return data;
  const facts = parcelFacts(zoneId, plot);
  if (!facts) return data;
  const zone = { ...(data.zone as Record<string, unknown>) };
  if (nearChannel(facts)) zone.cerca_drenaje = facts.canal_m;
  else delete zone.cerca_drenaje;
  return { ...data, zone } as Snapshot;
}
