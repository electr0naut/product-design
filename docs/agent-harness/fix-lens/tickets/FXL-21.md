+++
key = "FXL-21"
title = "Paging on the page: the page line and buttons, the timeline and the cards in step"
rank = 21
blocked_by = ["FXL-19", "FXL-20"]
labels = ["security"]
+++
With up to 10,000 messages accepted (FXL-19), drawing every card at once takes many seconds. Show the timeline
and the message cards 200 messages at a time, following technical design section 16 (v1.3, PRD US-010). Which
messages are on a page and the text of the page line come from `pageOf` and `pageLabel` in `src/paging.js`
(FXL-20). Only the drawing changes: `analyse()` and every result stay as they are.

`src/render.js`, `src/main.js`, `styles.css`, `test/render.test.js`, `test/page.test.js` and
`test/styles.test.js` are expected to change in this ticket. `src/paging.js`, `index.html` and the other modules
do not change, and no existing test changes: a log of 200 messages or fewer is drawn exactly as today.

What is paged. The entries are what `#decode` shows today, in log order: with no filter and no order selected,
every decoded message and every malformed message, merged by message number; with a filter set or an order
selected (`narrowed`), the shown decoded messages only. `info = pageOf(entries, view.page)`, with page 1 when
`view` or `view.page` is missing.

What does not follow the page. The order banner, the summary strip, the trading summary and the filter lists
are built from the whole log, or from the whole filtered log, exactly as today; `render` passes the same
`shown` numbers to `tradeSummary` as before. The empty texts are unchanged, and with no entries there is no
pager.

The rules of design sections 8.2 and 8.4 still hold: every node is built with `document.createElement`, text
is set with `textContent`, no attribute or class name comes from pasted text, and the only element properties
set are `textContent`, `className`, `type`, `disabled` and `selectedIndex`. `test/static-checks.test.js` also
checks that every call of the `add` helper in `src/render.js` gives its class as a literal string or `null`, so
write the four button classes as literals. The page line holds only numbers the code computed.

jsdom has no `scrollIntoView`. A test of AC10 puts its own function on the `.results` element before pressing
a page button.

The rule set at the end of this ticket meets AC12 and was checked in a real browser in both themes, at 1280 and
at 375 pixels wide. It may be used as it is.

Acceptance criteria
- AC0: `render(result, view, handlers)` reads `view.page` and `handlers.setPage`. For a log of 201 valid
  messages and no `view`, `#decode` holds 200 `article.card`, numbered `#1` to `#200`, and the page holds two
  `nav.pager`.
- AC1: A page is 200 entries. A log of exactly 200 messages is shown whole, with 200 cards and no `nav.pager`
  anywhere. A log of 201 messages has two pages: with `view.page` 2, `#decode` holds one card, `#201`.
- AC2: With more than one page there are exactly two `nav.pager`: one is the last element inside `#summary`,
  after `div.filters`, and one is the last element inside `#decode`, after the cards. Each holds, in this
  order and nothing else, `span.page-info` and four `button` elements of type `button` with the classes and
  texts `page-first` `First`, `page-prev` `Previous`, `page-next` `Next` and `page-last` `Last`.
- AC3: `span.page-info` holds `pageLabel(info, narrowed)`, the same text in both pagers. For a log of 450 valid
  messages it reads `Messages 1 to 200 of 450` on page 1, `Messages 201 to 400 of 450` on page 2 and `Messages
  401 to 450 of 450` on page 3, where `#decode` holds 50 cards.
- AC4: On page 1, `First` and `Previous` have `disabled` true and `Next` and `Last` have it false. On the last
  page it is the other way round. On a page in between, none of the four is disabled. Both pagers agree.
- AC5: The buttons call `handlers.setPage` with a page number: `First` with `1`, `Previous` with
  `info.page - 1`, `Next` with `info.page + 1` and `Last` with `info.pages`. On page 2 of 3 they call it with
  `1`, `1`, `3` and `3`. The buttons of both pagers do this.
- AC6: A `view.page` that is not a valid page is shown as `pageOf` makes it valid: for 450 messages,
  `view.page` 99 shows page 3 and `view.page` 0 shows page 1.
- AC7: The timeline and the cards show the same page. The timeline holds the events whose message number is
  the number of a decoded message on the page, and no others; a SequenceGap row is on the page of its message: for a log of 450 heartbeats, page 2 has 200
  timeline rows numbered `#201` to `#400` and page 3 has 50, `#401` to `#450`.
- AC8: Malformed messages count, at their place in the log. For a log of 250 messages of which the third is
  malformed and the 249 valid ones are heartbeats whose MsgSeqNum runs from 1 to 249 without a gap (so that
  each has one timeline row), with no filter: page 1 reads `Messages 1 to 200 of 250`, and holds 200 cards of which the third
  is `article.card.malformed`, and 199 timeline rows; page 2 holds 50 cards.
- AC9: While a filter is set or an order is selected, the pages run over the shown decoded messages and the
  line ends with ` shown`. For a log of 450 valid messages of which 250 have SenderCompID `A`, with the
  SenderCompID filter on `A`: page 1 reads `Messages 1 to 200 of 250 shown` and page 2 reads `Messages 201 to
  250 of 250 shown`, with 50 cards. A filter or an order that leaves 200 messages or fewer shows no pager.
- AC10: Nothing else follows the page. On every page of a log, `div.stats`, `div.trades` and the options of
  the five filters are the same as on page 1, and so is `div.order-story` when an order is selected. For the
  450-message log of AC9 with the filter on `A`, the summary strip starts with `250 of 450 messages` on page 1,
  where `#decode` holds 200 cards, and on page 2, where it holds 50.
- AC11: In `src/main.js`, `handlers.setPage(n)` sets `view.page` to `n`, renders, and then calls
  `scrollIntoView()` once on the element with the class `results`. Where that element has no such method,
  nothing is called and nothing is thrown. After a decode of 450 messages, pressing `Next` shows page 2 and
  pressing `Last` shows page 3.
- AC12: `src/main.js` goes back to page 1 whenever what is shown changes: pressing Decode, `setFilter` (a
  filter chosen, changed or cleared), `pick` and `clear` each set `view.page` to 1 before rendering. From page
  2 of a 450-message log, choosing a filter, pressing an order link and pressing Decode again each show page 1.
- AC13: `styles.css` has a rule for `.pager` with `display: flex` and `flex-wrap: wrap`; a rule for `.pager
  button` with `background: var(--panel)` and `color: var(--ink)`, so the page buttons are quiet like
  `.show-all`; and a rule for `.pager button:disabled` with `color: var(--muted)`. The rules of design section
  8.3 still hold: no new custom property, and no hex colour or `rgb(`, `rgba(`, `hsl(` or `hsla(` outside the
  three colour blocks.

Reference rule set (add at the end of `styles.css`):

```css
.pager { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin-top: 1rem; }
.page-info { flex: 1 1 18rem; color: var(--muted); font-size: .875rem; font-variant-numeric: tabular-nums; }
.pager button { padding: .3rem .8rem; border-color: var(--line); background: var(--panel); color: var(--ink); }
.pager button:disabled { color: var(--muted); cursor: default; }
```
