# FIX Lens - Technical Design: proposed clarifications to v1.2

**Status: proposed, for Ubay's approval.** Until approved, `technical-design.md` (v1.2) stands as it is. Nothing
here changes the PRD.

**Where these come from.** A second agent built v1.2 from the design alone and listed every place where the
design was silent, ambiguous or different from the code already built. The reviewer's hidden tests were then run
against that build. The items below are the ones that decide visible behaviour. The tickets FXL-9 to FXL-16
already state each of them; this brings the design into line, so that the spec review and the tickets say the
same thing.

## Corrections: the design described something other than what is built and correct

1. **Section 2, Message.** A message is `{ number, start, end, fields }`. It has no `beginString` or `msgType`
   property; the version and the type are the first values of tags 8 and 35 in `fields`. A ParseError's
   `position` is 1-based; `start`, `end` and a field's `position` are 0-based.
2. **Section 5, dictionary modules.** Each module's object is `{ "fields": { "<tag>": { "name", "type",
   "enumValues": { "<value>": "<symbolicName>" } } }, "commit": "<pinned commit>" }`. `enumValues` is present
   only for fields with a code set.
3. **Section 7, step 1.** A Logon with 141=Y resets the expected number to 1 only when 43 isn't `Y` (PRD TR-003:
   a PossDup message never advances or resets).
4. **Section 2, TimelineEvent.** `origClOrdId` is tag 41 on order events only. `execRefId` is tag 19 on
   TradeCancel and TradeCorrect events only. Both are `null` everywhere else.

## Additions: the design was silent

5. **Section 8.1, the not-started message (PRD AC-024, "in place of the tool").** The textarea, the Decode button,
   `#summary` and `.results` are inside `<main hidden>`, and `#not-started` is outside it. `main.js` removes the
   message and then sets `hidden = false` on `<main>`. `#timeline` and `#decode` each start with an `h2`
   (`Timeline`, `Decode`) that `render` keeps.
6. **Section 8.2, the size warning.** Over a limit, `#summary` and `#timeline` are empty apart from the heading,
   and `#decode` shows one `p.warning` with the warning text.
7. **Section 8.2, the order banner.** A part whose tag is missing is left out, with no stray separator. The fill
   part is `<14> filled @ <6>`, or `<14> filled` when 6 is missing. A span that would be empty
   (`span.order-terms`, `span.order-state`) is not created. Terms and state come from the whole order, whatever
   the filters are.
8. **Section 8.2, the narrowed summary strip.** In `N of M messages`, M counts valid and malformed messages. "The
   orders among the messages shown" are the orders of the full log that have at least one message shown.
9. **Section 13, step 1.**
   - An empty value counts as a missing tag for Symbol 55, ExecID 17 and ExecRefID 19.
   - A Fill that makes no execution (no Symbol, another side) is not remembered, so a later TradeCancel that
     names it is unmatched.
   - A TradeCorrect that names an execution in the log, but whose own LastQty is not a finite number above zero,
     changes nothing and is not unmatched.
   - An unmatched TradeCancel or TradeCorrect is remembered by its OrderID and ExecID, so a resend of it is not
     counted again.
   - Messages of an unsupported version count for nothing in the summary, their NewOrderSingles included.
10. **Section 13, Figures.** The sign of Net comes from the rounded value. A value that rounds to zero is written
    `0`, never `-0` or `+0`.
11. **Section 8.3, colours.** Each of the sixteen properties is a six-digit hex colour, and outside the three
    blocks the stylesheet has no hex colour and no `rgb(`, `rgba(`, `hsl(` or `hsla(`.

## Left as they are

The second agent listed other points where the v1.2 text repeats v1.1 wording that the built code already
settles (which field a `header_order` error points at, the wording of the other error texts, what `end`
includes). The tickets say that shapes, positions and error texts do not change, so these need no new text.
