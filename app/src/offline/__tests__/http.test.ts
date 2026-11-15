import { HttpTransport } from "../http";

test("uses the contract query and treats an unchanged package as no update", async () => {
  const request = jest.fn().mockResolvedValue({ status: 304 });
  const transport = new HttpTransport("https://example.test/v1", request);
  expect(await transport.pull("D9_itocta", 42)).toBeNull();
  expect(request).toHaveBeenCalledWith(
    "https://example.test/v1/sync?zone_id=D9_itocta&desde_version=42",
  );
});

test("posts reports as multipart with the persistent idempotency key", async () => {
  const request = jest.fn().mockResolvedValue({ status: 409, ok: false });
  const transport = new HttpTransport("https://example.test/v1", request);
  await transport.send({
    id: "local-uuid",
    kind: "reports",
    payload: { tipo: "helada", lat: -17.461 },
    attempts: 1,
    next_attempt: 0,
  });
  const options = request.mock.calls[0][1];
  expect(options.headers["Idempotency-Key"]).toBe("local-uuid");
  expect(options.body.get("tipo")).toBe("helada");
  expect(options.headers["Content-Type"]).toBeUndefined();
});

test("keeps non-successful feedback available for retry", async () => {
  const request = jest.fn().mockResolvedValue({ status: 503, ok: false });
  await expect(
    new HttpTransport("https://example.test", request).send({
      id: "feedback-id",
      kind: "feedback",
      payload: {},
      attempts: 0,
      next_attempt: 0,
    }),
  ).rejects.toThrow("503");
});

test("treats a repeated feedback or plan key (409) as already delivered", async () => {
  const request = jest.fn().mockResolvedValue({ status: 409, ok: false });
  const transport = new HttpTransport("https://example.test", request);
  for (const kind of ["feedback", "plans"] as const) {
    await expect(
      transport.send({
        id: `${kind}-id`,
        kind,
        payload: {},
        attempts: 1,
        next_attempt: 0,
      }),
    ).resolves.toBeUndefined();
  }
});

test("the default request calls fetch unbound, as browsers require", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = function (this: unknown) {
    if (this !== undefined && this !== globalThis)
      throw new TypeError("Illegal invocation");
    return Promise.resolve({ status: 304 } as Response);
  } as typeof fetch;
  try {
    await expect(
      new HttpTransport("https://example.test").pull("D9_itocta", 1),
    ).resolves.toBeNull();
  } finally {
    globalThis.fetch = original;
  }
});
