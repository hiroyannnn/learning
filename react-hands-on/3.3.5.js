// const countdown = (v, fn) => {
//   fn(v);
//   return v > 0 ? countdown(v - 1, fn) : v;
// };

// countdown(10, (v) => console.log(v));

const countdown = (v, fn, delay = 1000) => {
  fn(v);
  return v > 0 ? setTimeout(() => countdown(v - 1, fn, delay), delay) : v;
};

const log = (v) => console.log(v);
countdown(10, log);
