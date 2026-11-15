import {
  defaultGoal,
  planDates,
  planFor,
  rankFor,
  rotationsFor,
  season,
} from "../rotations";

const rotaciones = {
  rotaciones: [
    {
      id: "choclo-sin_cultivo",
      secuencia: ["choclo", null],
      actual_tipica: true,
      puntaje: { agua: 3, tierra: 1, forraje: 2, vender: 2 },
    },
    {
      id: "choclo-haba",
      secuencia: ["choclo", "haba"],
      puntaje: { agua: 1, tierra: 3, forraje: 1, vender: 3 },
    },
    {
      id: "choclo-avena",
      secuencia: ["choclo", "avena"],
      puntaje: { agua: 2, tierra: 3, forraje: 3, vender: 1 },
    },
    {
      id: "papa-haba",
      secuencia: ["papa", "haba"],
      puntaje: { agua: 1, tierra: 3, forraje: 1, vender: 3 },
    },
  ],
};

test("only the rotations that start with the crop, the current one first", () => {
  expect(rotationsFor(rotaciones, "choclo").map((r) => r.id)).toEqual([
    "choclo-sin_cultivo",
    "choclo-haba",
    "choclo-avena",
  ]);
  expect(rotationsFor(null, "choclo")).toEqual([]);
});

test("the best plan for the goal goes right after the current one", () => {
  const list = rotationsFor(rotaciones, "choclo");
  const forage = rankFor(list, "forraje");
  expect(forage.map((r) => [r.id, r.mejor])).toEqual([
    ["choclo-sin_cultivo", false],
    ["choclo-avena", true],
    ["choclo-haba", false],
  ]);
  expect(rankFor(list, "vender")[1].id).toBe("choclo-haba");
});

test("the next crop is sown about a month after the harvest and lasts its cycle", () => {
  expect(planDates("2027-03-10", 135)).toEqual({
    siembra: "2027-04-09",
    cosecha: "2027-08-22",
  });
});

test("the season line follows the sowing month", () => {
  expect([
    season("2027-04-09"),
    season("2027-09-30"),
    season("2027-10-01"),
  ]).toEqual(["seca", "seca", "lluvias"]);
  expect(defaultGoal(undefined, "2027-05-01")).toBe("agua");
  expect(defaultGoal(undefined, "2027-12-01")).toBe("tierra");
  expect(defaultGoal("vender", "2027-05-01")).toBe("vender");
});

test("choosing a plan creates the planned sowing and the plan for the zone", () => {
  const plan = planFor(
    { id: "choclo-haba", secuencia: ["choclo", "haba"] },
    "D9_itocta",
    "2027-04-09",
  );
  expect(plan.kind).toBe("plans");
  expect(plan.payload).toEqual({
    zone_id: "D9_itocta",
    rotacion_id: "choclo-haba",
    siembra: "2027-04-09",
  });
});
