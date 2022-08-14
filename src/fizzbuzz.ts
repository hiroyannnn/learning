type FizzBuzz = number | string;
export const fizzbuzz = (n: number): FizzBuzz => {
  if (n % 3 === 0) {
    return "fizz";
  }
  return n;
};
