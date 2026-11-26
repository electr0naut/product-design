# FXL-7 landed, 53/53 hidden tests, and the page does not work in a browser

I rebuilt FIX Lens from the eleven landed patches and loaded `index.html` in Chromium (Playwright), served over
HTTP, with a 7-message sample log.

## Result on the landed code: nothing is decoded

The browser console shows, twice: `Connecting to '.../src/dictionary/fix42.json' violates the following Content
Security Policy directive: "connect-src 'none'"`. `src/dictionary.js` imports the dictionaries as JSON modules.
Browsers apply `connect-src` to JSON module imports, the PRD's CSP sets `connect-src 'none'`, the module graph
fails, and the Decode button does nothing. Every gate, the review, the spec pass and all 53 hidden tests passed,
because they all run in Node or jsdom, where no CSP applies. **Nothing in the pipeline ever loaded the page in a
browser.**

## With the dictionaries as JS modules (my local copy), the page works

6 cards, the timeline with a SequenceGap, one `BodyLength` error, no console message, no request to another
origin, no dialog and no `<img>` from the pasted `<img src=x onerror=alert(1)>`. Screenshot:
`fix-lens/browser-check/fixlens-with-fix-preview.png` (my local patch, not landed code).

## My security read of `index.html`, `main.js` and `render.js`

Nothing to fix: the CSP is first in `<head>`, there is no inline code, `render` only uses `createElement` with fixed
tag names, `textContent` and a fixed class name, and no attribute is ever set from pasted data.

## Other gaps the review left as notes (now criteria)

- The timeline rows show only the number, name and detail. PRD AC-010 requires SendingTime, sender, target,
  MsgSeqNum, ClOrdID and OrderID (review note F2, high, confidence 75, not sent to proof).
- An unsupported-version message shows every field as "Unknown tag N" (note F4).

## For the agent

1. Copy the updated hidden files to the host-only folder: `acc-render.test.js` (new, 5 tests, jsdom) and
   `acc-page.test.js` (1 new test). On the landed code 3 of them fail; they have never passed, so that is not a
   regression.
2. Load `fix-lens/tickets/FXL-8.md` (blocked by FXL-7, label `security`) and let it run. The design copy is
   readable only by the implementer profile today; copy it for the planner too, the same way, before the planner
   card starts.
3. When FXL-8 lands, post the comment as usual. I run the browser check from the reviewing session
   (`fix-lens/browser-check/check.mjs` with `sample.log`); Playwright is not in the container.

## Harness backlog (D17)

A web deliverable needs a **real-browser smoke gate**: serve the worktree, load the page under its real CSP, fail
on any console error, foreign request or empty result. It needs Chromium in the container (an install the user
approves). Until then the reviewer runs `browser-check/check.mjs` on every page ticket.

Also for D16: a review finding rated high must not become a note only because its confidence is under the
threshold; send it to the refuter and prover like the others, or block as unproven.
