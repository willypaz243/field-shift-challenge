import { initialize } from "../../offline/schema";
import { testDatabase } from "../../offline/__tests__/database";
import { fetchHistory, fetchZoneMap, MapCache } from "../fetch";
import {
  clampCenter,
  floodMarks,
  historyItems,
  imageRect,
  notice,
  projectCells,
  projectPoint,
  unproject,
} from "../map";

const center = { lat: -17.4611, lon: -66.2185 };
const view = { width: 340, height: 520 };
const cell = (lat: number, lon: number, reportes: number) => ({
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [lon - 0.005, lat - 0.005],
        [lon + 0.005, lat - 0.005],
        [lon + 0.005, lat + 0.005],
        [lon - 0.005, lat + 0.005],
        [lon - 0.005, lat - 0.005],
      ],
    ],
  },
  properties: { reportes },
});
const mapa = {
  resumen: { sin_agua_vecinos: 8, periodo_dias: 7, direccion: "este" },
  capas: {
    sin_agua: {
      type: "FeatureCollection",
      features: [cell(-17.4611, -66.2085, 8)],
    },
    inundable: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-66.2185, -17.4611] },
          properties: {},
        },
      ],
    },
  },
};

test("cells east of the plot are drawn right of the centre", () => {
  const [rect] = projectCells(mapa, center, view);
  expect(rect.x).toBeGreaterThan(view.width / 2);
  expect(Math.abs(rect.y + rect.h / 2 - view.height / 2)).toBeLessThan(1);
  expect(rect.reportes).toBe(8);
});

test("flood points are drawn where they are", () => {
  expect(floodMarks(mapa, center, view)).toEqual([{ cx: 170, cy: 260 }]);
});

test("the notice only appears when neighbours reported no water", () => {
  expect(notice(mapa)).toEqual({ vecinos: 8, direccion: "este" });
  expect(notice({ resumen: { sin_agua_vecinos: 0 } })).toBeNull();
  expect(notice(null)).toBeNull();
});

test("history is newest first", () => {
  const items = historyItems([
    { fecha: "2018-11-26", tipo: "granizo", descripcion: "Granizada" },
    { fecha: "2024-07-04", tipo: "represa_baja", valor: { nivel_pct: 18 } },
  ]);
  expect(items.map((i) => i.fecha)).toEqual(["2024-07-04", "2018-11-26"]);
  expect(items[0].nivel_pct).toBe(18);
});

test("a fetched map is kept for the next time there is no signal", async () => {
  const { db } = testDatabase();
  await initialize(db);
  const cache = new MapCache(db);
  await cache.save("D9_itocta", mapa);
  expect(await cache.read("D9_itocta")).toEqual(mapa);
  expect(await cache.read("D3_molle")).toBeNull();
});

test("a failed request gives no map instead of an error", async () => {
  const request = jest.fn().mockResolvedValue({ ok: false, status: 503 });
  expect(
    await fetchZoneMap("https://api.test", "D9_itocta", request),
  ).toBeNull();
  expect(request).toHaveBeenCalledWith("https://api.test/zones/D9_itocta/map");
  const offline = jest.fn().mockRejectedValue(new Error("network"));
  expect(
    await fetchZoneMap("https://api.test", "D9_itocta", offline),
  ).toBeNull();
});

test("history is asked for the exact range", async () => {
  const request = jest
    .fn()
    .mockResolvedValue({ ok: true, json: async () => ({ dias: [] }) });
  expect(
    await fetchHistory(
      "https://api.test",
      "D9_itocta",
      "2026-10-19",
      "2026-11-15",
      request,
    ),
  ).toEqual({ dias: [] });
  expect(request).toHaveBeenCalledWith(
    "https://api.test/zones/D9_itocta/history?desde=2026-10-19&hasta=2026-11-15",
  );
});

test("a tap on the map gives back the coordinates it shows", () => {
  const tapped = { lat: -17.455, lon: -66.21 };
  const { x, y } = projectPoint(center, view, tapped);
  const back = unproject(center, view, x, y);
  expect(back.lat).toBeCloseTo(tapped.lat, 9);
  expect(back.lon).toBeCloseTo(tapped.lon, 9);
});

test("the GAMC image is placed by its bounding box around the plot", () => {
  const rect = imageRect(
    center,
    view,
    [-66.2485, -17.4911, -66.1885, -17.4311],
  );
  expect(rect.left + rect.width / 2).toBeCloseTo(view.width / 2, 6);
  expect(rect.top + rect.height / 2).toBeCloseTo(view.height / 2, 6);
  expect(rect.width).toBeGreaterThan(view.width);
});

test("the view never leaves the GAMC image", () => {
  const bbox = [-66.2785, -17.5211, -66.1585, -17.4011];
  const far = clampCenter({ lat: -17.4011, lon: -66.1585 }, view, bbox);
  const rect = imageRect(far, view, bbox);
  expect(rect.left).toBeLessThanOrEqual(0.001);
  expect(rect.top).toBeLessThanOrEqual(0.001);
  expect(rect.left + rect.width).toBeGreaterThanOrEqual(view.width - 0.1);
  expect(rect.top + rect.height).toBeGreaterThanOrEqual(view.height - 0.1);
  expect(clampCenter(center, view, bbox)).toEqual(center);
});
