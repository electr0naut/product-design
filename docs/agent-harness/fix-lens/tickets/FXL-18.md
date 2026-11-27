+++
key = "FXL-18"
title = "Style the order banner, the order links, the trading summary and the filters"
rank = 18
blocked_by = ["FXL-16"]
labels = []
+++
The order banner, the order links, the trading summary and the filters were added to the page without rules in
`styles.css`: an order id looks like the Decode button, the trading table has no alignment or borders, and the
filters are a bare stack. Add the rules. The markup is that of technical design section 8.2 and does not change.

`styles.css` and a new test file `test/styles.test.js` are expected to change in this ticket. Nothing in `src/`
or `index.html` changes, no existing test changes, and no existing rule changes except the one named in AC6.

The rules of design section 8.3 still hold and the existing tests check them: every colour is one of the sixteen
custom properties, no new property is added, and outside the three colour blocks there is no hex colour and no
`rgb(`, `rgba(`, `hsl(` or `hsla(`. Font sizes of the new rules are not below `.8rem`.

The tests of this ticket read `styles.css` as text, as the existing colour tests do. A helper that finds the
rule (or rules) whose selector list names a given selector, and returns its declarations, is enough.

The rule set at the end of this ticket meets every criterion and was checked in a real browser in both themes,
at 1280 and at 375 pixels wide, with ids and symbols of 60 characters. It may be used as it is.

Acceptance criteria
- AC0: `styles.css` has at least one rule whose selector list names each of `.order-story`, `.order-link`,
  `.show-all`, `.clear-filters`, `.trades`, `.trade-table`, `.note`, `.filters` and `.filter`.
- AC1: `.order-story` and `.filters` are rows that wrap: both get `display: flex` and `flex-wrap: wrap`.
  `.order-story` has `background: var(--order-bg)` and a border colour of `var(--order)`.
- AC2: An order link does not look like the Decode button: `.order-link` has `background: none`, `border: 0`,
  a `border-bottom` that uses `var(--accent)`, and `color: var(--accent)`.
- AC3: `.show-all` and `.clear-filters` are quiet buttons: `background: var(--panel)` and `color: var(--ink)`.
- AC4: `.trades` has `overflow-x: auto`, so a wide table scrolls inside its box and the page does not.
  `.trade-table` has `border-collapse: collapse`. Its header and body cells have `text-align: right`, and the
  first cell of each row has `text-align: left`.
- AC5: `.filter select` has `max-width: 100%`, and `.filter` has `min-width: 0`, so a long value cannot make the
  page wider than the screen.
- AC6: `N valid` is green only in the full strip. The selector `.stat:nth-child(2)` on its own no longer
  appears; the rule that sets `color: var(--ok)` has the selector `.stat:nth-child(2):nth-last-child(4)`. (While
  a filter or an order is chosen the second item is the sequence gaps, which must not be green.)

Reference rule set (replace the `.stat:nth-child(2)` rule with the first line, add the rest at the end):

```css
.stat:nth-child(2):nth-last-child(4) { color: var(--ok); }

.order-story, .trades, .filters {
  margin-top: 1rem;
  padding: .75rem 1rem;
  border: 1px solid var(--line);
  border-radius: .65rem;
  background: var(--panel);
}
.order-story, .filters { display: flex; flex-wrap: wrap; gap: .5rem 1rem; }
.order-story {
  align-items: baseline;
  border-color: var(--order);
  background: var(--order-bg);
  overflow-wrap: anywhere;
}
.order-story strong, .order-link, .trade-table td, .filter select { font-family: ui-monospace, monospace; }
.order-state { font-weight: 650; }
.show-all, .clear-filters {
  margin-left: auto;
  padding: .3rem .8rem;
  border-color: var(--line);
  background: var(--panel);
  color: var(--ink);
}
.order-link {
  padding: 0 .15rem;
  border: 0;
  border-bottom: 1px dashed var(--accent);
  border-radius: 0;
  background: none;
  color: var(--accent);
  font-size: inherit;
  text-align: left;
  overflow-wrap: anywhere;
}
.order-link:hover { background: var(--order-bg); color: var(--order); }

.trades { overflow-x: auto; }
.trade-table { width: 100%; border-collapse: collapse; font-size: .875rem; font-variant-numeric: tabular-nums; }
.trade-table th, .trade-table td { padding: .35rem .6rem; text-align: right; white-space: nowrap; }
.trade-table th { border-bottom: 1px solid var(--line); color: var(--muted); font-size: .8rem; }
.trade-table td { border-top: 1px solid var(--soft); }
.trade-table th:first-child, .trade-table td:first-child { min-width: 8rem; text-align: left; white-space: normal; overflow-wrap: anywhere; }
.trade-table td:first-child, .trade-table td:last-child { font-weight: 650; }
.note { margin-top: .5rem; color: var(--muted); font-size: .8rem; }
.note.unmatched { color: var(--warn); background: var(--warn-bg); padding: .3rem .6rem; border-radius: .35rem; font-weight: 600; }
.trades .empty { padding: 0; border: 0; }

.filters { align-items: end; }
.filter { display: grid; gap: .2rem; min-width: 0; color: var(--muted); font-size: .8rem; }
.filter select {
  min-width: 9.5rem;
  max-width: 100%;
  padding: .3rem .4rem;
  border: 1px solid var(--line);
  border-radius: .35rem;
  background: var(--bg);
  color: var(--ink);
  font-size: .85rem;
}
.filter select:disabled { border-style: dashed; color: var(--muted); }
```
