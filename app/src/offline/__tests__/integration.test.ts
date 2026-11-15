import apiSync from "../fixtures/api_sync_D9.json";
import { testDatabase } from "./database";
import { initialize } from "../schema";
import { LocalStore } from "../store";
import { SyncClient } from "../client";
import { HttpTransport } from "../http";
import { MockTransport } from "../mock";
import { transportFromEnv } from "../transport";
import { sections } from "../types";

const zone = "D9_itocta";
let fixture: ReturnType<typeof testDatabase>;
beforeEach(async () => {
  fixture = testDatabase();
  await initialize(fixture.db);
});
afterEach(() => fixture.close());

test("uses the real API when EXPO_PUBLIC_API_URL is set and the mock otherwise", () => {
  expect(
    transportFromEnv({ EXPO_PUBLIC_API_URL: "http://192.168.0.10:8000" }),
  ).toBeInstanceOf(HttpTransport);
  expect(transportFromEnv({})).toBeInstanceOf(MockTransport);
});

test("stores the nine sections of a real /sync response and keeps them on 304", async () => {
  const request = jest
    .fn()
    .mockResolvedValueOnce({ status: 200, ok: true, json: async () => apiSync })
    .mockResolvedValueOnce({ status: 304, ok: false });
  const client = new SyncClient(
    new LocalStore(fixture.db),
    new HttpTransport("http://api.test", request),
  );

  await client.refresh(zone, true);
  await client.refresh(zone, true);

  const stored = await client.store.read(zone);
  for (const name of sections) expect(stored?.[name]).toEqual(apiSync[name]);
  expect(request.mock.calls[1][0]).toBe(
    `http://api.test/sync?zone_id=${zone}&desde_version=${apiSync.sync_version}`,
  );
});

test("delivers queued feedback with its idempotency key and clears it on 201 or 409", async () => {
  for (const status of [201, 409]) {
    const request = jest.fn().mockResolvedValue({ status, ok: status === 201 });
    const client = new SyncClient(
      new LocalStore(fixture.db),
      new HttpTransport("http://api.test", request),
    );
    const id = `feedback-${status}`;
    await client.outbox.enqueue({
      id,
      kind: "feedback",
      payload: {
        zone_id: zone,
        crop_id: "haba",
        cosecha: "2026-11-16",
        resultado: "buena",
      },
    });

    await client.outbox.flush();

    const [url, options] = request.mock.calls[0];
    expect(url).toBe("http://api.test/feedback");
    expect(options.headers["Idempotency-Key"]).toBe(id);
    expect(JSON.parse(options.body).resultado).toBe("buena");
    expect(await fixture.db.getAllAsync("SELECT id FROM outbox")).toEqual([]);
  }
});
