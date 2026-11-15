export type Point = { lat: number; lon: number };

export type Zone = Point & { id: string; nombre: string; distrito?: number };

export const waterSources = [
  "angostura",
  "misicuni",
  "pozo",
  "rio",
  "lluvia",
  "no_se",
] as const;
export type WaterSource = (typeof waterSources)[number];

export const priorities = ["agua", "tierra", "forraje", "vender"] as const;
export type Priority = (typeof priorities)[number];

export type Language = "es" | "qu";

export type Farm = {
  zone_id?: string;
  parcela?: Point;
  agua?: WaterSource;
  prioridad?: Priority;
  idioma?: Language;
};
