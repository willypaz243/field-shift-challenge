import { useEffect, useState } from "react";
import { AppState } from "react-native";
import type { SyncClient } from "./client";
import type { Snapshot } from "./types";

export function useLocalData(client: SyncClient, zone: string) {
  const [data, setData] = useState<Snapshot | null>(null);
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    let active = true;
    setData(null);
    const read = async () => {
      const cached = await client.store.read(zone);
      if (active) setData(cached);
    };
    const refresh = async () => {
      try {
        await read();
        await client.refresh(zone, true);
        if (active) setError(undefined);
      } catch (failure) {
        if (active) setError(failure);
      } finally {
        if (active) await read().catch((failure: unknown) => setError(failure));
      }
    };
    void refresh();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") void refresh();
    });
    return () => {
      active = false;
      subscription.remove();
    };
  }, [client, zone]);
  return { data, error };
}
