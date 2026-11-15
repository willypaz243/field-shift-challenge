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
