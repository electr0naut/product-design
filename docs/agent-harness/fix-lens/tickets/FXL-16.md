+++
key = "FXL-16"
title = "The trading summary and the filters on the page"
rank = 16
blocked_by = ["FXL-12", "FXL-13", "FXL-15"]
labels = ["security"]
+++
Show the trading summary and the five filters in `#summary`, following technical design sections 8.2 and 13
(v1.2, "Figures"). The numbers come from `tradeSummary` in `src/summary.js`, and the filtering from `src/filters.js`.
Inside `#summary` the order is: the order banner (when an order is selected), the summary strip, the trading
summary, the filters.

`src/render.js`, `src/main.js` and `test/render.test.js` are expected to change in this ticket.

The expected figures below use log A of FXL-12 and were computed independently of the code.

Acceptance criteria
- AC0: After a decode, `#summary` holds `div.trades` and `div.filters`, after `div.stats`.
- AC1: `div.trades` holds `table.trade-table` with the header cells `Symbol`, `Buy orders`, `Bought`, `Avg buy`,
  `Sell orders`, `Sold`, `Avg sell`, `Net`, and one body row per row of `tradeSummary`, in its order.
- AC2: Figures are written by `format(n)`: `n` rounded to 4 decimal places, without trailing zeros and without a
  thousands separator. `1500` is `1500`, `71.25` is `71.25`, `0.1 + 0.2` is `0.3`, `1234.56789` is `1234.5679`
  and `2 / 3` is `0.6667`. Bought and Sold are `format(filledQty)`. An average is `format(notional / pricedQty)`,
  or `–` (an en dash) when `pricedQty` is zero. Net is `format(buy.filledQty - sell.filledQty)`, with a leading
  `+` when it is above zero.
- AC3: For log A of FXL-12 the body rows read, cell by cell:
  - `AZN.L`, `0`, `10`, `–`, `0`, `0`, `–`, `+10`;
  - `BARC.L`, `0`, `0`, `–`, `1`, `50`, `2.5`, `-50`;
  - `VOD.L`, `1`, `300`, `71.2`, `1`, `260`, `72.2`, `+40`.
- AC4: Under the table, `p.note` reads `Bought and sold are filled quantities from execution reports in this log,
  counted once per ExecID, after trade cancels and corrections.` When `unmatched` is above zero a second
  `p.note.unmatched` follows. For log A it reads `2 trade cancels or corrections refer to an execution that is
  not in this log.` With one it reads `1 trade cancel or correction refers to an execution that is not in this
  log.`
- AC5: With no rows, `div.trades` holds `p.empty` with `No orders or fills in the messages shown.` and no table.
- AC6: `div.filters` holds five `label.filter`, in the order of `FILTERS`, each with a `span` holding the filter's
  label and a `select`. The first option is `All`, then one option per value from `filterOptions`, its text set
  with `textContent`. A filter with no values has `select.disabled` true.
- AC7: Changing a select calls `handlers.setFilter(key, value)` with the chosen value, or `null` for `All`. The
  value is read through `selectedIndex`, never from an option's `value`. When `view.filters` has a value, that
  option is the selected one after `render`.
- AC8: When at least one filter is set, `div.filters` also holds `button.clear-filters` with the text `Clear
  filters`, which calls `handlers.setFilter(null, null)`. With no filter set there is no such button.
- AC9: With a filter set, the timeline, the cards and the trading summary show the filtered log: `render` passes
  the numbers of the shown messages to `tradeSummary(decoded, shown)`, and passes `undefined` when nothing is
  narrowed. For log A with the Account filter on `ACC2`, the only body row is `VOD.L`, `0`, `0`, `–`, `1`, `260`,
  `72.2`, `-260`, and there is no unmatched note.
- AC10: While a filter is set, the summary strip holds `N of M messages`, then the sequence gaps and the orders
  among the messages shown, and no `valid` or `malformed` count; malformed cards are not shown; and with nothing
  to show `#decode` holds `p.empty` with `No messages match the current filters.`
- AC11: A filter and a selected order apply together: the messages shown are the order's messages that pass the
  filters.
- AC12: Filtering changes only what is shown. Message numbers, sequence gaps, order grouping and the effect of
  trade cancels and corrections are those of the full log: with the SenderCompID filter on the client's id, a
  SequenceGap of a client message keeps its detail, and no new gap appears.
- AC13: `src/main.js` keeps the filters in memory only. `setFilter(key, value)` sets one filter and renders again;
  `setFilter(null, null)` clears all five; pressing Decode clears them.
- AC14: The rules of FXL-14 AC10 still hold: option texts, cells and notes are set with `textContent`, and no
  attribute, option `value` or class name comes from pasted text.
