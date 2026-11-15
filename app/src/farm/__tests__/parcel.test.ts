import { nearChannel, parcelFacts } from "../parcel";
import { zones } from "../zones";

test("a point outside the zone map has no facts", () => {
  expect(parcelFacts("D9_itocta", { lat: 0, lon: 0 })).toBeNull();
  expect(parcelFacts("D99_x", { lat: -17.46, lon: -66.21 })).toBeNull();
});

test("every zone centre falls on a cell with a distance and a class", () => {
  for (const zone of zones) {
    const facts = parcelFacts(zone.id, zone);
    expect(facts).not.toBeNull();
    expect(facts!.canal_m % 20).toBe(0);
    expect(facts!.canal_m).toBeLessThanOrEqual(600);
  }
});

test("nearby cells differ: the facts follow the plot, not the zone", () => {
  const base = zones.find((z) => z.id === "D14_valle_hermoso")!;
  const seen = new Set<number>();
  for (let i = -6; i <= 6; i++)
    seen.add(
      parcelFacts(base.id, { lat: base.lat, lon: base.lon + i * 0.002 })!
        .canal_m,
    );
  expect(seen.size).toBeGreaterThan(2);
});

test("near a channel means within 200 m", () => {
  expect(nearChannel({ canal_m: 200, periurbano: null })).toBe(true);
  expect(nearChannel({ canal_m: 220, periurbano: null })).toBe(false);
  expect(nearChannel(null)).toBe(false);
});
