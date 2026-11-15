import { zoneLabel, zones } from "../zones";

test("ships every farming zone with its position", () => {
  expect(zones.length).toBeGreaterThan(0);
  for (const zone of zones) {
    expect(zone.id).toMatch(/^D\d+_/);
    expect(Number.isFinite(zone.lat) && Number.isFinite(zone.lon)).toBe(true);
  }
});

test("names the zone with its district", () => {
  expect(
    zoneLabel({
      id: "D9_itocta",
      nombre: "Itocta",
      distrito: 9,
      lat: 0,
      lon: 0,
    }),
  ).toBe("Itocta · Distrito 9");
  expect(
    zoneLabel({
      id: "D1_x",
      nombre: "Tunari (valle + alturas)",
      lat: 0,
      lon: 0,
    }),
  ).toBe("Tunari");
});
