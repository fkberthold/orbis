// The lookup fetches the catalog over the network and lists the parts that
// match a search. The fetch is the part worth testing, because a test that
// never waits for it can pass without ever seeing the catalog.

// A fixed pause after the fetch, so the loading notice stays up long enough
// to check and the order of events never depends on the network.
const SETTLE_MS = 600;

let catalog = [];

function el(id) {
  return document.getElementById(id);
}

function settle() {
  return new Promise(function (resolve) {
    setTimeout(resolve, SETTLE_MS);
  });
}

function matches(part, text) {
  const wanted = text.toLowerCase();
  return (
    part.name.toLowerCase().includes(wanted) ||
    part.number.toLowerCase().includes(wanted)
  );
}

function row(part) {
  const item = document.createElement("li");
  item.className = "part";

  const number = document.createElement("span");
  number.className = "number";
  number.textContent = part.number;

  const name = document.createElement("span");
  name.className = "name";
  name.textContent = part.name;

  item.append(number, " ", name);
  return item;
}

function render() {
  const text = el("search").value.trim();
  const shown = catalog.filter(function (part) {
    return matches(part, text);
  });

  el("results").replaceChildren(...shown.map(row));

  el("empty").textContent =
    shown.length === 0 ? 'No parts match "' + text + '".' : "";
}

async function load() {
  el("status").textContent = "Loading parts...";

  let parts = null;
  try {
    const response = await fetch("parts.json");
    // fetch only throws when the request gets no answer at all. A 500 is an
    // answer, so it has to be checked here or it gets read as a catalog.
    if (!response.ok) {
      throw new Error("catalog answered " + response.status);
    }
    parts = await response.json();
  } catch (problem) {
    parts = null;
  }

  await settle();
  el("status").textContent = "";

  if (parts === null) {
    el("error").textContent = "Couldn't load the parts catalog.";
    return;
  }
  if (parts.length === 0) {
    el("error").textContent = "The parts catalog is empty.";
    return;
  }

  catalog = parts;
  // The box stays off until there's something to search, so nobody types
  // into a list that isn't there yet.
  el("search").disabled = false;
  render();
}

el("search").addEventListener("input", render);
load();
