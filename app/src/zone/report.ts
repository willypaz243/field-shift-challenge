import type { Point } from "../farm/types";
import type { Submission } from "../offline/types";
import { uuid } from "../offline/uuid";

export const reportTypes = [
  "sin_agua",
  "helada",
  "granizo",
  "inundacion",
  "plaga",
] as const;
export type ReportType = (typeof reportTypes)[number];

const round3 = (n: number) => Math.round(n * 1000) / 1000;

export function newReport(
  tipo: ReportType,
  zone: string,
  parcela?: Point,
  now = new Date(),
): Omit<Submission, "attempts" | "next_attempt"> {
  return {
    id: uuid(),
    kind: "reports",
    payload: {
      tipo,
      zone_id: zone,
      ...(parcela
        ? { lat: round3(parcela.lat), lon: round3(parcela.lon) }
        : {}),
      ocurrido_en: now.toISOString(),
    },
  };
}
