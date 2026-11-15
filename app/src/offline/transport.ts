import { HttpTransport } from "./http";
import { MockTransport } from "./mock";
import type { Transport } from "./types";

type Env = { EXPO_PUBLIC_API_URL?: string };

export function transportFromEnv(env: Env): Transport {
  const url = env.EXPO_PUBLIC_API_URL?.trim();
  return url ? new HttpTransport(url.replace(/\/$/, "")) : new MockTransport();
}
