import { Money } from "./Money";

export class Dollar extends Money {
  constructor(amount: number) {
    super();
    this.amount = amount;
  }

  currency(): string {
    return "USD";
  }

  times(multiplier: number): Money {
    return new Dollar(this.amount * multiplier);
  }
}
