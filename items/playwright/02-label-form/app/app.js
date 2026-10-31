// A label desk for a small warehouse. The desk checks a label before it
// answers, and the answer is either a printed label or a message under each
// field that's wrong. Both arrive after the same wait, so a test that looks
// for "nothing printed" before the answer is in will pass for the wrong reason.

const CHECK_MS = 400;
const MAX_KG = 30;
const EXPRESS_MAX_KG = 5;
const FIELDS = ["recipient", "postcode", "weight", "service"];

function el(id) {
  return document.getElementById(id);
}

function check() {
  return new Promise(function (resolve) {
    setTimeout(resolve, CHECK_MS);
  });
}

function clearErrors() {
  for (const field of FIELDS) {
    el(field + "-error").textContent = "";
  }
}

// Every rule runs, so a label with three mistakes gets three messages rather
// than one at a time.
function validate(label) {
  const errors = {};

  if (label.recipient === "") {
    errors.recipient = "Enter a recipient.";
  }

  if (!/^\d{5}$/.test(label.postcode)) {
    errors.postcode = "Postcode must be five digits.";
  }

  const weightOk = Number.isFinite(label.weight) &&
    label.weight > 0 && label.weight <= MAX_KG;
  if (!weightOk) {
    errors.weight = "Weight must be over 0 and at most 30 kg.";
  }

  // Only a weight that's fine on its own gets measured against Express, so a
  // bad weight is reported once, under the weight.
  if (weightOk && label.service === "Express" && label.weight > EXPRESS_MAX_KG) {
    errors.service = "Express takes 5 kg or less.";
  }

  return errors;
}

function readForm() {
  return {
    recipient: el("recipient").value.trim(),
    postcode: el("postcode").value.trim(),
    weight: Number(el("weight").value.trim() || NaN),
    service: el("service").value,
  };
}

function printLabel(label) {
  const row = document.createElement("li");
  row.className = "label";
  row.textContent = label.recipient + ", " + label.postcode + ", " +
    label.weight + " kg, " + label.service;
  el("labels").appendChild(row);
}

function resetForm() {
  el("recipient").value = "";
  el("postcode").value = "";
  el("weight").value = "";
}

async function submit(event) {
  event.preventDefault();
  clearErrors();

  const label = readForm();

  // The button stays down while the desk checks, so a second press can't
  // print the same label twice.
  el("print").disabled = true;
  el("status").textContent = "Checking...";

  await check();

  const errors = validate(label);
  for (const field of Object.keys(errors)) {
    el(field + "-error").textContent = errors[field];
  }

  if (Object.keys(errors).length === 0) {
    printLabel(label);
    resetForm();
  }

  el("status").textContent = "";
  el("print").disabled = false;
}

el("label-form").addEventListener("submit", submit);
