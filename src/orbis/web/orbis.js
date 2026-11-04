// The live parts of the reading pages, filled in from orbis.page.
//
// The built site is static and knows nothing that happens while it runs. The
// app's address, the last verdict and the worked answer all come from the
// server, so this file asks for them and draws them.
//
// A line of the worked answer only reaches the browser as the reply to a
// reveal, and the server has already written the reveal down by then. Nothing
// here records anything, and no hidden line's text is ever sent.
//
// navigation.instant loads pages the way a single-page app does, so a script
// that ran on load would run once, on whichever page was opened first. So the
// work hangs off document$, which mkdocs-material emits on the first load and
// again after every instant navigation. The click handler is bound once, on
// document, since document is the one thing navigation doesn't replace.

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (key === "text") {
      node.textContent = value;
    } else {
      node.setAttribute(key, value);
    }
  }
  for (const child of children || []) {
    node.append(child);
  }
  return node;
}

function code(text) {
  return el("code", { text: text });
}

function table(head, rows) {
  const thead = el("thead", {}, [el("tr", {}, head.map((h) => el("th", { text: h })))]);
  const body = el("tbody", {}, rows.map((cells) => el("tr", {}, cells.map((c) => el("td", {}, [c])))));
  return el("table", {}, [thead, body]);
}

function block(text) {
  return el("pre", {}, [code(text)]);
}

function drawApp(box, data) {
  const app = data.app;
  const link = el("a", { href: app.url, target: "_blank", rel: "noopener", text: app.url });
  box.replaceChildren(
    el("p", {}, ["The real app is running at ", link,
      ". Poke at it, watch what changes and when, and write your tests against it."]),
    el("p", {}, ["Write your tests in ", code(app.workspace + "/" + app.mine),
      ". In a shell, after ", code("source env.sh"), " and ", code("cd " + app.workspace), ":"]),
    table(["for", "run"], app.commands.map(([what, command]) => [document.createTextNode(what), code(command)])),
  );
}

function drawAttempt(box, data) {
  const last = data.attempt;
  if (!last) {
    box.replaceChildren(el("p", { text: "No attempt graded yet. Grade one with" }), block(data.grade));
    return;
  }
  const word = el("span", { class: "orbis-verdict " + last.word, text: last.word });
  const rows = last.cells.map((cell) => {
    // One collapsed entry per test, named after it, with the command that
    // opens its trace inside. Spelled out, the commands bury the verdict.
    const traces = el("div", {}, cell.traces.map((t) =>
      el("details", { class: "orbis-trace" }, [el("summary", { text: t.test }), block(t.command)])));
    return [document.createTextNode(cell.environment), el("span", { class: "orbis-cell " + cell.cell, text: cell.cell }), traces];
  });
  box.replaceChildren(
    el("p", {}, ["The gate ", word, " ", code(last.candidate), " at " + last.at + "."]),
    table(["environment", "cell", "what each test saw, as a trace"], rows),
    el("p", { text: "Open a test's entry for the command that shows its trace. Run it from " + data.app.workspace + "." }),
    el("p", { text: "Grade another with" }),
    block(data.grade),
  );
}

function drawAnswer(box, data) {
  const rows = data.lines.map((line) => {
    if (line.blank) {
      return el("li", { class: "blank" });
    }
    const margin = el("span", { class: "margin", text: line.margin });
    if ("text" in line) {
      return el("li", { class: "line", id: "line-" + line.number }, [margin, code(line.text)]);
    }
    const button = el("button", { type: "button", "data-line": line.number, text: "reveal" });
    return el("li", { class: "line hidden", id: "line-" + line.number }, [margin, button]);
  });
  box.replaceChildren(el("ol", { class: "lines" }, rows));
}

const DRAW = { app: drawApp, attempt: drawAttempt, answer: drawAnswer };

async function boot() {
  const boxes = document.querySelectorAll("[data-orbis-part]");
  if (boxes.length) {
    const item = boxes[0].dataset.orbisItem;
    const reply = await fetch("/api/practice/" + item, { cache: "no-store" });
    if (reply.ok) {
      const data = await reply.json();
      for (const box of boxes) {
        DRAW[box.dataset.orbisPart](box, data);
      }
    }
  }
  const marks = document.querySelectorAll(".orbis-status[data-orbis-item]");
  if (marks.length) {
    const reply = await fetch("/api/status", { cache: "no-store" });
    if (reply.ok) {
      const words = await reply.json();
      for (const mark of marks) {
        const word = words[mark.dataset.orbisItem];
        mark.textContent = word || "";
        mark.className = "orbis-status" + (word ? " " + word : "");
      }
    }
  }
}

async function reveal(button) {
  const item = button.closest("[data-orbis-item]").dataset.orbisItem;
  const line = Number(button.dataset.line);
  button.disabled = true;

  const reply = await fetch("/reveal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item: item, line: line }),
  });
  if (!reply.ok) {
    button.disabled = false;
    return;
  }

  const answer = await reply.json();
  const row = document.getElementById("line-" + line);
  button.replaceWith(code(answer.text));
  row.className = "line";
}

document.addEventListener("click", function (event) {
  const button = event.target.closest("button[data-line]");
  if (button) {
    reveal(button);
  }
});

document$.subscribe(function () {
  boot();
});
