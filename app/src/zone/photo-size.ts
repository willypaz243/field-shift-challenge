// API-CONTRACT §7.1: report photos are JPEG of at most 300 KB.
export const MAX_PHOTO_BYTES = 300_000;
const STEPS: [number, number][] = [
  [1280, 0.7],
  [1024, 0.6],
  [800, 0.55],
  [640, 0.5],
];

type Rendered = { uri: string; size: number };

// A photo the server would reject would stay in the outbox retrying forever.
export async function shrinkWith(
  render: (width: number, compress: number) => Promise<Rendered>,
): Promise<Rendered | null> {
  for (const [width, compress] of STEPS) {
    const out = await render(width, compress);
    if (out.size > 0 && out.size <= MAX_PHOTO_BYTES) return out;
  }
  return null;
}

export function orphanPhotos(files: string[], queued: unknown[]) {
  const kept = new Set(
    queued
      .map((p) => (p as { foto?: { uri?: string } } | null)?.foto?.uri)
      .filter(Boolean),
  );
  return files.filter((uri) => !kept.has(uri));
}
