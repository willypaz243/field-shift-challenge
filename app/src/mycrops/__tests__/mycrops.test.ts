import { initialize } from "../../offline/schema";
import { testDatabase } from "../../offline/__tests__/database";
import { MyCrops } from "../../farm/my-crops";
import {
  Harvests,
  cropEvents,
  dueHarvest,
  feedbackFor,
  monthTimeline,
  reminderPlan,
  recentReminders,
} from "../mycrops";

const haba = {
  id: "c1",
  crop_id: "haba",
  siembra: "2026-06-20",
  cosecha: "2026-11-15",
  planificado: false,
};

test("reminders go 7 days, 1 day, the same day and 1 day after the harvest", () => {
  expect(reminderPlan([haba]).map((r) => [r.id, r.fecha, r.tipo])).toEqual([
    ["c1:7", "2026-11-08", "cosecha_en_7"],
    ["c1:1", "2026-11-14", "cosecha_manana"],
    ["c1:0", "2026-11-15", "cosecha_hoy"],
    ["c1:-1", "2026-11-16", "como_salio"],
  ]);
});

test("Avisos shows the reminders of the last two weeks, newest first", () => {
  const recent = recentReminders([haba], "2026-11-15");
  expect(recent.map((r) => r.id)).toEqual(["c1:0", "c1:1", "c1:7"]);
});

test("the harvest question appears from the day after the harvest until answered", () => {
  expect(dueHarvest([haba], new Map(), "2026-11-15")).toBeNull();
  expect(dueHarvest([haba], new Map(), "2026-11-16")?.id).toBe("c1");
  expect(
    dueHarvest([haba], new Map([["c1", { resultado: "buena" }]]), "2026-11-20"),
  ).toBeNull();
  const later = new Map([["c1", { preguntar_desde: "2026-11-19" }]]);
  expect(dueHarvest([haba], later, "2026-11-18")).toBeNull();
  expect(dueHarvest([haba], later, "2026-11-19")?.id).toBe("c1");
});

test("planned crops are not asked about", () => {
  expect(
    dueHarvest([{ ...haba, planificado: true }], new Map(), "2026-11-20"),
  ).toBeNull();
});

test("the answer is sent as feedback with its own key", () => {
  const item = feedbackFor(haba, "D9_itocta", "regular");
  expect(item.kind).toBe("feedback");
  expect(item.payload).toEqual({
    zone_id: "D9_itocta",
    crop_id: "haba",
    siembra: "2026-06-20",
    cosecha: "2026-11-15",
    resultado: "regular",
  });
  expect(item.id).toMatch(/^[0-9a-f-]{36}$/);
});

test("the crop timeline names the stage and frost risk of each month", () => {
  const etapas = [
    [0, "siembra"],
    [20, "crecimiento"],
    [60, "floracion"],
    [150, "cosecha"],
  ] as [number, string][];
  const meses = [
    { mes: 6, p_helada: 0.75 },
    { mes: 7, p_helada: 0.88 },
    { mes: 11, p_helada: 0 },
  ];
  const months = monthTimeline(haba, etapas, { meses });
  expect(months.map((m) => [m.mes, m.etapa, m.helada])).toEqual([
    [6, "siembra", true],
    [7, "crecimiento", true],
    [8, "floracion", false],
    [9, "floracion", false],
    [10, "floracion", false],
    [11, "cosecha", false],
  ]);
});

test("answers and postponements are kept on the phone", async () => {
  const { db } = testDatabase();
  await initialize(db);
  const harvests = new Harvests(db);
  await harvests.postpone("c1", "2026-11-19");
  await harvests.answer("c1", "mala");
  expect((await harvests.all()).get("c1")).toEqual({
    resultado: "mala",
    preguntar_desde: "2026-11-19",
  });
  const mine = new MyCrops(db);
  await mine.add({
    crop_id: "papa",
    siembra: "2026-09-01",
    cosecha: "2027-01-30",
  });
  expect((await mine.list())[0].crop_id).toBe("papa");
});

test("calendar events are the sowing and harvest days inside the range", () => {
  const papa = {
    ...haba,
    id: "c2",
    crop_id: "papa",
    siembra: "2026-11-20",
    cosecha: "2027-04-10",
  };
  expect(
    cropEvents([haba, papa], "2026-11-10", "2026-12-08").map((e) => [
      e.fecha,
      e.tipo,
      e.crop.id,
    ]),
  ).toEqual([
    ["2026-11-15", "cosecha", "c1"],
    ["2026-11-20", "siembra", "c2"],
  ]);
});
