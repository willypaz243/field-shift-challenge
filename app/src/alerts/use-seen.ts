import { useCallback, useEffect, useState } from "react";
import { useOffline } from "../offline/provider";
import { SeenAlerts } from "./alerts";

const listeners = new Set<() => void>();

// The bell in the header and the Avisos screen share what was already seen.
export function useSeenAlerts() {
  const { client } = useOffline();
  const [seen, setSeen] = useState<Set<string>>(new Set());
  useEffect(() => {
    const store = new SeenAlerts(client.store.db);
    const load = () => void store.read().then(setSeen);
    load();
    listeners.add(load);
    return () => {
      listeners.delete(load);
    };
  }, [client]);
  const markSeen = useCallback(
    async (ids: string[]) => {
      await new SeenAlerts(client.store.db).add(ids);
      listeners.forEach((listener) => listener());
    },
    [client],
  );
  return { seen, markSeen };
}
