export class Franc {
  private amount: number = 0;

  constructor(amount: number) {
    this.amount = amount;
  }

  times(multiplier: number): Franc {
    return new Franc(this.amount * multiplier);
  }

  public equals(object: Object): boolean {
    const franc: Franc = object as Franc;
    return this.amount === franc.amount;
  }
}
