import { readFileSync } from "node:fs";
import { join } from "node:path";
import { pyRound, scoreWindow, scoreWindows } from "../scoring";

type Vector = {
  id: string;
  entrada: {
    cultivo: Parameters<typeof scoreWindow>[0];
    zona: Parameters<typeof scoreWindow>[1];
    tmean: number[];
    tmin: number[];
    pmm: number[];
    et0: number[];
    horizon?: number | null;
    pos?: number;
    umbral_bueno?: number;
    umbral_malo?: number;
  };
  esperado: ReturnType<typeof scoreWindow>;
};

const vectors: Vector[] = JSON.parse(
  readFileSync(
    join(__dirname, "../../../../data/model/test_vectors.json"),
    "utf8",
  ),
).vectores;

test.each(vectors.map((v) => [v.id, v] as const))(
  "%s matches the Python reference",
  (_, v) => {
    const e = v.entrada;
    const got = scoreWindow(e.cultivo, e.zona, e.tmean, e.tmin, e.pmm, e.et0, {
      horizon: e.horizon ?? undefined,
      pos: e.pos ?? 0,
      umbralBueno: e.umbral_bueno,
      umbralMalo: e.umbral_malo,
    });
    expect(Math.abs(got.score - v.esperado.score)).toBeLessThanOrEqual(0.5);
    expect(got.veredicto).toBe(v.esperado.veredicto);
    expect(got.confianza).toBeCloseTo(v.esperado.confianza, 2);
    expect(got.motivos).toEqual(v.esperado.motivos);
    expect(got.detalle).toEqual(v.esperado.detalle);
  },
);

test("Python rounding sends exact halves to the even neighbour", () => {
  expect([
    pyRound(0.125, 2),
    pyRound(2.5, 0),
    pyRound(3.5, 0),
    pyRound(1.25, 1),
  ]).toEqual([0.12, 2, 4, 1.2]);
});

test("a month of windows for a 120-day crop takes well under 300 ms", () => {
  const H = 365;
  const dates = Array.from({ length: H }, (_, i) =>
    new Date(Date.UTC(2026, 10, 16 + i)).toISOString().slice(0, 10),
  );
  const series = (v: number) =>
    Array.from({ length: H }, (_, i) => v + Math.sin(i / 20) * 5);
  const crop = {
    id: "papa",
    ciclo_dias: [110, 130] as [number, number],
    temp: { tmean_opt: [12, 20] as [number, number] },
    helada: { tolerancia: "baja" },
    kc: { inicial: 0.5, medio: 1.15, final: 0.75 },
    drought_tolerant: "no",
  };
  const start = Date.now();
  const top = scoreWindows(
    crop,
    { cerca_drenaje: null },
    dates.slice(0, 150),
    series(15),
    series(4),
    series(3),
    series(4),
  );
  expect(Date.now() - start).toBeLessThan(300);
  expect(top.length).toBeGreaterThan(0);
  for (let i = 1; i < top.length; i++)
    expect(top[i - 1].score).toBeGreaterThanOrEqual(top[i].score);
});
