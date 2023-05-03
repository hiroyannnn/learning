function greet(name: string) {
  return "Hello, " + name;
}

let greet2 = function (name: string) {
  return "Hello, " + name;
};

let greet3 = (name: string) => {
  return "Hello, " + name;
};

let greet4 = (name: string) => "Hello, " + name;

let greet5 = new Function("name", 'return "Hello, " + name;');
,
