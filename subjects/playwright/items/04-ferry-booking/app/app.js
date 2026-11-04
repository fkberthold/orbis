// A three-step ferry booking on hash routes. Each step is drawn fresh from
// `trip` every time it's shown, so going Back keeps what was entered only
// because the draw puts it back. That's the part worth testing.

const CROSSINGS = {
  dawn: { label: "07:30 Harbor to Gull Isle", price: 12 },
  noon: { label: "12:15 Harbor to Gull Isle", price: 15 },
  dusk: { label: "18:45 Harbor to Gull Isle", price: 18 },
};

const trip = { crossing: "", lead: "", count: "1" };
const bookings = [];
let booked = null;
let nextRef = 101;

function el(id) {
  return document.getElementById(id);
}

function go(step) {
  location.hash = "#/" + step;
}

// Two confirms of the same trip should land on one booking, so a booking
// remembers exactly which trip it was made from.
function tripKey() {
  return trip.crossing + "|" + trip.lead + "|" + trip.count;
}

function fare() {
  return CROSSINGS[trip.crossing].price * Number(trip.count);
}

function drawCrossing() {
  let html = "<h2 id=\"step-title\">1. Pick a crossing</h2><fieldset>";
  for (const key of Object.keys(CROSSINGS)) {
    const c = CROSSINGS[key];
    html +=
      "<label for=\"crossing-" + key + "\">" +
      "<input type=\"radio\" name=\"crossing\" id=\"crossing-" + key +
      "\" value=\"" + key + "\"> " +
      c.label + " ($" + c.price + " a person)</label>";
  }
  html += "</fieldset><button id=\"next\" type=\"button\">Next</button>";
  el("step").innerHTML = html;

  // Put back the crossing picked earlier, so Back doesn't lose it.
  if (trip.crossing) {
    el("crossing-" + trip.crossing).checked = true;
  }

  el("next").addEventListener("click", function () {
    const picked = document.querySelector("input[name=crossing]:checked");
    if (!picked) {
      el("error").textContent = "Pick a crossing.";
      return;
    }
    trip.crossing = picked.value;
    go("passengers");
  });
}

function drawPassengers() {
  let html =
    "<h2 id=\"step-title\">2. Passengers</h2>" +
    "<div class=\"field\"><label for=\"lead\">Lead passenger</label>" +
    "<input id=\"lead\" type=\"text\" autocomplete=\"off\"></div>" +
    "<div class=\"field\"><label for=\"count\">Passengers</label>" +
    "<select id=\"count\">";
  for (const n of ["1", "2", "3", "4"]) {
    html += "<option value=\"" + n + "\">" + n + "</option>";
  }
  html += "</select></div><button id=\"next\" type=\"button\">Next</button>";
  el("step").innerHTML = html;

  // Same as the crossing step: what was entered goes back in.
  el("lead").value = trip.lead;
  el("count").value = trip.count;

  el("next").addEventListener("click", function () {
    const lead = el("lead").value.trim();
    if (lead === "") {
      el("error").textContent = "Enter the lead passenger's name.";
      return;
    }
    trip.lead = lead;
    trip.count = el("count").value;
    go("review");
  });
}

function drawReview() {
  // Built from the trip as it stands now, so a change made after going Back
  // shows up here.
  const c = CROSSINGS[trip.crossing];
  el("step").innerHTML =
    "<h2 id=\"step-title\">3. Review and confirm</h2><dl>" +
    "<dt>Crossing</dt><dd id=\"review-crossing\">" + c.label + "</dd>" +
    "<dt>Lead passenger</dt><dd id=\"review-lead\">" + trip.lead + "</dd>" +
    "<dt>Passengers</dt><dd id=\"review-count\">" + trip.count + "</dd>" +
    "<dt>Fare</dt><dd id=\"review-fare\">$" + fare() + "</dd>" +
    "</dl><button id=\"confirm\" type=\"button\">Confirm</button>";

  el("confirm").addEventListener("click", function () {
    // Confirming the same trip again finds the booking already made rather
    // than making a second one.
    if (!booked || booked.key !== tripKey()) {
      booked = { key: tripKey(), ref: "FB-" + nextRef };
      nextRef += 1;
      bookings.push({ ref: booked.ref, label: CROSSINGS[trip.crossing].label });
    }
    go("done");
  });
}

function drawDone() {
  let html =
    "<h2 id=\"step-title\">Booked</h2>" +
    "<p id=\"reference\">Booking " + booked.ref + "</p>" +
    "<h3>Your bookings</h3><ul id=\"bookings\">";
  for (const b of bookings) {
    html += "<li class=\"booking\">" + b.ref + " - " + b.label + "</li>";
  }
  html += "</ul>";
  el("step").innerHTML = html;
}

// Which steps need what, so a later step opened by its address can tell it
// was skipped to.
function allowed(step) {
  if (step === "crossing") return true;
  if (step === "passengers") return trip.crossing !== "";
  if (step === "review") return trip.crossing !== "" && trip.lead !== "";
  if (step === "done") return booked !== null;
  return false;
}

const DRAW = {
  crossing: drawCrossing,
  passengers: drawPassengers,
  review: drawReview,
  done: drawDone,
};

function route() {
  el("error").textContent = "";
  const step = location.hash.replace(/^#\//, "");
  if (!allowed(step)) {
    // replace rather than a new entry, so Back doesn't return to the address
    // that bounced and bounce again.
    location.replace("#/crossing");
    return;
  }
  DRAW[step]();
}

window.addEventListener("hashchange", route);
route();
