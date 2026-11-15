import type { Priority } from "../farm/types";
import type { Submission } from "../offline/types";
import { uuid } from "../offline/uuid";

export type Rotation = {
  id: string;
  secuencia: (string | null)[];
  actual_tipica?: boolean;
  meses_sin_cultivo?: number;
  puntaje?: Partial<Record<Priority, number>>;
  etiquetas?: [string, "bien" | "mal" | "neutro"][];
  por_que?: string;
  bueno?: string[];
  riesgos?: string[];
  falta_saber?: string[];
  evidencia?: { codigo: string; fuente?: string }[];
  confianza?: string;
};
export type RankedRotation = Rotation & { mejor: boolean; actual: boolean };

// API-CONTRACT §4: next sowing = harvest + about one month.
const GAP_DAYS = 30;
// API-CONTRACT §2.4: dry season April to September.
const DRY_MONTHS = [4, 5, 6, 7, 8, 9];

function addDays(iso: string, n: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return date.toISOString().slice(0, 10);
}

const isCurrent = (r: Rotation) => !!r.actual_tipica || r.secuencia[1] == null;

export function rotationsFor(rotaciones: unknown, cropId: string): Rotation[] {
  const list =
    (rotaciones as { rotaciones?: Rotation[] } | null)?.rotaciones ?? [];
  const mine = list.filter((r) => r.secuencia?.[0] === cropId);
  return [...mine.filter(isCurrent), ...mine.filter((r) => !isCurrent(r))];
}

export function rankFor(list: Rotation[], goal: Priority): RankedRotation[] {
  const current = list.filter(isCurrent);
  const others = list
    .filter((r) => !isCurrent(r))
    .sort((a, b) => (b.puntaje?.[goal] ?? 0) - (a.puntaje?.[goal] ?? 0));
  return [
    ...current.map((r) => ({ ...r, actual: true, mejor: false })),
    ...others.map((r, i) => ({ ...r, actual: false, mejor: i === 0 })),
  ];
}

export function planDates(harvest: string, cycle: number) {
  const siembra = addDays(harvest, GAP_DAYS);
  return { siembra, cosecha: addDays(siembra, cycle) };
}

export function season(iso: string): "seca" | "lluvias" {
  return DRY_MONTHS.includes(Number(iso.slice(5, 7))) ? "seca" : "lluvias";
}

export function defaultGoal(
  saved: Priority | undefined,
  nextSowing: string,
): Priority {
  return saved ?? (season(nextSowing) === "seca" ? "agua" : "tierra");
}

export function planFor(
  rotation: Pick<Rotation, "id" | "secuencia">,
  zone: string,
  siembra: string,
): Omit<Submission, "attempts" | "next_attempt"> {
  return {
    id: uuid(),
    kind: "plans",
    payload: { zone_id: zone, rotacion_id: rotation.id, siembra },
  };
}
