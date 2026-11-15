import { laPazToday, longDate, weekday } from "../dates";

test("today is the civil day in La Paz", () => {
  expect(laPazToday(new Date("2026-11-17T02:00:00Z"))).toBe("2026-11-16");
  expect(laPazToday(new Date("2026-11-17T05:00:00Z"))).toBe("2026-11-17");
});

test("dates read in plain Spanish", () => {
  expect(longDate("2026-11-16")).toBe("16 de noviembre");
  expect(weekday("2026-11-21")).toBe("sábado");
});
