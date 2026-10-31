# Parts lookup: hold the catalog search to its four rules

The front counter at Northgate Auto Repair looks up parts on a small page. The
page fetches the catalog, `parts.json`, over the network, then lists the parts
that match what's typed in the search box. The catalog takes a moment to
arrive, and it doesn't always arrive.

Write Playwright tests that hold the lookup to the rules below.

## The rules

1. When the page opens, it shows "Loading parts..." and the search box is
   disabled. Once the catalog arrives, the notice goes away, the box is
   enabled, and every part in the catalog is listed in catalog order.
2. Typing in the search box lists only the parts whose name or part number
   contains the typed text, ignoring upper and lower case. The parts stay in
   catalog order.
3. A search that matches no part lists no parts and shows
   `No parts match "<the typed text>".`
4. If the catalog request answers with an error status, like 500, the page
   shows "Couldn't load the parts catalog." If it answers with an empty list,
   the page shows "The parts catalog is empty." Either way, the loading notice
   goes away and no parts are listed.

## The network, and what you may stub

For rules 1 to 3, your tests must load the real `parts.json`. Don't stub it.
Some of the broken copies change the catalog file itself, and a test that
answers the request on its own never sees that.

For rule 4 you have to stub, because the real file never fails. Use
`page.route` to answer the catalog request yourself, and set it up before
`page.goto`.

## What you are given

- `app/` is the lookup itself. `app/parts.json` is the catalog, and your tests
  may name parts from it.
- Your tests run against a `--base-url`, so `page.goto("/")` reaches it.
- `page` is the pytest-playwright fixture. Nothing else is set up for you.

## How this is graded

Your tests run against the real lookup and against broken copies of it.
Passing the real lookup is not the bar, because a test that asserts nothing
passes it. Each broken copy breaks exactly one rule, and your tests have to
notice.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, so nothing was established |

A cell says what happened, not whether it is good news. `silent` against the
real lookup is correct. `silent` against a broken copy is the thing to go fix.
