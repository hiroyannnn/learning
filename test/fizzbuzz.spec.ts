import { fizzbuzz } from "../src/fizzbuzz";

describe("fizzbuzzTest", () => {
  const cases: Array<[number, number | string]> = [
    [1, 1],
    [2, 2],
    [3, "fizz"],
  ];
  cases.forEach((testCase) => {
    it(`fib${testCase}`, () => {
      expect(fizzbuzz(testCase[0])).toBe(testCase[1]);
    });
  });
});
