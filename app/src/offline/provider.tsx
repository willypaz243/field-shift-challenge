import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { SyncClient } from "./client";
import { openOfflineClient } from "./open";
import { transportFromEnv } from "./transport";
import { useLocalData } from "./use-local-data";

const ZONE = process.env.EXPO_PUBLIC_ZONE_ID ?? "D9_itocta";
const ClientContext = createContext<SyncClient | null>(null);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [client, setClient] = useState<SyncClient | null>(null);
  useEffect(() => {
    // Expo only inlines EXPO_PUBLIC_* when read as a direct property.
    const env = { EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL };
    void openOfflineClient(transportFromEnv(env)).then(setClient);
  }, []);
  return (
    <ClientContext.Provider value={client}>{children}</ClientContext.Provider>
  );
}

export function useOffline() {
  const client = useContext(ClientContext);
  if (!client)
    throw new Error("useOffline must be used inside a ready OfflineProvider");
  const { data, error } = useLocalData(client, ZONE);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  useEffect(() => {
    void client.store
      .state(ZONE)
      .then((s) => setUpdatedAt(s?.updated_at ?? null));
  }, [client, data]);
  return { client, zone: ZONE, data, error, updatedAt };
}

export function useOfflineReady() {
  return useContext(ClientContext) !== null;
}
