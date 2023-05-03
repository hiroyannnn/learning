export class Money {
  protected amount: number = 0;

  public equals(object: Object): boolean {
    const money: Money = object as Money;
    return this.amount === money.amount;
  }
}
