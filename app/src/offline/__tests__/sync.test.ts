import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { testDatabase } from "./database";
import { initialize } from "../schema";
import { LocalStore } from "../store";
import { SyncClient } from "../client";
import { contractPackage, MockTransport } from "../mock";

const zone = "D9_itocta";
let fixture: ReturnType<typeof testDatabase>;
let store: LocalStore;
beforeEach(async () => {
  fixture = testDatabase();
  await initialize(fixture.db);
  store = new LocalStore(fixture.db);
});
afterEach(() => fixture.close());

test("persists the first sync across a restart without network", async () => {
  const directory = mkdtempSync(join(tmpdir(), "choclito-"));
  const path = join(directory, "offline.db");
  const first = testDatabase(path);
  await initialize(first.db);
  await new SyncClient(new LocalStore(first.db), new MockTransport()).refresh(
    zone,
    true,
  );
  first.close();
  const reopened = testDatabase(path);
  try {
    const transport = { pull: jest.fn(), send: jest.fn() };
    const client = new SyncClient(new LocalStore(reopened.db), transport);
    await client.refresh(zone, false);
    expect((await client.store.read(zone))?.zone).toEqual(contractPackage.zone);
    expect(transport.pull).not.toHaveBeenCalled();
  } finally {
    reopened.close();
    rmSync(directory, { recursive: true });
  }
});

test("requests deltas and preserves omitted sections while replacing empty arrays", async () => {
  await store.apply(zone, contractPackage);
  const pull = jest
    .fn()
    .mockResolvedValue({ sync_version: 2, hash: "delta", alertas: [] });
  await new SyncClient(store, { pull, send: jest.fn() }).refresh(zone, true);
  expect(pull).toHaveBeenCalledWith(zone, 1);
  expect((await store.read(zone))?.crops).toEqual(contractPackage.crops);
  expect((await store.read(zone))?.alertas).toEqual([]);
});

test("rejects partial first sync and mismatched zones without advancing metadata", async () => {
  await expect(
    store.apply(zone, { sync_version: 1, hash: "partial" }),
  ).rejects.toThrow();
  expect(await store.state(zone)).toBeNull();
  await expect(
    store.apply(zone, { ...contractPackage, zone: { id: "other" } }),
  ).rejects.toThrow();
  expect(await store.read(zone)).toBeNull();
});

test("rolls back a failed write and ignores stale versions", async () => {
  await store.apply(zone, contractPackage);
  await fixture.db.execAsync(
    "CREATE TRIGGER fail_sync BEFORE INSERT ON sync_state BEGIN SELECT RAISE(ABORT, 'write failed'); END;",
  );
  await expect(
    store.apply(zone, { sync_version: 2, hash: "delta", alertas: [] }),
  ).rejects.toThrow();
  expect((await store.read(zone))?.alertas).toEqual(contractPackage.alertas);
  await store.apply(zone, { sync_version: 0, hash: "old", alertas: [] });
  expect((await store.state(zone))?.version).toBe(1);
});

test("rejects malformed sections without replacing the cached package", async () => {
  await store.apply(zone, contractPackage);
  await expect(
    store.apply(zone, { sync_version: 2, hash: "invalid", alertas: {} }),
  ).rejects.toThrow("Invalid sync section");
  expect((await store.state(zone))?.version).toBe(1);
});

test("the web build applies a package without exclusive transactions", async () => {
  const web = new LocalStore(fixture.db, false);
  await web.apply(zone, contractPackage);
  expect((await web.read(zone))?.zone).toEqual(contractPackage.zone);
  await expect(
    web.apply(zone, { ...contractPackage, zone: { id: "D3_molle" } }),
  ).rejects.toThrow();
});
