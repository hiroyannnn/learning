import { Money } from "./Money";

export class Sum implements Expression {
  augend: Money | undefined;
  addend: Money | undefined;

  constructor(augend: Money, addend: Money) {
    this.addend = addend;
    this.augend = augend;
  }
}
