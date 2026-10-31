# A stubbed request can't see the server

`page.route` lets a test answer the page's network requests itself. You give it
a URL pattern and a handler, and every matching request goes to the handler
instead of the network. The handler can let the request through, change it, or
answer it outright.

```ts
await page.route('**/api/orders', route =>
  route.fulfill({ status: 503, json: { error: 'down' } }));
await page.goto('/');
```

The handler is a short function, `route => ...`, that Playwright calls with
each matching request. `route.fulfill` answers it.

Two details shape how a stubbed test is written. The route has to be in place
before the request goes out, so for anything the page fetches on load it goes
before `page.goto`. And a request that doesn't match the pattern goes to the
real server, with no warning. A typo in the pattern quietly turns a stubbed
test back into a real one.

A stub buys control over a case the real server won't produce on demand, like
a 500, a slow answer or an empty list. It costs everything on the far side of
the request. A stubbed test checks how the page handles the
answer you wrote, so it can't see anything wrong with the answer the server
really sends.

| a bug in... | a test against the real server | a test with the request stubbed |
|---|---|---|
| how the page shows a good answer | sees it | sees it, if the stub looks like the real answer |
| how the page handles an error status | only if the server can be made to fail | sees it |
| the data the server sends | sees it | can't see it |
| the address the page asks for | sees it | only by luck, as a request the stub missed |

So the two kinds of test aren't stand-ins for each other. I'd use the real
server for everything it can produce, and stub only the cases it can't.

When you do stub, make the answer look like the real one, down to the shape of
the body. A page can handle a malformed answer correctly by accident. Say the
real server sends JSON with its 500, and your stub sends plain text. The page
might fail to parse the text and land on its error message anyway, and the test
passes without ever checking the status. I suspect that's the most common way a
stubbed test ends up proving less than it looks like it does.
