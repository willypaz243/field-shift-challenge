import type { SQLiteDatabase } from "expo-sqlite";
import type { Submission, Transport } from "./types";

export class Outbox {
  private pending?: Promise<void>;
  constructor(
    private db: SQLiteDatabase,
    private transport: Transport,
  ) {}

  async enqueue(item: Omit<Submission, "attempts" | "next_attempt">) {
    await this.db.runAsync(
      "INSERT INTO outbox (id, kind, payload) VALUES (?, ?, ?)",
      item.id,
      item.kind,
      JSON.stringify(item.payload),
    );
  }

  flush(now = Date.now()) {
    if (this.pending) return this.pending;
    this.pending = this.drain(now).finally(() => {
      this.pending = undefined;
    });
    return this.pending;
  }

  private async drain(now: number) {
    const rows = await this.db.getAllAsync<
      Omit<Submission, "payload"> & { payload: string }
    >("SELECT * FROM outbox WHERE next_attempt <= ? ORDER BY rowid", now);
    for (const row of rows) {
      try {
        await this.transport.send({ ...row, payload: JSON.parse(row.payload) });
        await this.db.runAsync("DELETE FROM outbox WHERE id = ?", row.id);
      } catch {
        const delay = Math.min(3600000, 1000 * 2 ** Math.min(row.attempts, 12));
        await this.db.runAsync(
          "UPDATE outbox SET attempts = attempts + 1, next_attempt = ? WHERE id = ?",
          now + delay,
          row.id,
        );
      }
    }
  }
}
