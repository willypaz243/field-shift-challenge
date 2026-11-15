import snapshot from "./zones.json";
import type { Zone } from "./types";

// Bundled so the first use works without signal; zones change only with a new release.
export const zones: Zone[] = snapshot.zones;

export function shortName(nombre: string) {
  return nombre.split(" (")[0];
}

export function zoneLabel(zone: Zone) {
  const name = shortName(zone.nombre);
  return zone.distrito ? `${name} · Distrito ${zone.distrito}` : name;
}
