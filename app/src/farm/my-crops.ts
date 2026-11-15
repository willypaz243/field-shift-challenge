import type { SQLiteDatabase } from "expo-sqlite";

export type MyCrop = {
  id: string;
  crop_id: string;
  siembra: string;
  cosecha: string;
  planificado: boolean;
};

function newId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

// The farmer's crops never leave the phone (API-CONTRACT §1, privacy).
export class MyCrops {
  constructor(private db: SQLiteDatabase) {}

  async list(): Promise<MyCrop[]> {
    const rows = await this.db.getAllAsync<
      Omit<MyCrop, "planificado"> & { planificado: number }
    >(
      "SELECT id, crop_id, siembra, cosecha, planificado FROM my_crops ORDER BY siembra",
    );
    return rows.map((r) => ({ ...r, planificado: r.planificado === 1 }));
  }

  async add(
    crop: Omit<MyCrop, "id" | "planificado"> & { planificado?: boolean },
  ) {
    const id = newId();
    await this.db.runAsync(
      "INSERT INTO my_crops (id, crop_id, siembra, cosecha, planificado) VALUES (?, ?, ?, ?, ?)",
      id,
      crop.crop_id,
      crop.siembra,
      crop.cosecha,
      crop.planificado ? 1 : 0,
    );
    return id;
  }

  async remove(id: string) {
    await this.db.runAsync("DELETE FROM my_crops WHERE id = ?", id);
  }
}
