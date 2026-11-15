// Interpretation rules from API-CONTRACT §2.4.
export type RainWord = "sin_lluvia" | "debil" | "moderada" | "fuerte";
export type DayIcon = "granizo" | "helada" | "lluvia" | "sol";

type DayData = { tmin: number; pmm: number; granizo?: boolean };
export type Today = {
  fecha: string;
  tmin: number;
  tmax: number;
  pmm: number;
  granizo?: boolean;
  proyeccion: boolean;
};
type Alert = {
  tipo: string;
  fecha_evento?: string;
  valor?: { nivel_pct?: number; tmin?: number };
};
export type AlertStrip =
  | { tipo: string; fecha: string; tmin?: number }
  | { tipo: "represa_baja"; nivel_pct: number };

// The reservoir is loaded weekly; an older reading no longer says how much water there is.
const RESERVOIR_MAX_AGE_DAYS = 30;

export function rainWord(pmm: number): RainWord {
  if (pmm <= 0) return "sin_lluvia";
  if (pmm < 4) return "debil";
  return pmm < 15 ? "moderada" : "fuerte";
}

export function dayIcon(day: DayData): DayIcon {
  if (day.granizo) return "granizo";
  if (day.tmin < 0) return "helada";
  return day.pmm > 0 ? "lluvia" : "sol";
}

type Days = { dias?: Partial<Today>[] } | undefined;

function findDay(section: unknown, fecha: string) {
  return (section as Days)?.dias?.find((d) => d.fecha === fecha);
}

export function pickToday(snapshot: unknown, fecha: string): Today | null {
  const data = snapshot as { corto_plazo?: unknown; forecast?: unknown } | null;
  const short = findDay(data?.corto_plazo, fecha);
  const day = short ?? findDay(data?.forecast, fecha);
  if (!day || day.tmin == null || day.tmax == null || day.pmm == null)
    return null;
  return {
    fecha,
    tmin: Math.round(day.tmin),
    tmax: Math.round(day.tmax),
    pmm: day.pmm,
    ...(day.granizo ? { granizo: true } : {}),
    proyeccion: !short,
  };
}

export function alertStrip(alerts: unknown): AlertStrip | null {
  const list = (Array.isArray(alerts) ? alerts : []) as Alert[];
  const weather = list
    .filter((a) => a.fecha_evento)
    .sort((a, b) => a.fecha_evento!.localeCompare(b.fecha_evento!))[0];
  if (weather) {
    const tmin = weather.valor?.tmin;
    return {
      tipo: weather.tipo,
      fecha: weather.fecha_evento!,
      ...(tmin == null ? {} : { tmin: Math.round(tmin) }),
    };
  }
  const reservoir = list.find((a) => a.tipo === "represa_baja");
  const nivel = reservoir?.valor?.nivel_pct;
  return nivel == null ? null : { tipo: "represa_baja", nivel_pct: nivel };
}

export function reservoirStrip(
  represa: unknown,
  now = new Date(),
): { nivel_pct: number } | null {
  const r = represa as { actualizado_en?: string; nivel_pct?: number } | null;
  if (!r?.actualizado_en || r.nivel_pct == null) return null;
  const ageDays =
    (now.getTime() - new Date(r.actualizado_en).getTime()) / 86_400_000;
  return ageDays <= RESERVOIR_MAX_AGE_DAYS ? { nivel_pct: r.nivel_pct } : null;
}
