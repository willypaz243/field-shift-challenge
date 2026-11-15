import { Platform } from "react-native";
import { openDatabaseAsync } from "expo-sqlite";
import { initialize } from "./schema";
import { LocalStore } from "./store";
import { SyncClient } from "./client";
import type { Transport } from "./types";

export async function openOfflineClient(transport: Transport) {
  const db = await openDatabaseAsync("choclito.db");
  await initialize(db);
  return new SyncClient(new LocalStore(db, Platform.OS !== "web"), transport);
}
