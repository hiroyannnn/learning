import { fib } from "../src/fibonacci";

describe("FibonacciTest", () => {
  const cases: Array<Array<number>> = [
    [0, 0],
    [1, 1]
  ];
  cases.forEach(testCase => {
    it(`fib${testCase}`, () => {
      expect(fib(testCase[0])).toBe(testCase[1]);
    });
  });
});
