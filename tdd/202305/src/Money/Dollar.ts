import { Money } from "./Money";

export class Dollar extends Money {
  constructor(amount: number) {
    super();
    this.amount = amount;
    this._currency = "USD";
  }

  times(multiplier: number): Money {
    return new Dollar(this.amount * multiplier);
  }
}
