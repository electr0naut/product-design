+++
key = "FXL-15"
title = "The story of one order: click an order id to see only that order"
rank = 15
blocked_by = ["FXL-11", "FXL-14"]
labels = ["security"]
+++
Make every order id on the page a button that shows that order alone, following technical design section 8.2
(v1.2): the `view` and `handlers` arguments of `render`, the order banner, and the narrowed summary strip. Orders
come from `orderGroups` and `findOrder` in `src/orders.js`, always computed on the whole log. The trading summary
and the filters are FXL-16.

`src/render.js`, `src/main.js` and `test/render.test.js` are expected to change in this ticket.

Acceptance criteria
- AC0: `render(result, view, handlers)` takes `view` `{ orderId, filters }` and `handlers`
  `{ pick(id), clear(), setFilter(key, value) }`. `render(result)` alone still works and shows the whole log.
- AC1: In the timeline, each ClOrdID, OrderID and OrigClOrdID is a `button.order-link` with `type` `button` and
  the text `ClOrdID <11>`, `OrderID <37>` or `OrigClOrdID <41>`. In a message card, the value cell of tag 11, 37
  or 41 holds a `button.order-link` whose text is the value alone. Clicking any of them calls
  `handlers.pick(id)` with the id alone. They are buttons, never links.
- AC2: An OrderID of `NONE` is plain text, not a button, in the timeline and in the cards. An empty value is not
  a button.
- AC3: With `view.orderId` set, `#timeline` shows only the events, and `#decode` only the cards, of the messages
  in that order's group. Message numbers are those of the full log.
- AC4: With `view.orderId` set, `#summary` starts with `div.order-story`, which holds:
  - a `strong` with the group's ClOrdIDs then its OrderIDs, joined by ` · `;
  - `span.order-terms`: from the group's first NewOrder (35=D), or its first message when it has none: the
    meaning of 54, the value of 38, the value of 55, `@ <44>` when 44 is present, and the meaning of 40, joined
    by spaces;
  - `span.order-state`: from the group's last ExecutionReport (35=8): the meaning of 39, then, when 14 is a number
    above zero, ` · <14> filled @ <6>`. With no ExecutionReport there is no `span.order-state`;
  - `button.show-all` with the text `Show all messages`, which calls `handlers.clear()`.

  "The meaning of" a tag is the field's `enumName`, or its value when it has none or the name is
  `unknown value`.
- AC5: For this FIX.4.4 log: NewOrder 11=C1, 54=1, 38=500, 55=VOD.L, 44=71.25, 40=2; ExecutionReport 11=C1,
  37=O1, 150=0, 39=0, 14=0, 6=0; ExecutionReport 11=C1, 37=O1, 150=F, 39=2, 14=500, 6=71.25, 32=500, 31=71.25;
  with `view.orderId` `O1` the banner shows `C1 · O1`, the terms `Buy 500 VOD.L @ 71.25 Limit` and the state
  `Filled · 500 filled @ 71.25`.
- AC6: While an order is selected, the summary strip holds `N of M messages`, then the sequence gaps and the
  orders among the messages shown, and no `valid` or `malformed` count. Malformed cards are not shown.
- AC7: Selecting an order changes only what is shown: a SequenceGap event of a message in the order is shown
  with the same detail as in the full log, and selecting an order never creates a gap.
- AC8: `src/main.js` keeps the view in memory only. `pick` sets `view.orderId` and renders again; `clear` sets it
  to `null` and renders again; pressing Decode clears it.
- AC9: A `view.orderId` that matches no order shows the whole log, without a banner.
- AC10: The rules of FXL-14 AC10 still hold: ids and banner text are set with `textContent`, and no attribute or
  class name comes from pasted text.
