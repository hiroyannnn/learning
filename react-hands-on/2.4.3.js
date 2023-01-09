// console.log(fetch("https://api.randomuser.me/?nat=US&results=1"));

// fetch("https://api.randomuser.me/?nat=US&results=1").then((res) =>
//   console.log(res.json())
// );

// fetch("https://api.randomuser.me/?nat=US&results=1")
//   .then((res) => res.json())
//   .then((json) => json.results)
//   .then(console.log)
//   .catch(console.error);

const getFakePerson = async () => {
  try {
    const res = await fetch("https://api.randomuser.me/?nat=US&results=1");
    const { results } = await res.json();
    console.log(results);
  } catch (error) {
    console.log(error);
  }
};
getFakePerson();
