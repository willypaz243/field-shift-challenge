import { initialize } from "../../offline/schema";
import { testDatabase } from "../../offline/__tests__/database";
import { alertRows, newCount, SeenAlerts } from "../alerts";
import { notificationPlan } from "../plan";

const alertas = [
  { id: "represa_baja", tipo: "represa_baja", valor: { nivel_pct: 34 } },
  {
    id: "granizo-2026-11-26",
    tipo: "granizo",
    fecha_evento: "2026-11-26",
    confianza: "baja",
  },
  {
    id: "helada-2026-11-21",
    tipo: "helada",
    fecha_evento: "2026-11-21",
    momento: "madrugada",
    valor: { tmin: -2 },
    confianza: "alta",
    volver_a_avisar: "2026-11-20",
  },
];

test("dated alerts come first by date, the reservoir last, new ones marked", () => {
  const rows = alertRows(alertas, new Set(["granizo-2026-11-26"]));
  expect(rows.map((r) => [r.id, r.nuevo])).toEqual([
    ["helada-2026-11-21", true],
    ["granizo-2026-11-26", false],
    ["represa_baja", true],
  ]);
  expect(newCount(alertas, new Set(["granizo-2026-11-26"]))).toBe(2);
});

test("notifications go out at 6:00 La Paz, 7 days and 1 day before", () => {
  const plan = notificationPlan(alertas, new Date("2026-11-10T12:00:00Z"));
  expect(plan.map((p) => [p.id, p.at.toISOString()])).toEqual([
    ["helada-2026-11-21:7", "2026-11-14T10:00:00.000Z"],
    ["helada-2026-11-21:1", "2026-11-20T10:00:00.000Z"],
    ["granizo-2026-11-26:1", "2026-11-25T10:00:00.000Z"],
  ]);
});

test("low-confidence alerts skip the 7-day notice and past times are dropped", () => {
  const plan = notificationPlan(alertas, new Date("2026-11-20T11:00:00Z"));
  expect(plan.map((p) => p.id)).toEqual(["granizo-2026-11-26:1"]);
});

test("seen alerts are remembered on the phone", async () => {
  const { db } = testDatabase();
  await initialize(db);
  const seen = new SeenAlerts(db);
  expect(await seen.read()).toEqual(new Set());
  await seen.add(["a", "b"]);
  await seen.add(["b", "c"]);
  expect(await seen.read()).toEqual(new Set(["a", "b", "c"]));
});
