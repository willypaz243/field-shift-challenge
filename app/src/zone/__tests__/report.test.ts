import { newReport, reportTypes } from "../report";

test("a report carries the event, the zone, the rounded plot and when it happened", () => {
  const now = new Date("2026-11-16T10:00:00Z");
  const report = newReport(
    "sin_agua",
    "D9_itocta",
    { lat: -17.46123, lon: -66.21849 },
    now,
  );
  expect(report.kind).toBe("reports");
  expect(report.payload).toEqual({
    tipo: "sin_agua",
    zone_id: "D9_itocta",
    lat: -17.461,
    lon: -66.218,
    ocurrido_en: "2026-11-16T10:00:00.000Z",
  });
});

test("each report gets its own idempotency key", () => {
  const ids = new Set(
    Array.from({ length: 50 }, () => newReport("helada", "D9_itocta").id),
  );
  expect(ids.size).toBe(50);
  for (const id of ids)
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
});

test("without a plot the report is sent without location", () => {
  expect(newReport("plaga", "D9_itocta").payload).not.toHaveProperty("lat");
  expect(reportTypes).toEqual([
    "sin_agua",
    "helada",
    "granizo",
    "inundacion",
    "plaga",
  ]);
});

test("a photo travels with the report as a file reference", () => {
  const foto = {
    uri: "file:///docs/reports/1.jpg",
    name: "foto.jpg",
    type: "image/jpeg",
  };
  expect(
    newReport("plaga", "D9_itocta", undefined, new Date(), foto).payload.foto,
  ).toEqual(foto);
});
