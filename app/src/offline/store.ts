import { validatePackage } from "./validate";
import type { SQLiteDatabase } from "expo-sqlite";
import {
  sections,
  type Section,
  type Snapshot,
  type SyncPackage,
} from "./types";

export class LocalStore {
  // expo-sqlite has no exclusive transactions on web (a single worker
  // connection serialises the queries anyway), so the web build uses a plain one.
  constructor(
    readonly db: SQLiteDatabase,
    private exclusive = true,
  ) {}

  private transaction(task: (tx: SQLiteDatabase) => Promise<void>) {
    if (this.exclusive)
      return this.db.withExclusiveTransactionAsync((tx) =>
        task(tx as unknown as SQLiteDatabase),
      );
    return this.db.withTransactionAsync(() => task(this.db));
  }

  state(zone: string) {
    return this.db.getFirstAsync<{
      version: number;
      hash: string;
      updated_at: string;
    }>(
      "SELECT version, hash, updated_at FROM sync_state WHERE zone_id = ?",
      zone,
    );
  }

  async read(zone: string): Promise<Snapshot | null> {
    const rows = await this.db.getAllAsync<{ name: Section; value: string }>(
      "SELECT name, value FROM sync_sections WHERE zone_id = ?",
      zone,
    );
    if (!sections.every((name) => rows.some((row) => row.name === name)))
      return null;
    return Object.fromEntries(
      rows.map((row) => [row.name, JSON.parse(row.value)]),
    ) as Snapshot;
  }

  async apply(zone: string, packet: SyncPackage) {
    await this.transaction(async (tx) => {
      const current = await tx.getFirstAsync<{ version: number }>(
        "SELECT version FROM sync_state WHERE zone_id = ?",
        zone,
      );
      validatePackage(packet, zone, !current);
      if (current && packet.sync_version <= current.version) return;
      for (const name of sections) {
        if (packet[name] !== undefined)
          await tx.runAsync(
            "INSERT OR REPLACE INTO sync_sections (zone_id, name, value) VALUES (?, ?, ?)",
            zone,
            name,
            JSON.stringify(packet[name]),
          );
      }
      await tx.runAsync(
        "INSERT OR REPLACE INTO sync_state (zone_id, version, hash, updated_at) VALUES (?, ?, ?, ?)",
        zone,
        packet.sync_version,
        packet.hash,
        new Date().toISOString(),
      );
    });
  }
}
