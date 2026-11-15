import { orphanPhotos, shrinkWith, MAX_PHOTO_BYTES } from "../photo-size";

test("the photo is shrunk step by step until it fits the 300 KB limit", async () => {
  const sizes = [900_000, 420_000, 250_000];
  const render = jest.fn(async () => ({ uri: "x", size: sizes.shift()! }));
  const result = await shrinkWith(render);
  expect(result?.size).toBe(250_000);
  expect(render).toHaveBeenCalledTimes(3);
  expect(render.mock.calls[0]).toEqual([1280, 0.7]);
});

test("a photo that never fits is dropped instead of failing on the server", async () => {
  const render = jest.fn(async () => ({ uri: "x", size: MAX_PHOTO_BYTES + 1 }));
  expect(await shrinkWith(render)).toBeNull();
});

test("photos of reports already sent are cleaned up", () => {
  const files = ["file:///docs/reports/a.jpg", "file:///docs/reports/b.jpg"];
  const queued = [
    { tipo: "helada", foto: { uri: "file:///docs/reports/b.jpg" } },
    { tipo: "plaga" },
  ];
  expect(orphanPhotos(files, queued)).toEqual(["file:///docs/reports/a.jpg"]);
});
