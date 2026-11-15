// Port of src/model/scoring.py (score_window / score_windows). The vectors in
// data/model/test_vectors.json are the portability contract; keep both in step.

export type Crop = {
  id: string;
  ciclo_dias: [number, number] | number[];
  temp: { tmean_opt: [number, number] | number[] };
  helada?: { tolerancia?: string };
  kc?: { inicial: number; medio: number; final: number };
  drought_tolerant?: string;
  erosion_sens?: string;
};
export type ZoneInput = { cerca_drenaje?: number | null };
export type Veredicto = "bueno" | "con_cuidado" | "malo";
export type Motivo =
  "temp_fuera_rango" | "deficit_agua" | "heladas" | "erosion_riesgo";
export type WindowScore = {
  score: number;
  veredicto: Veredicto;
  confianza: number;
  motivos: Motivo[];
  detalle: {
    temp: number;
    agua: number;
    helada: number;
    erosion: number;
    deficit_mm: number;
    frost_days: number;
  };
};
export type RankedWindow = WindowScore & { inicio: string; fin: string };

const FROST_SEV: Record<string, number> = { baja: 1.0, media: 0.5, alta: 0.2 };
const DROUGHT_MITIG: Record<string, number> = { no: 1.0, poco: 0.6, sí: 0.3 };
const EROSION_PEN: Record<string, number> = { alta: 0.5, media: 0.75 };
const WATER_ALLOW_PER_DAY = 2.0;
const MIN_GAP_DAYS = 14;
const FROST_OFFSET = 0.0;
const VERDICT_GOOD = 70.0;
const VERDICT_POOR = 40.0;
const BASE_CONFIDENCE = 0.7;

// Python's round(): exact halves go to the even neighbour; anything a hair
// above or below a half (as stored in binary) rounds normally.
export function pyRound(x: number, digits = 0) {
  const m = 10 ** digits;
  const v = x * m;
  const floor = Math.floor(v);
  const r =
    v - floor === 0.5 ? (floor % 2 === 0 ? floor : floor + 1) : Math.round(v);
  return r / m;
}

export function veredicto(
  score: number,
  bueno = VERDICT_GOOD,
  malo = VERDICT_POOR,
): Veredicto {
  if (score >= bueno) return "bueno";
  return score >= malo ? "con_cuidado" : "malo";
}

function confianza(L: number, horizon: number | undefined, pos: number) {
  if (horizon == null || horizon <= 0) return BASE_CONFIDENCE;
  const center = (pos + L / 2) / horizon;
  return Math.max(0.4, Math.min(0.9, 0.92 - 0.5 * center));
}

type Options = {
  horizon?: number;
  pos?: number;
  umbralBueno?: number;
  umbralMalo?: number;
};

export function scoreWindow(
  crop: Crop,
  zone: ZoneInput,
  tmean: number[],
  tmin: number[],
  pmm: number[],
  et0: number[],
  {
    horizon,
    pos = 0,
    umbralBueno = VERDICT_GOOD,
    umbralMalo = VERDICT_POOR,
  }: Options = {},
): WindowScore {
  const L = tmean.length;
  const [lo, hi] = crop.temp.tmean_opt;
  const temp = tmean.filter((x) => lo <= x && x <= hi).length / L;

  const frostDays = tmin.filter((x) => x + FROST_OFFSET < 0).length;
  const sev = FROST_SEV[crop.helada?.tolerancia ?? "baja"] ?? 1.0;
  const helada = 1.0 - (sev * frostDays) / L;

  const kc = crop.kc ?? { inicial: 1.0, medio: 1.0, final: 1.0 };
  const kcAvg = (kc.inicial + kc.medio + kc.final) / 3;
  let deficit = 0;
  for (let i = 0; i < Math.min(et0.length, pmm.length); i++)
    deficit += Math.max(0.0, et0[i] * kcAvg - pmm[i]);
  const mit = DROUGHT_MITIG[crop.drought_tolerant ?? "no"] ?? 1.0;
  const agua = 1.0 - Math.min(1.0, (deficit * mit) / (WATER_ALLOW_PER_DAY * L));

  let erosion = 1.0;
  if (
    zone.cerca_drenaje != null &&
    crop.erosion_sens &&
    crop.erosion_sens in EROSION_PEN
  )
    erosion = EROSION_PEN[crop.erosion_sens];

  const score = pyRound(
    100.0 * (0.45 * temp + 0.4 * agua + 0.15 * helada) * erosion,
    1,
  );

  const motivos: Motivo[] = [];
  if (pyRound(temp, 2) < 1.0) motivos.push("temp_fuera_rango");
  if (pyRound(deficit, 1) > 0) motivos.push("deficit_agua");
  if (frostDays > 0) motivos.push("heladas");
  if (erosion < 1.0) motivos.push("erosion_riesgo");

  return {
    score,
    veredicto: veredicto(score, umbralBueno, umbralMalo),
    confianza: pyRound(confianza(L, horizon, pos), 2),
    motivos,
    detalle: {
      temp: pyRound(temp, 2),
      agua: pyRound(agua, 2),
      helada: pyRound(helada, 2),
      erosion,
      deficit_mm: pyRound(deficit, 1),
      frost_days: frostDays,
    },
  };
}

function dayNumber(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return (y - 2026) * 365 + m * 31 + d;
}

export function scoreWindows(
  crop: Crop,
  zone: ZoneInput,
  dates: string[],
  tmean: number[],
  tmin: number[],
  pmm: number[],
  et0: number[],
  { horizon, umbralBueno, umbralMalo }: Omit<Options, "pos"> = {},
): RankedWindow[] {
  const L = pyRound((crop.ciclo_dias[0] + crop.ciclo_dias[1]) / 2);
  const H = dates.length;
  const total = horizon ?? H;
  const scored: RankedWindow[] = [];
  for (let s = 0; s <= H - L; s++) {
    const det = scoreWindow(
      crop,
      zone,
      tmean.slice(s, s + L),
      tmin.slice(s, s + L),
      pmm.slice(s, s + L),
      et0.slice(s, s + L),
      { horizon: total, pos: s, umbralBueno, umbralMalo },
    );
    scored.push({ inicio: dates[s], fin: dates[s + L - 1], ...det });
  }
  // Stable sort keeps the earliest window first among equal scores, like Python.
  scored.sort((a, b) => b.score - a.score);
  const top: RankedWindow[] = [];
  for (const w of scored) {
    if (
      top.every(
        (t) =>
          Math.abs(dayNumber(w.inicio) - dayNumber(t.inicio)) >= MIN_GAP_DAYS,
      )
    )
      top.push(w);
    if (top.length === 3) break;
  }
  return top;
}
