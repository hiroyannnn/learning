import { fizzbuzz } from "../src/fizzbuzz";

describe("fizzbuzzTest", () => {
  const cases: Array<[number, number | string]> = [
    [1, 1],
    [2, 2],
    [3, "fizz"],
    [4, 4],
    [5, "buzz"],
  ];
  cases.forEach((testCase) => {
    it(`fizz buzz${testCase}`, () => {
      expect(fizzbuzz(testCase[0])).toBe(testCase[1]);
    });
  });
});
