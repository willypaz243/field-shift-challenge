import { useCallback, useEffect, useState } from "react";
import { MyCrops, type MyCrop } from "../farm/my-crops";
import { useOffline } from "../offline/provider";
import { Harvests, type HarvestState } from "./mycrops";

const listeners = new Set<() => void>();

export function notifyMyCrops() {
  listeners.forEach((listener) => listener());
}

// Hoy, Calendario, Avisos and the crop page share the farmer's crops.
export function useMyCrops() {
  const { client } = useOffline();
  const [crops, setCrops] = useState<MyCrop[]>([]);
  const [states, setStates] = useState<Map<string, HarvestState>>(new Map());
  const load = useCallback(() => {
    void new MyCrops(client.store.db).list().then(setCrops);
    void new Harvests(client.store.db).all().then(setStates);
  }, [client]);
  useEffect(() => {
    load();
    listeners.add(load);
    return () => {
      listeners.delete(load);
    };
  }, [load]);
  return { crops, states };
}

export function cropName(data: unknown, cropId: string) {
  const crops = (
    data as { crops?: { crops?: { id: string; nombre: string }[] } } | null
  )?.crops?.crops;
  return crops?.find((c) => c.id === cropId)?.nombre.split(" (")[0] ?? cropId;
}
