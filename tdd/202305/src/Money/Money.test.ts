import { Dollar } from "./Dollar";
import { Franc } from "./Franc";

describe("Money", () => {
  describe("multiplication", () => {
    test("Dollar", () => {
      const five: Dollar = new Dollar(5);

      expect(five.times(2)).toStrictEqual(new Dollar(10));
      expect(five.times(3)).toStrictEqual(new Dollar(15));
    });

    test("Franc", () => {
      const five: Franc = new Franc(5);

      expect(five.times(2)).toStrictEqual(new Franc(10));
      expect(five.times(3)).toStrictEqual(new Franc(15));
    });
  });

  test("equality", () => {
    expect(new Dollar(5).equals(new Dollar(5))).toBe(true);
    expect(new Dollar(5).equals(new Dollar(6))).toBe(false);
    expect(new Franc(5).equals(new Franc(5))).toBe(true);
    expect(new Franc(5).equals(new Franc(6))).toBe(false);
  });
});