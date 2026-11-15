import {
  createContext,
  useCallback,
  useMemo,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { SyncClient } from "./client";
import { openOfflineClient } from "./open";
import { transportFromEnv } from "./transport";
import { useLocalData } from "./use-local-data";
import { FarmStore } from "../farm/store";
import type { Farm } from "../farm/types";
import { setupI18n } from "../i18n";
import { withParcel } from "./with-parcel";

const DEFAULT_ZONE = process.env.EXPO_PUBLIC_ZONE_ID ?? "D9_itocta";

type Offline = {
  client: SyncClient;
  farm: Farm | null;
  saveFarm: (answers: Farm) => Promise<void>;
};
const ClientContext = createContext<Offline | null>(null);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{
    client: SyncClient;
    store: FarmStore;
    farm: Farm | null;
  } | null>(null);
  useEffect(() => {
    // Expo only inlines EXPO_PUBLIC_* when read as a direct property.
    const env = { EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL };
    void openOfflineClient(transportFromEnv(env)).then(async (client) => {
      const store = new FarmStore(client.store.db);
      const farm = await store.read();
      setupI18n(farm?.idioma);
      setState({ client, store, farm });
    });
  }, []);
  const saveFarm = useCallback(
    async (answers: Farm) => {
      if (!state) return;
      await state.store.save(answers);
      if (answers.idioma) setupI18n(answers.idioma);
      setState((s) => s && { ...s, farm: { ...s.farm, ...answers } });
    },
    [state],
  );
  const value = state && { client: state.client, farm: state.farm, saveFarm };
  return (
    <ClientContext.Provider value={value}>{children}</ClientContext.Provider>
  );
}

function useReadyContext() {
  const context = useContext(ClientContext);
  if (!context)
    throw new Error("useOffline must be used inside a ready OfflineProvider");
  return context;
}

export function useOffline() {
  const { client, farm } = useReadyContext();
  const zone = farm?.zone_id ?? DEFAULT_ZONE;
  const { data: zoneData, error } = useLocalData(client, zone);
  const data = useMemo(
    () => withParcel(zoneData, zone, farm?.parcela),
    [zoneData, zone, farm?.parcela],
  );
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  useEffect(() => {
    void client.store
      .state(zone)
      .then((s) => setUpdatedAt(s?.updated_at ?? null));
  }, [client, zone, data]);
  return { client, zone, data, error, updatedAt };
}

export function useFarm() {
  const { farm, saveFarm } = useReadyContext();
  return { farm, saveFarm };
}

export function useOfflineReady() {
  return useContext(ClientContext) !== null;
}
