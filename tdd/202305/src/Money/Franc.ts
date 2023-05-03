import { Money } from "./Money";

export class Franc extends Money {
  private _currency: string = "";

  constructor(amount: number) {
    super();
    this.amount = amount;
    this._currency = "CHF";
  }

  currency(): string {
    return this._currency;
  }

  times(multiplier: number): Money {
    return new Franc(this.amount * multiplier);
  }
}
