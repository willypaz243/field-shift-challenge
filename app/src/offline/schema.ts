import type { SQLiteDatabase } from "expo-sqlite";

export async function initialize(db: SQLiteDatabase) {
  await db.execAsync(`
    PRAGMA journal_mode = WAL;
    CREATE TABLE IF NOT EXISTS sync_state (
      zone_id TEXT PRIMARY KEY, version INTEGER NOT NULL, hash TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sync_sections (
      zone_id TEXT NOT NULL, name TEXT NOT NULL, value TEXT NOT NULL,
      PRIMARY KEY (zone_id, name)
    );
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0, next_attempt INTEGER NOT NULL DEFAULT 0
    );
  `);
}
