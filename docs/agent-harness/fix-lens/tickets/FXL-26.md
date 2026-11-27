+++
key = "FXL-26"
title = "On the page: an id button opens the order of its message; figures round a half away from zero"
rank = 26
blocked_by = ["FXL-21", "FXL-22"]
labels = ["security"]
+++
Two changes on the page (PRD v1.4 AC-036 and AC-045; technical design v1.4 sections 8.2, 12 and 13).

The order of a button. A value can be the ClOrdID of one order and the OrderID of another, and two clients can
use the same ClOrdID (FXL-22 made those two orders). An id button passed its value alone, so it opened the
first order that held the value, which could be the wrong one. From v1.4 every `button.order-link` calls
`handlers.pick(id, number)`: the id as before, and the number of the message the button is on, which is the
event's message in the timeline and the card's message in a card. `number` is a number, not text. `view` gains
`orderMessage` (a message number or `null`). `render` finds the selected order with `findOrder(groups,
view.orderId, view.orderMessage)` from `src/orders.js` (FXL-22); a view without `orderMessage` is found by its
id, as before. In `src/main.js`, `pick(id, number)` sets `view.orderId` and `view.orderMessage` (and page 1, as
today); `clear` and pressing Decode set both to `null`.

Rounding. The figures of the trading summary are rounded to four decimals with `toFixed(4)`, which rounds the
stored binary value: an average of exactly 1.00255 is stored a hair below and shows as `1.0025`. From v1.4 a
half is rounded away from zero, in decimal: `1.00255` is `1.0026` and `-1.00255` is `-1.0026`. The method of
design section 13: write the absolute value with `toPrecision(15)`; take its digits up to the fourth decimal
place and add one in the last place when the fifth decimal digit is 5 or more; put the sign back. A value that
`toPrecision(15)` writes with an exponent, or with fewer than five decimals, is rounded with `toFixed(4)` as
before. Everything after the rounding is as today: trailing zeros are not shown, a value that rounds to zero is
`0`, the net has a leading `+` when the rounded value is above zero, and an average without a priced quantity
is `–`. Do the arithmetic on the digits (a `BigInt` or a string), not by multiplying the number by 10,000.

`src/render.js`, `src/main.js`, `test/render.test.js` and `test/page.test.js` are expected to change.
`src/orders.js`, `src/summary.js`, `index.html` and `styles.css` do not change. Existing tests that check what
`pick` is called with, or what `view` holds after a click, move to the two arguments and to `orderMessage`;
on the code as landed with FXL-21 these are `test_render_order_identifiers_are_typed_pick_buttons` and
`test_render_optional_order_view_preserves_whole_log` in `test/render.test.js`. No other existing test changes.

The rules of design sections 8.2 and 8.4 still hold: nodes are built with `document.createElement`, text is
set with `textContent`, and no attribute or class name comes from pasted text. The message number is passed in
the click handler's closure; it is never written into the page as an attribute.

The examples use this log (`ALPHA -> BRK` means 49=ALPHA and 56=BRK): (1) `D`, ALPHA -> BRK, 11=500, 55=AAA,
54=1, 38=100; (2) `D`, BETA -> BRK, 11=Q9, 55=BBB, 54=2, 38=50; (3) `8`, BRK -> ALPHA, 37=12, 11=500, 150=0;
(4) `8`, BRK -> BETA, 37=500, 11=Q9, 150=F, 55=BBB, 54=2, 32=50, 31=7. Order A is the messages 1 and 3, order B
the messages 2 and 4, and the value `500` is the ClOrdID of A and the OrderID of B.

Acceptance criteria
- AC0: `render(result, view, handlers)` reads `view.orderMessage`, and every `button.order-link` calls
  `handlers.pick` with two arguments, the id and a message number of type `number`.
- AC1: In the timeline, a button calls `pick` with the number of its event's message; in a card, with the
  number of the card's message. This holds for ClOrdID (11), OrderID (37) and OrigClOrdID (41) buttons. In the
  example, the `500` button in card 4 calls `pick("500", 4)` and the `500` button in card 1 calls
  `pick("500", 1)`.
- AC2: `render` with `view` `{ orderId: "500", orderMessage: 4 }` shows order B (cards `#2` and `#4`); with
  `orderMessage` 1 or 3 it shows order A (cards `#1` and `#3`); with `orderMessage` `null`, or with no
  `orderMessage` in the view, it shows the first order that holds the value, order A.
- AC3: On the page (through `src/main.js`): after Decode of the example, pressing `500` in card 4 shows the
  cards `#2` and `#4` and the banner of order B; `Show all` brings back the four cards; pressing the ClOrdID
  button of message 1 in the timeline then shows `#1` and `#3`. Pressing Decode again shows all four cards and
  no banner.
- AC4: Two clients with the same ClOrdID: for the log of FXL-22 AC1, the `7` button of message 2 opens the
  order of the messages 2 and 4, and the `7` button of message 3 the order of 1, 3, 5 and 6. The trading
  summary and the summary strip follow the opened order, as for any selected order.
- AC5: `view.orderMessage` is set by `pick`, and `clear` and Decode set it to `null`; `pick` still goes back to
  page 1.
- AC6: An average on a half rounds away from zero. Two buy fills of one symbol, 1 at 1.005 and 1 at 1.0001,
  have the average 1.00255 and show `1.0026` (v1.3 shows `1.0025`).
- AC7: Bought, Sold and Net round the same way, on both sides of zero. A buy fill of 7.00015 shows Bought
  `7.0002` and Net `+7.0002`; a sell fill of 3.00025 shows Sold `3.0003` and Net `-3.0003`; a buy fill of
  0.00035 shows `0.0004`. With eight to ten digits before the point the half is still found: a buy fill of
  87654321.00005 shows `87654321.0001`.
- AC8: Values that are not on a half show as before: an average of 4 / 3 is `1.3333`, 2.00004 is `2`, 2.00006
  is `2.0001`, 123456789012.5 is `123456789012.5`, and a quantity of 0.00004 shows `0` with the net `0`, never
  `-0` or `+0`.
