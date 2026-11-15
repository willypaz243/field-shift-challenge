import { reportForm } from "./report-form";
import type { Submission, SyncPackage, Transport } from "./types";

export class HttpTransport implements Transport {
  constructor(
    private baseUrl: string,
    // Browsers reject fetch called as a method of another object ("Illegal
    // invocation"), so the default wraps it instead of storing it.
    private request: typeof fetch = (input, init) => fetch(input, init),
  ) {}

  async pull(zone: string, version?: number): Promise<SyncPackage | null> {
    const query = new URLSearchParams({ zone_id: zone });
    if (version !== undefined) query.set("desde_version", String(version));
    const response = await this.request(`${this.baseUrl}/sync?${query}`);
    if (response.status === 304 || response.status === 204) return null;
    if (!response.ok) throw new Error(`Sync failed: ${response.status}`);
    return response.json();
  }

  async send(item: Submission) {
    const headers: Record<string, string> = { "Idempotency-Key": item.id };
    let body: FormData | string;
    if (item.kind === "reports") {
      body = reportForm(item.payload);
    } else {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(item.payload);
    }
    const response = await this.request(`${this.baseUrl}/${item.kind}`, {
      method: "POST",
      headers,
      body,
    });
    if (response.status === 409) return;
    if (!response.ok) throw new Error(`Submission failed: ${response.status}`);
  }
}
