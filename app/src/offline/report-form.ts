import type { Submission } from "./types";

export function reportForm(payload: Submission["payload"]) {
  const body = new FormData();
  for (const [key, value] of Object.entries(payload)) {
    if (value === null) continue;
    if (key === "foto" || key === "audio") {
      if (
        typeof value !== "object" ||
        Array.isArray(value) ||
        typeof value.uri !== "string"
      )
        throw new Error("Invalid report attachment");
      body.append(key, value as unknown as Blob);
    } else if ((key === "lat" || key === "lon") && typeof value === "number") {
      body.append(key, value.toFixed(3));
    } else {
      body.append(key, String(value));
    }
  }
  return body;
}
