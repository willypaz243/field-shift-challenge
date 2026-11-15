import { initialize } from "../../offline/schema";
import { testDatabase } from "../../offline/__tests__/database";
import { MyCrops } from "../../farm/my-crops";
import {
  addDays,
  bestNow,
  cycleDays,
  dayVerdicts,
  monthGrid,
  scoreFrom,
} from "../sow";

const crop = {
  id: "rapido",
  nombre: "Rápido",
  ciclo_dias: [8, 12],
  temp: { tmean_opt: [15, 20] },
  helada: { tolerancia: "baja" },
  kc: { inicial: 1, medio: 1, final: 1 },
  drought_tolerant: "no",
};

function snapshot(tmeanOf: (i: number) => number) {
  const dias = Array.from({ length: 60 }, (_, i) => ({
    fecha: addDays("2026-11-17", i),
    tmean: tmeanOf(i),
    tmin: 5,
    pmm: 4,
    et0: 2,
  }));
  return { crops: { crops: [crop] }, zone: {}, forecast: { dias } };
}

test("the cycle is the mean of the catalog range", () => {
  expect(cycleDays(crop)).toBe(10);
  expect(addDays("2026-11-16", 10)).toBe("2026-11-26");
});

test("every sowing day inside the forecast gets a verdict", () => {
  const verdicts = dayVerdicts(
    snapshot(() => 17),
    "rapido",
    "2026-11-16",
  );
  expect(verdicts.get("2026-11-17")).toBe("bueno");
  expect(verdicts.size).toBe(51);
  expect(verdicts.has("2027-01-10")).toBe(false);
});

test("hot days lower the sowing days that cover them", () => {
  const verdicts = dayVerdicts(
    snapshot((i) => (i >= 20 ? 30 : 17)),
    "rapido",
    "2026-11-16",
  );
  expect(verdicts.get("2026-11-17")).toBe("bueno");
  expect(verdicts.get("2026-12-15")).toBe("con_cuidado");
});

test("best season means a good sowing day within the next 30 days", () => {
  expect(
    bestNow(
      snapshot(() => 17),
      "rapido",
      "2026-11-16",
    ),
  ).toBe(true);
  expect(
    bestNow(
      snapshot(() => 30),
      "rapido",
      "2026-11-16",
    ),
  ).toBe(false);
});

test("the month grid has 6 rows starting on Monday", () => {
  const grid = monthGrid(2026, 11);
  expect(grid).toHaveLength(42);
  expect(grid.slice(0, 7)).toEqual([
    null,
    null,
    null,
    null,
    null,
    null,
    "2026-11-01",
  ]);
  expect(grid[35]).toBe("2026-11-30");
});

test("added crops stay on the phone", async () => {
  const { db } = testDatabase();
  await initialize(db);
  const mine = new MyCrops(db);
  await mine.add({
    crop_id: "haba",
    siembra: "2026-11-20",
    cosecha: "2027-04-19",
  });
  const [saved] = await mine.list();
  expect(saved).toMatchObject({
    crop_id: "haba",
    siembra: "2026-11-20",
    cosecha: "2027-04-19",
    planificado: false,
  });
  expect(saved.id).toBeTruthy();
});

test("the score of one sowing day explains its verdict", () => {
  const data = snapshot((i) => (i < 3 ? 30 : 17));
  const score = scoreFrom(data, "rapido", "2026-11-16", "2026-11-17");
  expect(score?.motivos).toEqual(["temp_fuera_rango"]);
  expect(scoreFrom(data, "rapido", "2026-11-16", "2027-02-01")).toBeNull();
});
