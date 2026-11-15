export type Json =
  null | boolean | number | string | Json[] | { [key: string]: Json };
export const sections = [
  "zone",
  "crops",
  "forecast",
  "corto_plazo",
  "climatologia",
  "alertas",
  "rotaciones",
  "represa",
  "historial_zona",
] as const;
export type Section = (typeof sections)[number];
export type Snapshot = Record<Section, Json>;
export type SyncPackage = Partial<Snapshot> & {
  sync_version: number;
  hash: string;
};
export type Submission = {
  id: string;
  kind: "reports" | "feedback" | "plans";
  payload: Record<string, Json>;
  attempts: number;
  next_attempt: number;
};
export interface Transport {
  pull(zone: string, version?: number): Promise<SyncPackage | null>;
  send(item: Submission): Promise<void>;
}
