import { buildWeeks, monthsAhead, pastWeeks, sourceLine } from "../calendar";

function days(from: string, count: number, extra: object = {}) {
  const start = new Date(`${from}T00:00:00Z`);
  return Array.from({ length: count }, (_, i) => ({
    fecha: new Date(start.getTime() + i * 86_400_000)
      .toISOString()
      .slice(0, 10),
    tmin: 8,
    tmax: 24,
    pmm: 0,
    ...extra,
  }));
}

test("four weeks start today; the short forecast covers the first two", () => {
  const weeks = buildWeeks(
    {
      corto_plazo: { dias: days("2026-11-16", 14) },
      forecast: { dias: days("2026-11-16", 40) },
    },
    "2026-11-16",
  );
  expect(weeks.map((w) => [w.inicio, w.fin, w.lejos])).toEqual([
    ["2026-11-16", "2026-11-22", false],
    ["2026-11-23", "2026-11-29", false],
    ["2026-11-30", "2026-12-06", true],
    ["2026-12-07", "2026-12-13", true],
  ]);
  expect(weeks.every((w) => w.dias.length === 7)).toBe(true);
});

test("without a short forecast every week is marked as far", () => {
  const weeks = buildWeeks(
    { corto_plazo: { dias: [] }, forecast: { dias: days("2026-11-16", 28) } },
    "2026-11-16",
  );
  expect(weeks.map((w) => w.lejos)).toEqual([true, true, true, true]);
});

test("the week tile puts hail over frost over rain", () => {
  const base = days("2026-11-16", 7);
  const tile = (change: (d: (typeof base)[number][]) => void) => {
    const week = base.map((d) => ({ ...d }));
    change(week);
    return buildWeeks(
      { corto_plazo: { dias: week }, forecast: { dias: [] } },
      "2026-11-16",
    )[0];
  };
  expect(tile(() => undefined).tile).toBe("sin_lluvia");
  expect(tile((w) => (w[2].pmm = 6)).tile).toBe("lluvia");
  expect(tile((w) => (w[2].pmm = 16)).tile).toBe("lluvia_fuerte");
  const frost = tile((w) => (w[5].tmin = -2));
  expect([frost.tile, frost.helada]).toEqual(["helada", "2026-11-21"]);
  const hail = tile((w) => {
    w[5].tmin = -2;
    Object.assign(w[3], { granizo: true });
  });
  expect([hail.tile, hail.granizo]).toEqual(["granizo", "2026-11-19"]);
});

test("a week with too few days has no tile", () => {
  const weeks = buildWeeks(
    { corto_plazo: { dias: [] }, forecast: { dias: days("2026-11-16", 9) } },
    "2026-11-16",
  );
  expect(weeks.map((w) => w.tile)).toEqual([
    "sin_lluvia",
    "sin_datos",
    "sin_datos",
    "sin_datos",
  ]);
});

test("next months come from the climatology with frost risk from 20 %", () => {
  const meses = [
    { mes: 12, pmm_total: 170, p_helada: 0 },
    { mes: 1, pmm_total: 170, p_helada: 0 },
    { mes: 4, pmm_total: 45, p_helada: 0.06 },
    { mes: 5, pmm_total: 30, p_helada: 0.69 },
  ];
  const months = monthsAhead({ meses }, "2026-11-16", 6);
  expect(months.map((m) => [m.mes, m.tile, m.helada])).toEqual([
    [12, "lluvia_fuerte", false],
    [1, "lluvia_fuerte", false],
    [4, "lluvia", false],
    [5, "helada", true],
  ]);
});

test("the source line names the NASA datasets", () => {
  expect(sourceLine(["nasa_power", "nasa_imerg"])).toBe(
    "NASA POWER · NASA IMERG",
  );
  expect(sourceLine(["nasa_geos", "otro"])).toBe("NASA GEOS · otro");
});

test("past weeks come from the measured history, newest first", () => {
  const history = {
    dias: [
      { fecha: "2026-11-10", tmin: -1.2, tmax: 25, pmm: 2 },
      { fecha: "2026-11-11", tmin: 4, tmax: 26 },
      { fecha: "2026-11-12", tmin: 5, tmax: 27, pmm: 3 },
      { fecha: "2026-11-13", tmin: 5, tmax: 27, pmm: 0 },
      { fecha: "2026-11-14", tmin: 6, tmax: 28, pmm: 0 },
    ],
  };
  const weeks = pastWeeks(history, "2026-11-16");
  expect(weeks.map((w) => w.inicio)).toEqual([
    "2026-11-09",
    "2026-11-02",
    "2026-10-26",
    "2026-10-19",
  ]);
  expect([
    weeks[0].dias.length,
    weeks[0].pmm,
    weeks[0].tile,
    weeks[0].helada,
  ]).toEqual([5, 5, "helada", "2026-11-10"]);
  expect(weeks[1].tile).toBe("sin_datos");
});
