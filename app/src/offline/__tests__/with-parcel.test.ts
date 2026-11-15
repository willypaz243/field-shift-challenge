import { withParcel } from "../with-parcel";
import type { Snapshot } from "../types";
import { zones } from "../../farm/zones";
import { parcelFacts } from "../../farm/parcel";

const base = {
  zone: { id: "D14_valle_hermoso", cerca_drenaje: 999 },
} as unknown as Snapshot;
const centre = zones.find((z) => z.id === "D14_valle_hermoso")!;

test("without a plot the synced zone is untouched", () => {
  expect(withParcel(base, "D14_valle_hermoso", undefined)).toBe(base);
  expect(withParcel(null, "D14_valle_hermoso", centre)).toBeNull();
});

test("a plot near a channel replaces the zone value with its own distance", () => {
  const facts = parcelFacts("D14_valle_hermoso", centre)!;
  expect(facts.canal_m).toBeLessThanOrEqual(200);
  const zone = withParcel(base, "D14_valle_hermoso", centre)!.zone as {
    cerca_drenaje?: number;
  };
  expect(zone.cerca_drenaje).toBe(facts.canal_m);
});

test("a plot far from channels clears the zone value", () => {
  const far = zones.find((z) => z.id === "D1_tunari")!;
  const data = {
    zone: { id: "D1_tunari", cerca_drenaje: 50 },
  } as unknown as Snapshot;
  const zone = withParcel(data, "D1_tunari", far)!.zone as {
    cerca_drenaje?: number;
  };
  expect(zone.cerca_drenaje).toBeUndefined();
});
