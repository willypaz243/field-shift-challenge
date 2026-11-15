import { headerLine } from "../header-line";

test("shows the zone and the last update in Bolivian time", () => {
  expect(headerLine("Itocta", "2026-11-15T07:26:05Z")).toBe(
    "Itocta · actualizado 15 nov, 03:26",
  );
});

test("says it is looking for data before the first sync", () => {
  expect(headerLine(null, null)).toBe("Buscando datos…");
});
