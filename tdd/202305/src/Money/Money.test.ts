import { Franc } from "./Franc";
import { Money } from "./Money";

describe("Money", () => {
  describe("multiplication", () => {
    test("Dollar", () => {
      const five: Money = Money.dollar(5);

      expect(five.times(2)).toStrictEqual(Money.dollar(10));
      expect(five.times(3)).toStrictEqual(Money.dollar(15));
    });

    test("Franc", () => {
      const five: Money = Money.franc(5);

      expect(five.times(2)).toStrictEqual(Money.franc(10));
      expect(five.times(3)).toStrictEqual(Money.franc(15));
    });
  });

  test("equality", () => {
    expect(Money.dollar(5).equals(Money.dollar(5))).toBe(true);
    expect(Money.dollar(5).equals(Money.dollar(6))).toBe(false);
    expect(Money.franc(5).equals(Money.franc(5))).toBe(true);
    expect(Money.franc(5).equals(Money.franc(6))).toBe(false);
    expect(Money.franc(5).equals(Money.dollar(5))).toBe(false);
  });
  test("currency", () => {
    expect(Money.dollar(1).currency()).toBe("USD");
    expect(Money.franc(1).currency()).toBe("CHF");
  });
  test("different class equality", () => {
    expect(new Money(10, "CHF").equals(new Franc(10, "CHF"))).toBe(true);
  });
});
