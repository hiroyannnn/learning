import { Bank } from "./Bank";
import { Expression } from "./Expression";
import { Sum } from "./Sum";

export class Money implements Expression {
  public amount: number = 0;
  protected _currency: string = "";

  constructor(amount: number, currency: string) {
    this.amount = amount;
    this._currency = currency;
  }

  times(multiplier: number): Money {
    return new Money(this.amount * multiplier, this._currency);
  }

  plus(addend: Money): Expression {
    return new Sum(this, addend);
  }

  public reduce(bank: Bank, to: string): Money {
    const rate = bank.rate(this._currency, to);
    return new Money(this.amount / rate, to);
  }

  currency(): string {
    return this._currency;
  }

  public equals(object: Object): boolean {
    const money: Money = object as Money;

    return this.amount === money.amount && this.currency() === money.currency();
  }

  public static dollar(amount: number): Money {
    return new Money(amount, "USD");
  }

  public static franc(amount: number): Money {
    return new Money(amount, "CHF");
  }
}
