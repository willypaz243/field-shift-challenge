import {
  alertStrip,
  dayIcon,
  pickToday,
  rainWord,
  reservoirStrip,
} from "../today";

const snapshot = (corto: object[], proyeccion: object[]) => ({
  corto_plazo: { dias: corto },
  forecast: { dias: proyeccion },
});

test("rain words follow the contract thresholds", () => {
  expect([0, 0.5, 3.9, 4, 14.9, 15, 40].map(rainWord)).toEqual([
    "sin_lluvia",
    "debil",
    "debil",
    "moderada",
    "moderada",
    "fuerte",
    "fuerte",
  ]);
});

test("the day icon puts hail over frost over rain over sun", () => {
  expect(dayIcon({ tmin: -2, pmm: 5, granizo: true })).toBe("granizo");
  expect(dayIcon({ tmin: -2, pmm: 5 })).toBe("helada");
  expect(dayIcon({ tmin: 0, pmm: 5 })).toBe("lluvia");
  expect(dayIcon({ tmin: 3, pmm: 0 })).toBe("sol");
});

test("today comes from the short forecast first", () => {
  const day = pickToday(
    snapshot(
      [{ fecha: "2026-11-16", tmin: 9, tmax: 24, pmm: 0 }],
      [{ fecha: "2026-11-16", tmin: 8, tmax: 22, pmm: 3 }],
    ),
    "2026-11-16",
  );
  expect(day).toEqual({
    fecha: "2026-11-16",
    tmin: 9,
    tmax: 24,
    pmm: 0,
    proyeccion: false,
  });
});

test("without a short forecast today comes from the projection, marked", () => {
  const day = pickToday(
    snapshot([], [{ fecha: "2026-11-16", tmin: 8.4, tmax: 22.6, pmm: 3.1 }]),
    "2026-11-16",
  );
  expect(day).toEqual({
    fecha: "2026-11-16",
    tmin: 8,
    tmax: 23,
    pmm: 3.1,
    proyeccion: true,
  });
});

test("there is no day when nothing covers today", () => {
  expect(pickToday(snapshot([], []), "2026-11-16")).toBeNull();
  expect(pickToday(null, "2026-11-16")).toBeNull();
});

test("the alert strip shows the nearest weather alert", () => {
  const strip = alertStrip([
    { id: "represa_baja", tipo: "represa_baja", valor: { nivel_pct: 15 } },
    {
      id: "h",
      tipo: "helada",
      fecha_evento: "2026-11-21",
      valor: { tmin: -2 },
    },
    { id: "g", tipo: "granizo", fecha_evento: "2026-11-19" },
  ]);
  expect(strip).toEqual({ tipo: "granizo", fecha: "2026-11-19" });
});

test("a frost alert carries its temperature", () => {
  expect(
    alertStrip([
      { tipo: "helada", fecha_evento: "2026-11-21", valor: { tmin: -2.4 } },
    ]),
  ).toEqual({ tipo: "helada", fecha: "2026-11-21", tmin: -2 });
});

test("the alert strip falls back to the reservoir alert", () => {
  expect(
    alertStrip([{ id: "r", tipo: "represa_baja", valor: { nivel_pct: 15 } }]),
  ).toEqual({
    tipo: "represa_baja",
    nivel_pct: 15,
  });
  expect(alertStrip([])).toBeNull();
});

test("the reservoir strip only shows a recent reading", () => {
  const now = new Date("2026-11-16T12:00:00Z");
  expect(
    reservoirStrip(
      { actualizado_en: "2026-11-10T00:00:00", nivel_pct: 34 },
      now,
    ),
  ).toEqual({ nivel_pct: 34 });
  expect(
    reservoirStrip(
      { actualizado_en: "2002-11-27T00:00:00", nivel_pct: 5 },
      now,
    ),
  ).toBeNull();
  expect(reservoirStrip(null, now)).toBeNull();
});
