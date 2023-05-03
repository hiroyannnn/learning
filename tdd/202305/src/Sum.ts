import { Bank } from "./Bank";
import { Expression } from "./Expression";
import { Money } from "./Money";

export class Sum implements Expression {
  augend: Money;
  addend: Money;

  constructor(augend: Money, addend: Money) {
    this.addend = addend;
    this.augend = augend;
  }

  public reduce(bank: Bank, to: string): Money {
    const amount: number = this.augend.amount + this.addend.amount;
    return new Money(amount, to);
  }
}
