import { initialize } from "../../offline/schema";
import { testDatabase } from "../../offline/__tests__/database";
import { FarmStore } from "../store";

async function store() {
  const { db } = testDatabase();
  await initialize(db);
  return new FarmStore(db);
}

test("has no farm before the first use", async () => {
  expect(await (await store()).read()).toBeNull();
});

test("keeps each answer as soon as it is given", async () => {
  const farm = await store();
  await farm.save({
    zone_id: "D9_itocta",
    parcela: { lat: -17.461, lon: -66.218 },
  });
  await farm.save({ agua: "angostura" });
  await farm.save({ prioridad: "tierra" });

  expect(await farm.read()).toEqual({
    zone_id: "D9_itocta",
    parcela: { lat: -17.461, lon: -66.218 },
    agua: "angostura",
    prioridad: "tierra",
  });
});

test("a farm without a zone is not ready", async () => {
  const farm = await store();
  await farm.save({ idioma: "qu" });

  expect(await farm.read()).toEqual({ idioma: "qu" });
});

test("a plot without real coordinates is refused", async () => {
  const farm = await store();
  await expect(
    farm.save({ parcela: { lat: NaN, lon: -66.2 } }),
  ).rejects.toThrow();
  expect(await farm.read()).toBeNull();
});
