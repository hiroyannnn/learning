import { Dollar } from "./Dollar";
import { Franc } from "./Franc";

export abstract class Money {
  protected amount: number = 0;
  protected _currency: string = "";

  abstract times(multiplier: number): Money;
  currency(): string {
    return this._currency;
  }

  public equals(object: Object): boolean {
    const money: Money = object as Money;

    return (
      this.amount === money.amount &&
      this.constructor.name === money.constructor.name
    );
  }

  public static dollar(amount: number): Money {
    return new Dollar(amount);
  }

  public static franc(amount: number): Money {
    return new Franc(amount);
  }
}
