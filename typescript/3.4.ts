type Age = number;
type Person = {
  name: string;
  age: Age;
};

let age: Age = 55;

let driver: Person = {
  name: "James May",
  age: age
};

type Color = "red";
let x = Math.random() < 0.5;
if (x) {
  type Color = "blue";
  let b: Color = "blue";
} else {
  let c: Color = "red";
}

type Cat = { name: string; purrs: boolean };
type Dog = { name: string; barks: boolean; wags: boolean };
type CatOrDogOrBoth = Cat | Dog;
type CatAndDog = Cat & Dog;

let a: CatOrDogOrBoth = {
  name: "Bonkers",
  purrs: true
};
a = {
  name: "Domino",
  barks: true,
  wags: true
};
a = {
  name: "Donkers",
  barks: true,
  wags: true,
  purrs: true
};

let b: CatAndDog = {
  name: "Domino",
  barks: true,
  wags: true,
  purrs: true
};

function trueOrNull(isTrue: boolean) {
  if (isTrue) {
    return "true";
  }
  return null;
}

type Returns = string | null;

function bb(a: string, b: number) {
  return a || b;
}

let a = 1042;
let b = "apples and oranges";
const c = "pineapples";
let d = [true, true, false];
let e = { type: "ficus" };
let f = [1, false];
const g = [3];
let h = null;

let i: 3 = 3;
i = 4;

let j = [1, 2, 3];
j.push(4);
j.push("5");

let k: never = 4;

let l: unknown = 4;
let m = l * 2;
