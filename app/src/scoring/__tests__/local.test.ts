import { windowsFor } from "../local";

const crop = {
  id: "rapido",
  ciclo_dias: [10, 10],
  temp: { tmean_opt: [15, 20] },
  helada: { tolerancia: "media" },
  kc: { inicial: 1, medio: 1, final: 1 },
  drought_tolerant: "no",
};

function snapshot(days: number, gap?: number) {
  const dias = Array.from({ length: days }, (_, i) => ({
    fecha: new Date(Date.UTC(2026, 10, 16 + i)).toISOString().slice(0, 10),
    tmean: i < 15 ? 17 : 25,
    tmin: 5,
    pmm: 4,
    et0: i === gap ? undefined : 2,
  }));
  return {
    crops: { crops: [crop] },
    zone: { cerca_drenaje: 30 },
    forecast: { dias },
  };
}

test("ranks windows starting tomorrow from the local forecast", () => {
  const top = windowsFor(snapshot(60), "rapido", "2026-11-16");
  expect(top[0].inicio).toBe("2026-11-17");
  expect(top[0].veredicto).toBe("bueno");
});

test("an unknown crop or an empty forecast gives no windows", () => {
  expect(windowsFor(snapshot(60), "otro", "2026-11-16")).toEqual([]);
  expect(windowsFor(null, "rapido", "2026-11-16")).toEqual([]);
});

test("the series stops at the first day without all the variables", () => {
  const top = windowsFor(snapshot(60, 25), "rapido", "2026-11-16");
  expect(top.every((w) => w.fin < "2026-12-11")).toBe(true);
});
