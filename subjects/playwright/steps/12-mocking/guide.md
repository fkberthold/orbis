# A stubbed request can't see the server

In Selenium, controlling what the page gets back from its API meant a proxy,
or, since Selenium 4, the DevTools bridge. A Postman mock server sits outside
the browser and needs the app pointed at it. Playwright intercepts inside the
browser context. `page.route` takes a URL pattern and a handler, and every
matching request goes to the handler instead of the network.

```ts
await page.route('**/api/orders', route =>
  route.fulfill({ status: 503, json: { error: 'down' } }));
await page.goto('/');
```

The handler can answer the request outright with `route.fulfill`, let it
through with `route.continue`, or fetch the real answer and change it.

Two details decide whether a stubbed test is testing what you think. The route
has to be in place before the request goes out, so for anything the page
fetches on load it goes before `page.goto`. And a request that doesn't match the
pattern goes to the real server with no warning. A typo in the pattern quietly
turns a stubbed test back into a real one.

The trade itself you know. A stub buys cases the real server won't produce on
demand, and it can't see anything wrong with what the real server sends. The
part I'd watch is narrower: a stub that doesn't look like the real answer.

A page can handle a malformed answer correctly by accident. Say the real server
sends JSON with its 500, and your stub sends plain text. The page fails to
parse the text and lands on its error message anyway, and the test passes
without ever checking the status. I suspect that's the most common way a
stubbed test ends up proving less than it looks like it does.

Playwright has a direct answer to it. `route.fetch` makes the real request, and
you change only the part the test is about, so the rest of the answer keeps the
server's real shape.

```ts
await page.route('**/api/orders', async route => {
  const response = await route.fetch();
  await route.fulfill({ response, json: [] }); // the real headers, an empty list
});
```
