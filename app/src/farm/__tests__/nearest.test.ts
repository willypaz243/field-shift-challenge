import { nearestZone } from "../nearest";

const zones = [
  { id: "D9_itocta", nombre: "Itocta", lat: -17.4611, lon: -66.2185 },
  { id: "D3_molle", nombre: "El Molle", lat: -17.3707, lon: -66.1922 },
];

test("picks the zone closest to the phone", () => {
  expect(nearestZone(zones, { lat: -17.37, lon: -66.19 })?.id).toBe("D3_molle");
  expect(nearestZone(zones, { lat: -17.47, lon: -66.22 })?.id).toBe(
    "D9_itocta",
  );
});

test("returns nothing when there are no zones", () => {
  expect(nearestZone([], { lat: -17.4, lon: -66.2 })).toBeNull();
});
