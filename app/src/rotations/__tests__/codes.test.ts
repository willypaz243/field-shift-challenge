import { parseCode } from "../codes";

test("month ranges become readable values", () => {
  expect(parseCode("heladas_may_ago")).toEqual({
    key: "heladas_rango",
    values: { desde: "mayo", hasta: "agosto" },
  });
  expect(parseCode("poca_lluvia_sep")).toEqual({
    key: "poca_lluvia_mes",
    values: { desde: "septiembre" },
  });
});

test("a price code carries the crop id", () => {
  expect(parseCode("precio_haba")).toEqual({
    key: "precio",
    values: { cultivo: "haba" },
  });
});

test("plain codes and unknown months are left to the translation table", () => {
  expect(parseCode("abona_tierra")).toBeNull();
  expect(parseCode("heladas_xyz_abc")).toBeNull();
});
