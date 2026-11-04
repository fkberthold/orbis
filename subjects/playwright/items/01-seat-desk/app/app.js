// The desk holds four seats and two of them are already booked. A reservation
// takes a moment to confirm, which is the part worth testing.

const SEATS = ["A1", "A2", "A3", "A4"];
const TAKEN = new Set(["A2", "A3"]);
const SETTLE_MS = 300;

function el(id) {
  return document.getElementById(id);
}

function fillSeats() {
  const seat = el("seat");
  for (const s of SEATS) {
    const option = document.createElement("option");
    option.value = s;
    option.textContent = TAKEN.has(s) ? s + " (taken)" : s;
    seat.appendChild(option);
  }
}

function clearMessages() {
  el("error").textContent = "";
  el("banner").textContent = "";
}

function settle() {
  return new Promise(function (resolve) {
    setTimeout(resolve, SETTLE_MS);
  });
}

async function reserve(event) {
  event.preventDefault();
  clearMessages();

  const name = el("name").value.trim();
  if (name === "") {
    el("error").textContent = "Enter a name.";
    return;
  }

  const seat = el("seat").value;

  // The button stays down for the whole round trip, so a second click during
  // the wait cannot start a second reservation.
  el("reserve").disabled = true;
  el("status").textContent = "Reserving...";

  await settle();

  if (TAKEN.has(seat)) {
    el("error").textContent = "Seat " + seat + " is already taken.";
    el("status").textContent = "";
    el("reserve").disabled = false;
    return;
  }

  TAKEN.add(seat);

  const row = document.createElement("li");
  row.className = "reservation";
  row.textContent = seat + " - " + name;
  el("reservations").appendChild(row);

  el("banner").textContent = "Reserved " + seat + " for " + name + ".";
  el("status").textContent = "";
  el("reserve").disabled = false;
}

fillSeats();
el("desk").addEventListener("submit", reserve);
