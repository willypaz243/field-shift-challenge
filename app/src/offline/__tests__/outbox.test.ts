import { testDatabase } from "./database";
import { initialize } from "../schema";
import { Outbox } from "../outbox";

const fixture = testDatabase();
beforeAll(() => initialize(fixture.db));
afterAll(() => fixture.close());

test.each(["reports", "feedback", "plans"] as const)(
  "retries %s with a stable id after reopening the queue",
  async (kind) => {
    const send = jest
      .fn()
      .mockRejectedValueOnce(new Error("Offline"))
      .mockResolvedValue(undefined);
    const transport = { pull: jest.fn(), send };
    const queue = new Outbox(fixture.db, transport);
    await queue.enqueue({ id: kind, kind, payload: { zone_id: "D9_itocta" } });
    await queue.flush(0);
    const reopened = new Outbox(fixture.db, transport);
    await reopened.flush(999);
    expect(send).toHaveBeenCalledTimes(1);
    await reopened.flush(1000);
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.mock.calls[1][0].id).toBe(kind);
    expect(await fixture.db.getAllAsync("SELECT * FROM outbox")).toEqual([]);
  },
);

test("shares concurrent flushes without sending the same item twice", async () => {
  const send = jest.fn().mockResolvedValue(undefined);
  const queue = new Outbox(fixture.db, { pull: jest.fn(), send });
  await queue.enqueue({ id: "concurrent", kind: "plans", payload: {} });
  await Promise.all([queue.flush(), queue.flush()]);
  expect(send).toHaveBeenCalledTimes(1);
});
