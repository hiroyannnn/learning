import { Money } from "./Money";

export class Dollar extends Money {
  private _currency: string = "";

  constructor(amount: number) {
    super();
    this.amount = amount;
    this._currency = "USD";
  }

  currency(): string {
    return this._currency;
  }

  times(multiplier: number): Money {
    return new Dollar(this.amount * multiplier);
  }
}
