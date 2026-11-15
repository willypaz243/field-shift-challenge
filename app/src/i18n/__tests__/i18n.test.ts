import { es } from "../es";
import { qu } from "../qu";

function keys(value: object, prefix = ""): string[] {
  return Object.entries(value).flatMap(([key, child]) =>
    typeof child === "object"
      ? keys(child, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  );
}

test("every Quechua text has a Spanish original", () => {
  const spanish = new Set(keys(es));
  expect(keys(qu).filter((key) => !spanish.has(key))).toEqual([]);
});

function values(value: object): unknown[] {
  return Object.values(value).flatMap((child) =>
    typeof child === "object" ? values(child) : [child],
  );
}

test("no text is empty", () => {
  for (const language of [es, qu])
    for (const text of values(language)) expect(text).not.toBe("");
});
