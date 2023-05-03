import { Money } from "./Money";
import { Sum } from "./Sum";

export class Bank {
  reduce(source: Expression, to: string): Money {
    const sum: Sum = source as Sum;
    const amount: number = sum.augend.amount + sum.addend.amount;

    return new Money(amount, to);
  }
}
