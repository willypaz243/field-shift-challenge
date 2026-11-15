import type { SQLiteDatabase } from "expo-sqlite";
import type { MyCrop } from "../farm/my-crops";
import type { Submission } from "../offline/types";
import { uuid } from "../offline/uuid";

export type ReminderType =
  "cosecha_en_7" | "cosecha_manana" | "cosecha_hoy" | "como_salio";
export type Reminder = {
  id: string;
  crop: MyCrop;
  fecha: string;
  tipo: ReminderType;
};
export type HarvestState = { resultado?: string; preguntar_desde?: string };
export type Resultado = "buena" | "regular" | "mala";

const OFFSETS: [number, ReminderType][] = [
  [7, "cosecha_en_7"],
  [1, "cosecha_manana"],
  [0, "cosecha_hoy"],
  [-1, "como_salio"],
];
const RECENT_DAYS = 14;
// API-CONTRACT §3.2: the app marks a monthly risk from a 20 % share of years.
const RISK_SHARE = 0.2;

function addDays(iso: string, n: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return date.toISOString().slice(0, 10);
}

export function reminderPlan(crops: MyCrop[]): Reminder[] {
  return crops
    .filter((c) => !c.planificado)
    .flatMap((crop) =>
      OFFSETS.map(([before, tipo]) => ({
        id: `${crop.id}:${before}`,
        crop,
        fecha: addDays(crop.cosecha, -before),
        tipo,
      })),
    )
    .sort((a, b) => a.fecha.localeCompare(b.fecha));
}

export function recentReminders(crops: MyCrop[], today: string) {
  const from = addDays(today, -RECENT_DAYS);
  return reminderPlan(crops)
    .filter((r) => r.fecha <= today && r.fecha >= from)
    .reverse();
}

export function dueHarvest(
  crops: MyCrop[],
  states: Map<string, HarvestState>,
  today: string,
) {
  return (
    crops.find((c) => {
      if (c.planificado || addDays(c.cosecha, 1) > today) return false;
      const state = states.get(c.id);
      if (state?.resultado) return false;
      return !state?.preguntar_desde || state.preguntar_desde <= today;
    }) ?? null
  );
}

export function feedbackFor(
  crop: MyCrop,
  zone: string,
  resultado: Resultado,
): Omit<Submission, "attempts" | "next_attempt"> {
  return {
    id: uuid(),
    kind: "feedback",
    payload: {
      zone_id: zone,
      crop_id: crop.crop_id,
      siembra: crop.siembra,
      cosecha: crop.cosecha,
      resultado,
    },
  };
}

export type TimelineMonth = {
  anio: number;
  mes: number;
  etapa: string;
  helada: boolean;
};

export function monthTimeline(
  crop: Pick<MyCrop, "siembra" | "cosecha">,
  etapas: [number, string][],
  climatologia: unknown,
): TimelineMonth[] {
  const meses =
    (climatologia as { meses?: { mes: number; p_helada?: number }[] } | null)
      ?.meses ?? [];
  const sown = new Date(`${crop.siembra}T00:00:00Z`).getTime();
  const months: TimelineMonth[] = [];
  let year = Number(crop.siembra.slice(0, 4));
  let month = Number(crop.siembra.slice(5, 7));
  const lastKey = crop.cosecha.slice(0, 7);
  for (;;) {
    const key = `${year}-${String(month).padStart(2, "0")}`;
    const monthEnd = Date.UTC(year, month, 0);
    const day = Math.floor((monthEnd - sown) / 86_400_000);
    let etapa = etapas.filter(([d]) => d <= day).at(-1)?.[1] ?? "siembra";
    if (key === crop.siembra.slice(0, 7)) etapa = "siembra";
    if (key === lastKey) etapa = "cosecha";
    const p = meses.find((m) => m.mes === month)?.p_helada ?? 0;
    months.push({ anio: year, mes: month, etapa, helada: p >= RISK_SHARE });
    if (key >= lastKey) break;
    month += 1;
    if (month > 12) [month, year] = [1, year + 1];
  }
  return months;
}

export class Harvests {
  constructor(private db: SQLiteDatabase) {}

  async all() {
    const rows = await this.db.getAllAsync<{
      id: string;
      resultado: string | null;
      preguntar_desde: string | null;
    }>("SELECT id, resultado, preguntar_desde FROM harvests");
    return new Map<string, HarvestState>(
      rows.map((r) => [
        r.id,
        {
          ...(r.resultado ? { resultado: r.resultado } : {}),
          ...(r.preguntar_desde ? { preguntar_desde: r.preguntar_desde } : {}),
        },
      ]),
    );
  }

  async answer(id: string, resultado: Resultado) {
    await this.db.runAsync(
      "INSERT INTO harvests (id, resultado) VALUES (?, ?) ON CONFLICT (id) DO UPDATE SET resultado = excluded.resultado",
      id,
      resultado,
    );
  }

  async postpone(id: string, until: string) {
    await this.db.runAsync(
      "INSERT INTO harvests (id, preguntar_desde) VALUES (?, ?) ON CONFLICT (id) DO UPDATE SET preguntar_desde = excluded.preguntar_desde",
      id,
      until,
    );
  }
}

export type CropEvent = {
  fecha: string;
  tipo: "siembra" | "cosecha";
  crop: MyCrop;
};

export function cropEvents(
  crops: MyCrop[],
  from: string,
  to: string,
): CropEvent[] {
  return crops
    .flatMap((crop) => [
      { fecha: crop.siembra, tipo: "siembra" as const, crop },
      { fecha: crop.cosecha, tipo: "cosecha" as const, crop },
    ])
    .filter((e) => e.fecha >= from && e.fecha <= to)
    .sort((a, b) => a.fecha.localeCompare(b.fecha));
}
