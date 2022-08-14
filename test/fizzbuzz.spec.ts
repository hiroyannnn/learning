import { fizzbuzz } from "../src/fizzbuzz";

describe("fizzbuzzTest", () => {
  const cases: Array<Array<number>> = [
    [1, 1],
    [2, 2],
  ];
  cases.forEach((testCase) => {
    it(`fib${testCase}`, () => {
      expect(fizzbuzz(testCase[0])).toBe(testCase[1]);
    });
  });
});
