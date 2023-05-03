import { Bank } from "./Bank";
import { Expression } from "./Expression";
import { Money } from "./Money";
import { Sum } from "./Sum";

describe("Money", () => {
  describe("multiplication", () => {
    test("Dollar", () => {
      const five: Money = Money.dollar(5);

      expect(five.times(2)).toStrictEqual(Money.dollar(10));
      expect(five.times(3)).toStrictEqual(Money.dollar(15));
    });
  });

  test("equality", () => {
    expect(Money.dollar(5).equals(Money.dollar(5))).toBe(true);
    expect(Money.dollar(5).equals(Money.dollar(6))).toBe(false);
    expect(Money.franc(5).equals(Money.dollar(5))).toBe(false);
  });
  test("currency", () => {
    expect(Money.dollar(1).currency()).toBe("USD");
    expect(Money.franc(1).currency()).toBe("CHF");
  });

  test("simple addition", () => {
    const five: Money = Money.dollar(5);
    const sum: Expression = five.plus(five);
    const bank: Bank = new Bank();
    const reduced: Money = bank.reduce(sum, "USD");
    expect(reduced).toStrictEqual(Money.dollar(10));
  });

  test("plus returns sum", () => {
    const five: Money = Money.dollar(5);
    const result: Expression = five.plus(five);
    const sum: Sum = result as Sum;
    expect(sum.augend).toStrictEqual(five);
    expect(sum.addend).toStrictEqual(five);
  });

  test("reduce sum", () => {
    const sum: Expression = new Sum(Money.dollar(3), Money.dollar(4));
    const bank: Bank = new Bank();
    const result: Money = bank.reduce(sum, "USD");
    expect(result).toStrictEqual(Money.dollar(7));
  });

  test("reduce money", () => {
    const bank: Bank = new Bank();
    const result: Money = bank.reduce(Money.dollar(1), "USD");
    expect(result).toStrictEqual(Money.dollar(1));
  });

  test("reduce money different currency", () => {
    const bank: Bank = new Bank();
    bank.addRate("CHF", "USD", 2);
    const result: Money = bank.reduce(Money.franc(2), "USD");
    expect(result).toStrictEqual(Money.dollar(1));
  });
});
