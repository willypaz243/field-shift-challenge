import crops from "../../../data/crops/crops.json";
import zone from "./fixtures/zone.json";
import forecast from "./fixtures/forecast.json";
import corto_plazo from "./fixtures/corto_plazo.json";
import climatologia from "./fixtures/climatologia.json";
import alertas from "./fixtures/alertas.json";
import rotaciones from "./fixtures/rotaciones.json";
import represa from "./fixtures/represa.json";
import historial_zona from "./fixtures/historial_zona.json";
import type { Submission, SyncPackage, Transport } from "./types";

export const contractPackage = {
  sync_version: 1,
  hash: "mock-contract-v1",
  zone,
  crops,
  forecast,
  corto_plazo,
  climatologia,
  alertas,
  rotaciones,
  represa,
  historial_zona,
} as unknown as SyncPackage;

export class MockTransport implements Transport {
  readonly submissions = new Map<string, Submission>();
  async pull(zoneId: string, version?: number) {
    if (zoneId !== zone.id) throw new Error("Unknown mock zone");
    return version === contractPackage.sync_version
      ? null
      : (JSON.parse(JSON.stringify(contractPackage)) as SyncPackage);
  }

  async send(item: Submission) {
    this.submissions.set(item.id, item);
  }
}
