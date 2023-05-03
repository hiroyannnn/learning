import { Money } from "./Money";
import { Sum } from "./Sum";

export class Bank {
  reduce(source: Expression, to: string): Money {
    if (source instanceof Money) {
      return source;
    }
    const sum: Sum = source as Sum;
    return sum.reduce(to);
  }
}
