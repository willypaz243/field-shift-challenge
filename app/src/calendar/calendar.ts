export type WeekTile =
  | "granizo"
  | "helada"
  | "lluvia_fuerte"
  | "lluvia"
  | "sin_lluvia"
  | "sin_datos";
export type MonthTile =
  "helada" | "lluvia_fuerte" | "lluvia" | "poca_lluvia" | "seco";

export type CalendarDay = {
  fecha: string;
  tmin: number;
  tmax: number;
  pmm: number;
  granizo?: boolean;
  proyeccion: boolean;
};
export type Week = {
  inicio: string;
  fin: string;
  dias: CalendarDay[];
  lejos: boolean;
  tile: WeekTile;
  pmm: number;
  helada?: string;
  granizo?: string;
};
export type Month = { mes: number; tile: MonthTile; helada: boolean };

const SHORT_WEEKS = 2;
// A week tile needs most of its days to say something about the week.
const MIN_DAYS = 4;
// API-CONTRACT §3.2: the app marks a monthly risk from a 20 % share of years.
const RISK_SHARE = 0.2;
const FROSTY_MONTH = 0.5;
const SOURCES: Record<string, string> = {
  nasa_power: "NASA POWER",
  nasa_imerg: "NASA IMERG",
  nasa_smap: "NASA SMAP",
  nasa_geos: "NASA GEOS",
};

type RawDay = Partial<Omit<CalendarDay, "proyeccion">>;

function addDays(iso: string, n: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return date.toISOString().slice(0, 10);
}

function byDate(section: unknown) {
  const dias = (section as { dias?: RawDay[] } | undefined)?.dias ?? [];
  return new Map(dias.filter((d) => d.fecha).map((d) => [d.fecha!, d]));
}

function tileOf(dias: CalendarDay[], pmm: number): WeekTile {
  if (dias.length < MIN_DAYS) return "sin_datos";
  if (dias.some((d) => d.granizo)) return "granizo";
  if (dias.some((d) => d.tmin < 0)) return "helada";
  if (pmm >= 15) return "lluvia_fuerte";
  return pmm >= 4 ? "lluvia" : "sin_lluvia";
}

export function buildWeeks(snapshot: unknown, today: string): Week[] {
  const data = snapshot as { corto_plazo?: unknown; forecast?: unknown } | null;
  const short = byDate(data?.corto_plazo);
  const projection = byDate(data?.forecast);
  return [0, 1, 2, 3].map((k) => {
    const inicio = addDays(today, k * 7);
    const dias: CalendarDay[] = [];
    for (let i = 0; i < 7; i++) {
      const fecha = addDays(inicio, i);
      const fromShort = k < SHORT_WEEKS ? short.get(fecha) : undefined;
      const day = fromShort ?? projection.get(fecha);
      if (day?.tmin == null || day.tmax == null || day.pmm == null) continue;
      dias.push({
        fecha,
        tmin: Math.round(day.tmin),
        tmax: Math.round(day.tmax),
        pmm: Math.round(day.pmm * 10) / 10,
        ...(day.granizo ? { granizo: true } : {}),
        proyeccion: !fromShort,
      });
    }
    const pmm = Math.round(dias.reduce((sum, d) => sum + d.pmm, 0) * 10) / 10;
    const helada = dias.find((d) => d.tmin < 0)?.fecha;
    const granizo = dias.find((d) => d.granizo)?.fecha;
    return {
      inicio,
      fin: addDays(inicio, 6),
      dias,
      lejos: k >= SHORT_WEEKS || dias.some((d) => d.proyeccion),
      tile: tileOf(dias, pmm),
      pmm,
      ...(helada ? { helada } : {}),
      ...(granizo ? { granizo } : {}),
    };
  });
}

type RawMonth = { mes: number; pmm_total?: number; p_helada?: number };

function monthTile(m: RawMonth): MonthTile {
  if ((m.p_helada ?? 0) >= FROSTY_MONTH) return "helada";
  const pmm = m.pmm_total ?? 0;
  if (pmm >= 100) return "lluvia_fuerte";
  if (pmm >= 40) return "lluvia";
  return pmm >= 15 ? "poca_lluvia" : "seco";
}

export function monthsAhead(
  climatologia: unknown,
  today: string,
  count = 5,
): Month[] {
  const meses = (climatologia as { meses?: RawMonth[] } | null)?.meses ?? [];
  const current = Number(today.slice(5, 7));
  const result: Month[] = [];
  for (let k = 1; k <= count; k++) {
    const mes = ((current - 1 + k) % 12) + 1;
    const m = meses.find((x) => x.mes === mes);
    if (m)
      result.push({
        mes,
        tile: monthTile(m),
        helada: (m.p_helada ?? 0) >= RISK_SHARE,
      });
  }
  return result;
}

export function sourceLine(fuente: unknown) {
  const codes = Array.isArray(fuente) ? (fuente as string[]) : [];
  return codes.map((code) => SOURCES[code] ?? code).join(" · ");
}
