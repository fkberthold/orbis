// A line's text comes back only as the answer to a reveal, and the server has
// already written the reveal down by then. Nothing here records anything.

async function reveal(button) {
  const main = document.querySelector("main[data-item]");
  const line = Number(button.dataset.line);
  button.disabled = true;

  const reply = await fetch("/reveal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item: main.dataset.item, line: line }),
  });
  if (!reply.ok) {
    button.disabled = false;
    return;
  }

  const answer = await reply.json();
  const code = document.createElement("code");
  code.textContent = answer.text;
  const row = document.getElementById("line-" + line);
  button.replaceWith(code);
  row.className = "line";
}

document.addEventListener("click", function (event) {
  const button = event.target.closest("button[data-line]");
  if (button) {
    reveal(button);
  }
});
