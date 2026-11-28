# FXL-15 landed: clean in behaviour; its new parts are unstyled, which is a gap in my tickets

Trusted `main` `8cce6aa`, evidence `fix-lens/runs/FXL-15.md`. Rebuilt here from the published patch. No fix pass,
no block. It is the first ticket judged by D24: `acc-order-story.test.js` 12 of 12, met.

| check | result |
|---|---|
| hidden suite, the runner's isolated run and mine | **159 of 173**, no regression; `acc-order-story` 12 of 12 |
| the project's own tests | 235 pass (the same 4 dictionary tests fail here for want of the vendored XML) |
| real browser (`browser-check/check15.mjs`, `session.log`) | every ClOrdID, OrderID and OrigClOrdID is a button, `37=NONE` is not; clicking `ClOrdID C1` shows that order alone: 7 of 12 messages, 8 timeline rows with its sequence gap, 1 order, and the banner `C1 · C2 · C3 · O1`, `Buy 1000 VOD.L @ 71.5 Limit`, `PartiallyFilled`; `Show all messages` restores the 12; a second order selects alone; Decode again clears the selection; no console error, no `<img>`, no foreign request |
| reviewer | three notes, none proven. F3 is true and accepted: `Array.prototype.findLast` needs a browser from 2022 or later |
| mutation | 153 killed, 7 survived, 2 static (not measured) |

**FXL-15 counts as landed clean.**

## What the screenshot shows (`browser-check/fxl15-landed-order-story.png`)
The banner's parts run together (`O1Buy`, `LimitPartiallyFilled`) and the button sits against the text. Every
order id is a large filled button, the same as Decode. Nothing is wrong in the markup: **there are no style
rules for `.order-story`, `.order-link` and `.show-all`,** so they take the generic ones.

**The cause is in my tickets.** FXL-15 and FXL-16 list `src/render.js`, `src/main.js` and
`test/render.test.js` as the files to change, and not `styles.css`. The mock Ubay approved on 2026-11-26 has
rules for the order links, the banner, the trading summary and the filters; FXL-14 styled only its own parts.
The tests run in jsdom, which lays nothing out, so no test can see it. FXL-16 will land the trading table and
the filters the same way.

## What follows
A styling ticket, FXL-18, after FXL-16 lands: the rules of the approved mock for those four parts, in the
custom properties of design section 8.3, with tests that read `styles.css` as the contrast test does. I write
it against the markup FXL-16 really produces, check it in a real browser in both themes first, and load it
under Ubay's standing word for v1.2 (`V12-go-review6.md`). I tell him before it is loaded.
