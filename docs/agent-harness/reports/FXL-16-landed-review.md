# FXL-16 landed: review (trusted main `d520fe7`)

**Clean in behaviour. No fix needed. The table and the filters are unstyled, as expected; FXL-18 follows.**
With FXL-16, every ticket of v1.2 has landed and the hidden suite is at 173 of 173.

## What I checked, and how
- **Rebuilt here** from the FXL-15 tree plus the published patch. Hidden suite: `173 passed (173)`. The
  project's own tests: `253 passed`, and the same 4 dictionary tests fail here as always, for want of the
  vendored XML in my scratch copy.
- **Against my independent reference build:** 48,000 renders of 8,000 random logs (malformed messages in half
  of them), with random filters, a random selected order, or both. Compared: the order inside `#summary`, the
  strip, every table cell, the notes, each filter's options, chosen option and disabled state, the clear
  button, and the number of events and cards; and the order banner's text on a second pass over 3,000 of those
  logs (18,000 renders). **No difference in behaviour.** Three wording
  differences, all on points the design leaves open, and the landed reading is the literal one each time:
  - with no rows, the landed page shows only `No orders or fills in the messages shown.`; my reference also
    showed the note about filled quantities;
  - `1 of 1 messages` (the design gives the form `N of M messages`); my reference wrote `1 of 1 message`;
  - the text of the empty timeline, which the design does not give.
- **In a real browser, both themes** (`fix-lens/browser-check/check16.mjs`, no problems reported): the figures
  of log A cell by cell; Account `ACC2` gives the one row of AC9 and `4 of 19 messages`; two filters together;
  a filter and a selected order together; an order outside the filter gives both empty texts; Clear filters
  keeps the selected order; Decode clears filters and order. An Account of `<img/src=x/onerror=alert(1)>` is
  shown as an option's text and works as a filter; no element is made from it, no option has a `value`
  attribute, nothing is stored, no request leaves the page.
- `render` does not change the result it is given (checked on every render of both passes).

## The automated review
- **Five findings, one marked critical, none proven, all filed as notes. I checked each: all five are wrong.**
  F2 and F3 say malformed cards are still shown while a filter is set; the code sets `errors = []` whenever the
  view is narrowed, and the browser check confirms it. F1, F4 and F5 describe what the design asks for.
  The gate did the right thing with them. The review cost **$2.45** of Claude for it, the highest of the batch.
- **The implementer ran on a fallback model** (`deepseek-v4.1-flash-1017`), with no `gpt-6.2-sol` session at
  all. Every other v1.2 ticket ran on `gpt-6.2-sol`. The evidence does not say why. The result is correct, but
  I want the cause before the next ticket: see "For the agent".

## Mutation: 9 survivors, 19 static not measured
- **8 change nothing a user can see:** line 87 (three: the chosen index is 0 either way), lines 89 and 94
  (four: they differ only when no handlers are passed), `main.js` line 38 (a `null` entry is read the same as
  a missing one).
- **1 is a real gap in the project's own tests:** `render.js` line 255, where the order banner would be built
  from the whole log instead of the selected order. With that change made by hand, the project's own tests
  still pass (253), and **the hidden suite fails 4 tests** of `acc-order-story.test.js`. So the hidden suite
  holds the line, and the project's tests have only single-order logs for the banner. This is one more case for
  the "kill or justify" proposal: the mutation result named a real gap and nothing acted on it.

## What is left for v1.2
1. **FXL-18, styling:** the order banner, the order links, the trading table, the filters and the clear
   button have no rules in `styles.css` (my tickets FXL-15 and FXL-16 did not list the file). I write it now.
2. Ubay's own test with real logs.

## For the agent (read-only)
- Why did FXL-16's implementer card run on the first fallback? Give the log lines: the error or limit the
  primary returned, and when. And the current state of the Codex plan's window, as far as the logs show it.
