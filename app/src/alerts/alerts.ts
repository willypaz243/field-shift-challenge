import type { SQLiteDatabase } from "expo-sqlite";

export type Alert = {
  id: string;
  tipo: string;
  fecha_evento?: string;
  momento?: string;
  valor?: { tmin?: number; nivel_pct?: number };
  confianza?: string;
  volver_a_avisar?: string;
};
export type AlertRow = Alert & { nuevo: boolean };

function list(alertas: unknown): Alert[] {
  return (Array.isArray(alertas) ? alertas : []).filter(
    (a): a is Alert => typeof a?.id === "string" && typeof a?.tipo === "string",
  );
}

export function alertRows(alertas: unknown, seen: Set<string>): AlertRow[] {
  const rows = list(alertas).map((a) => ({ ...a, nuevo: !seen.has(a.id) }));
  const dated = rows
    .filter((a) => a.fecha_evento)
    .sort((a, b) => a.fecha_evento!.localeCompare(b.fecha_evento!));
  return [...dated, ...rows.filter((a) => !a.fecha_evento)];
}

export function newCount(alertas: unknown, seen: Set<string>) {
  return list(alertas).filter((a) => !seen.has(a.id)).length;
}

const SEEN_KEY = "avisos_vistos";

export class SeenAlerts {
  constructor(private db: SQLiteDatabase) {}

  async read() {
    const row = await this.db.getFirstAsync<{ value: string }>(
      "SELECT value FROM cache WHERE key = ?",
      SEEN_KEY,
    );
    return new Set<string>(row ? JSON.parse(row.value) : []);
  }

  async add(ids: string[]) {
    const seen = await this.read();
    ids.forEach((id) => seen.add(id));
    await this.db.runAsync(
      "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
      SEEN_KEY,
      JSON.stringify([...seen]),
    );
  }
}
