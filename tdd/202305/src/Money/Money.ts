export class Money {
  protected amount: number = 0;
  protected _currency: string = "";

  constructor(amount: number, currency: string) {
    this.amount = amount;
    this._currency = currency;
  }

  times(multiplier: number): Money {
    return new Money(this.amount * multiplier, this._currency);
  }

  plus(addend: Money): Money {
    return new Money(this.amount + addend.amount, this._currency);
  }

  currency(): string {
    return this._currency;
  }

  public equals(object: Object): boolean {
    const money: Money = object as Money;

    return this.amount === money.amount && this.currency() === money.currency();
  }

  public static dollar(amount: number): Money {
    return new Money(amount, "USD");
  }

  public static franc(amount: number): Money {
    return new Money(amount, "CHF");
  }
}
