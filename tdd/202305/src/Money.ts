export class Dollar {
  private amount: number = 0;

  constructor(amount: number) {
    this.amount = amount;
  }

  times(multiplier: number): Dollar {
    return new Dollar(this.amount * multiplier);
  }

  public equals(object: Object): boolean {
    const dollar: Dollar = object as Dollar;
    return this.amount === dollar.amount;
  }
}
