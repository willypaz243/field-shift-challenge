import { DatabaseSync } from "node:sqlite";
import type { SQLiteDatabase } from "expo-sqlite";

export function testDatabase(path = ":memory:") {
  const connection = new DatabaseSync(path);
  const adapter = {
    async execAsync(sql: string) {
      connection.exec(sql);
    },
    async runAsync(sql: string, ...params: (string | number | null)[]) {
      return connection.prepare(sql).run(...params);
    },
    async getFirstAsync(sql: string, ...params: (string | number)[]) {
      return connection.prepare(sql).get(...params) ?? null;
    },
    async getAllAsync(sql: string, ...params: (string | number)[]) {
      return connection.prepare(sql).all(...params);
    },
    async withTransactionAsync(task: () => Promise<void>) {
      connection.exec("BEGIN");
      try {
        await task();
        connection.exec("COMMIT");
      } catch (error) {
        connection.exec("ROLLBACK");
        throw error;
      }
    },
    async withExclusiveTransactionAsync(task: (db: unknown) => Promise<void>) {
      connection.exec("BEGIN");
      try {
        await task(adapter);
        connection.exec("COMMIT");
      } catch (error) {
        connection.exec("ROLLBACK");
        throw error;
      }
    },
  };
  return {
    db: adapter as unknown as SQLiteDatabase,
    close: () => connection.close(),
  };
}
