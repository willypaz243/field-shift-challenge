import type { SQLiteDatabase } from "expo-sqlite";
import type { Farm } from "./types";

export class FarmStore {
  constructor(private db: SQLiteDatabase) {}

  async read(): Promise<Farm | null> {
    const rows = await this.db.getAllAsync<{ key: string; value: string }>(
      "SELECT key, value FROM farm",
    );
    if (rows.length === 0) return null;
    return Object.fromEntries(
      rows.map((row) => [row.key, JSON.parse(row.value)]),
    ) as Farm;
  }

  async save(answers: Farm) {
    const { lat, lon } = answers.parcela ?? { lat: 0, lon: 0 };
    if (!Number.isFinite(lat) || !Number.isFinite(lon))
      throw new Error("Invalid plot coordinates");
    for (const [key, value] of Object.entries(answers))
      await this.db.runAsync(
        "INSERT OR REPLACE INTO farm (key, value) VALUES (?, ?)",
        key,
        JSON.stringify(value),
      );
  }
}
