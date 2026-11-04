// A bike shop's repair queue. Three of the five jobs are brake pads for three
// different customers, so a job's title never picks out one row by itself.
// The ticket number does.

const PRIORITIES = ["High", "Normal", "Low"];
const RANK = { High: 0, Normal: 1, Low: 2 };

// Kept in the order the jobs came in, which is ticket order. The queue on the
// page is a sorted copy, so this order never shows directly.
const jobs = [
  { ticket: 101, title: "Brake pads", customer: "Ruiz", priority: "Normal" },
  { ticket: 102, title: "Flat tire", customer: "Okafor", priority: "High" },
  { ticket: 103, title: "Brake pads", customer: "Chen", priority: "Low" },
  { ticket: 104, title: "Chain tune", customer: "Patel", priority: "Normal" },
  { ticket: 105, title: "Brake pads", customer: "Ito", priority: "Normal" },
];

function el(id) {
  return document.getElementById(id);
}

// Most urgent first. Inside one priority the job that came in first goes
// first, so touching a job never lets it jump ahead of an older one.
function queueOrder(a, b) {
  if (RANK[a.priority] !== RANK[b.priority]) {
    return RANK[a.priority] - RANK[b.priority];
  }
  return a.ticket - b.ticket;
}

function cell(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

function row(job) {
  const li = document.createElement("li");
  li.className = "job";
  li.dataset.ticket = String(job.ticket);

  li.appendChild(cell("span", "ticket", "#" + job.ticket));
  li.appendChild(cell("span", "title", job.title));
  li.appendChild(cell("span", "customer", job.customer));

  const select = document.createElement("select");
  select.className = "priority";
  select.setAttribute("aria-label", "Priority");
  for (const p of PRIORITIES) {
    const option = document.createElement("option");
    option.value = p;
    option.textContent = p;
    option.selected = p === job.priority;
    select.appendChild(option);
  }
  li.appendChild(select);

  li.appendChild(cell("button", "finish", "Finish"));
  return li;
}

function render() {
  const rows = jobs.slice().sort(queueOrder).map(row);
  el("queue").replaceChildren(...rows);
}

// The row carries its ticket, and the ticket is the only thing that names one
// job. Two rows can share everything else.
function jobFor(li) {
  const ticket = Number(li.dataset.ticket);
  return jobs.find(function (job) {
    return job.ticket === ticket;
  });
}

function changePriority(event) {
  if (!event.target.matches("select.priority")) {
    return;
  }
  const job = jobFor(event.target.closest("li.job"));
  job.priority = event.target.value;
  render();
}

function finish(event) {
  if (!event.target.matches("button.finish")) {
    return;
  }
  const job = jobFor(event.target.closest("li.job"));
  const label = "#" + job.ticket + " " + job.title;

  // A native confirm, so the page stops until somebody answers it.
  if (!window.confirm("Finish " + label + " for " + job.customer + "?")) {
    return;
  }

  jobs.splice(jobs.indexOf(job), 1);
  el("done").appendChild(cell("li", "done", label + " (" + job.customer + ")"));
  render();
}

render();
el("queue").addEventListener("change", changePriority);
el("queue").addEventListener("click", finish);
