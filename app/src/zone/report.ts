import type { Point } from "../farm/types";
import type { Submission } from "../offline/types";

export const reportTypes = [
  "sin_agua",
  "helada",
  "granizo",
  "inundacion",
  "plaga",
] as const;
export type ReportType = (typeof reportTypes)[number];

const round3 = (n: number) => Math.round(n * 1000) / 1000;

function uuid() {
  const hex = Array.from({ length: 32 }, () =>
    Math.floor(Math.random() * 16).toString(16),
  );
  hex[12] = "4";
  hex[16] = ((parseInt(hex[16], 16) & 0x3) | 0x8).toString(16);
  const s = hex.join("");
  return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${s.slice(16, 20)}-${s.slice(20)}`;
}

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
