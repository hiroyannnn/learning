import { Money } from "./Money";

export class Franc extends Money {
  constructor(amount: number) {
    super();
    this.amount = amount;
  }

  currency(): string {
    return "CHF";
  }

  times(multiplier: number): Money {
    return new Franc(this.amount * multiplier);
  }
}
