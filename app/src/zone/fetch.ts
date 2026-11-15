import type { SQLiteDatabase } from "expo-sqlite";

// The map changes with farmers' reports, not with data loads, so it is not part
// of /sync: it is fetched when the screen opens and the last copy is kept.
export class MapCache {
  constructor(private db: SQLiteDatabase) {}

  async read(zone: string): Promise<unknown> {
    const row = await this.db.getFirstAsync<{ value: string }>(
      "SELECT value FROM cache WHERE key = ?",
      `mapa:${zone}`,
    );
    return row ? JSON.parse(row.value) : null;
  }

  async save(zone: string, map: unknown) {
    await this.db.runAsync(
      "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
      `mapa:${zone}`,
      JSON.stringify(map),
    );
  }
}

export async function fetchZoneMap(
  baseUrl: string,
  zone: string,
  request: typeof fetch = fetch,
): Promise<unknown> {
  try {
    const response = await request(`${baseUrl}/zones/${zone}/map`);
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

// Measured weeks also change outside data loads (IMERG Late arrives daily), so
// they follow the same pattern as the map: fetched on open, last copy kept.
export class HistoryCache {
  constructor(private db: SQLiteDatabase) {}

  async read(zone: string): Promise<unknown> {
    const row = await this.db.getFirstAsync<{ value: string }>(
      "SELECT value FROM cache WHERE key = ?",
      `historia:${zone}`,
    );
    return row ? JSON.parse(row.value) : null;
  }

  async save(zone: string, history: unknown) {
    await this.db.runAsync(
      "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
      `historia:${zone}`,
      JSON.stringify(history),
    );
  }
}

export async function fetchHistory(
  baseUrl: string,
  zone: string,
  desde: string,
  hasta: string,
  request: typeof fetch = fetch,
): Promise<unknown> {
  try {
    const response = await request(
      `${baseUrl}/zones/${zone}/history?desde=${desde}&hasta=${hasta}`,
    );
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}
