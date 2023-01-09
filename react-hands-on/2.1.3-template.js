// const person = (firstName, lastName) => ({
//   first: firstName,
//   last: lastName,
// });
// console.log(person("Brad", "Janson"));

// const tahoe = {
//   mountains: ["Freel", "Rose", "Tallac", "Rubicon", "Silver"],
//   print: function (delay = 1000) {
//     setTimeout(function () {
//       console.log(this.mountains.join(", "));
//     }, delay);
//   },
// };

// console.log(this);
// tahoe.print();

const tahoe = {
  mountains: ["Freel", "Rose", "Tallac", "Rubicon", "Silver"],
  print: function (delay = 1000) {
    setTimeout(() => {
      console.log(this.mountains.join(", "));
    }, delay);
  },
};

console.log(this);
tahoe.print();
