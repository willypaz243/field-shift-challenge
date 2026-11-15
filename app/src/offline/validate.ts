import { sections, type SyncPackage } from "./types";

export function validatePackage(
  packet: SyncPackage,
  zone: string,
  initial: boolean,
) {
  if (
    !packet ||
    !Number.isSafeInteger(packet.sync_version) ||
    packet.sync_version < 0 ||
    typeof packet.hash !== "string" ||
    !packet.hash
  )
    throw new Error("Invalid sync metadata");
  for (const name of sections) {
    const value = packet[name];
    if (value === undefined) {
      if (initial) throw new Error("Incomplete initial sync");
      continue;
    }
    const isList = name === "alertas" || name === "historial_zona";
    if (
      isList
        ? !Array.isArray(value)
        : !value || typeof value !== "object" || Array.isArray(value)
    )
      throw new Error(`Invalid sync section: ${name}`);
  }
  const packetZone = packet.zone as { id?: string } | undefined;
  if (packetZone && packetZone.id !== zone)
    throw new Error("Unexpected sync zone");
}
