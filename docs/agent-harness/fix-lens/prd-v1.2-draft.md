# FIX Lens PRD v1.2: changes from v1.1

**Status: draft for Gate 3. Not approved.** On approval, these changes are merged into the Confluence PRD
(page 557109) as v1.2. Everything in v1.1 that is not mentioned here stays as it is.

**Source:** Ubay's feedback on the landed v1.1 page and the presentation mock he approved on 2026-11-26
(`docs/agent-harness/fix-lens/mock/`), plus two defects found by running v1.1 in a real browser.

## Summary of changes

| # | Change | Kind |
|---|---|---|
| 1 | Logs that show the delimiter as `^A` or `<SOH>` are accepted | Fix to TR-002 |
| 2 | A page that was not opened through a web server says so | New AC under US-001 |
| 3 | A designed presentation, with a light and a dark theme | New story US-006 |
| 4 | The whole story of one order, from any of its ids | New story US-007 |
| 5 | Buys, sells and net per symbol | New story US-008 |
| 6 | Filters by account and by the four comp and sub ids | New story US-009 |

## Scope changes

- **Input** adds: fields may also be separated by the two-character text `^A` or the five-character text
  `<SOH>`, as terminals and log viewers show the SOH byte.
- **Output** adds: a summary of the log, a trading summary per symbol, filters, and a view of a single order.
- **Delivery** adds: the page is served over HTTP or HTTPS. Opening the file from disk is not supported, and
  the page says so (AC-024).
- **Out of scope, added:**
  - Applying trade cancels and trade corrections to the trading summary. Fills are counted as reported.
  - A `|` inside a field value in a log that uses `|` as its delimiter. Such a message is reported as malformed.
  - Remembering the theme, the filters or the selected order between visits (US-005 forbids storage).

## Changes to existing stories

### US-001: Paste and Decode FIX Log

- **AC-024 (new):** if the page's script has not run, the page shows a visible message in place of the tool:
  "FIX Lens did not start. Open it through a web server, not as a file from disk." The message is part of the
  static HTML and is removed by the script when it starts.

### US-002: Session Behaviour Timeline

- **AC-009 (extended):** the order lifecycle events also include:
  - CancelRequest (35=F);
  - ReplaceRequest (35=G);
  - CancelReject (35=9).

  *This is not in the mock. It is here because an order's story is incomplete without the requests that
  changed it. Strike it at Gate 3 if you don't want it.*
- **AC-010 (extended):** order events also show OrigClOrdID (41) when present.

## New stories

### US-006: A Clear, Themed Presentation

**As a** FIX support technician
**I want** the page laid out and styled so that the session, the orders and the errors stand out
**So that** I can read a log quickly, in a light or a dark room

**Acceptance Criteria:**

- AC-025: The page has a header with the product name and the line "Runs entirely in this page. Nothing you
  paste is sent, stored or logged."
- AC-026: After a decode, a summary strip shows five counts for the log: messages, valid, malformed, sequence
  gaps, orders.
- AC-027: On a window 900 px wide or more, the timeline and the decoded messages are side by side, and the
  timeline stays in view while the messages scroll. Under 900 px they are one column.
- AC-028: Each decoded message is a card with a header (message number, MsgType name, sender to target,
  MsgSeqNum, SendingTime) and a table of its fields with four columns: tag, field, value, meaning.
- AC-029: A malformed message appears as an error card at its place in log order, with the text AC-012
  requires.
- AC-030: Each timeline row shows the message number, the time, the event name as a badge, the direction, the
  sequence number and the order ids. Order events, sequence gaps and rejects are each marked differently, and
  never by colour alone: the badge text always names the event.
- AC-031: The page has a light and a dark theme. On load it follows the system setting
  (`prefers-color-scheme`). A button switches the theme. The choice is not stored, so a reload returns to the
  system setting.
- AC-032: In both themes, text meets WCAG 2.1 AA contrast (4.5 to 1) against its background.
- AC-033: The presentation keeps the v1.1 security rules (TR-006), and adds: no inline script or style, and no
  HTML attribute is ever set from pasted text.

### US-007: The Story of One Order

**As a** FIX support technician
**I want to** click any order id and see everything that happened to that order
**So that** I can follow one order through acknowledgement, fills, replaces and cancels without reading the
whole log

**Acceptance Criteria:**

- AC-034: Every ClOrdID (11), OrigClOrdID (41) and OrderID (37) value shown in the timeline or in a message
  card is a button.
- AC-035: Messages belong to the same order when they share a ClOrdID (11) or an OrderID (37), or are linked by
  an OrigClOrdID (41) that equals another message's ClOrdID, directly or through other messages. A
  cancel/replace chain is therefore one order.
- AC-036: Activating an id shows only that order's messages and timeline events, under a banner with:
  - every ClOrdID and OrderID of the order;
  - its terms, from its first message: side, quantity, symbol, price when present, order type;
  - its latest state, from its last ExecutionReport: OrdStatus (39) and, when CumQty (14) is above zero, the
    filled quantity and AvgPx (6).
- AC-037: The banner has a "Show all messages" button that returns to the full log. Decoding again also
  returns to the full log.
- AC-038: Message numbers, sequence gaps and every other result are those of the full log. Selecting an order
  only changes what is shown.

### US-008: Buys, Sells and Net per Symbol

**As a** FIX support technician
**I want** a table of what was bought and sold in the log, per symbol
**So that** I can check a client's activity against what they expect, at a glance

**Acceptance Criteria:**

- AC-039: After a decode, a table has one row per Symbol (55), sorted by symbol, with: buy orders, bought,
  average buy price, sell orders, sold, average sell price, net.
- AC-040: Buy orders and sell orders count NewOrderSingle messages (35=D) by Side (54).
- AC-041: Bought and sold are the sum of LastQty (32) over ExecutionReports (35=8) whose LastQty is above zero.
  A report is counted once per OrderID (37) and ExecID (17) pair, so a resent report is not counted twice.
- AC-042: The average price is the sum of LastQty times LastPx (31) divided by the sum of LastQty, shown to at
  most 4 decimal places. A side with no fills shows a dash.
- AC-043: Net is bought minus sold.
- AC-044: Side 1 (Buy) and 3 (Buy minus) are buys. Side 2 (Sell), 4 (Sell plus), 5 (Sell short) and 6 (Sell
  short exempt) are sells. Messages with any other side, or with no Symbol, are not counted.
- AC-045: A note under the table says: "Bought and sold are filled quantities from execution reports in this
  log, counted once per ExecID. Trade cancels and corrections are not applied."
- AC-046: The table follows the filters (US-009) and the selected order (US-007).

### US-009: Filter the Log

**As a** FIX support technician
**I want to** narrow the log to one account or one counterparty
**So that** I can look at one client's or one desk's flow in a shared log

**Acceptance Criteria:**

- AC-047: Five filters are offered: Account (1), SenderCompID (49), SenderSubID (50), TargetCompID (56) and
  TargetSubID (57). Each is a list of the distinct values present in the log, sorted, with "All" first. A
  filter with no values in the log is shown disabled.
- AC-048: The Account filter keeps every message of every order (AC-035) that has at least one message with
  that Account. The other four keep the messages whose own field has the chosen value.
- AC-049: Filters combine: a message is shown only if it passes every filter that is set.
- AC-050: The timeline, the message cards and the trading summary all show the filtered log. While a filter is
  set or an order is selected, the summary strip shows "N of M messages" and the sequence gaps and orders among
  the messages shown, and leaves out the valid and malformed counts.
- AC-051: While a filter is set or an order is selected, malformed messages are not shown.
- AC-052: A "Clear filters" button resets all five. Decoding again also resets them.
- AC-053: Filtering never changes a result. Sequence gaps, message numbers and order grouping are computed on
  the full log (AC-038).

## Changes to technical requirements

### TR-002: Message Parsing and Framing

- **Delimiters (replaces the first bullet):** fields are separated by SOH (0x01), `|`, the text `^A` or the
  text `<SOH>`. The delimiter is chosen per message: it is whichever of the four follows the BeginString value
  of that message. Only that delimiter separates fields in that message. Before any length or checksum
  calculation, each delimiter occurrence counts as the single byte 0x01.
- **Positions:** character positions in error messages (AC-012) are positions in the pasted text, whatever the
  delimiter.

### TR-004: User Interface

- **Layout (replaces the bullet):** as US-006 describes.
- **Code structure (extended):** order grouping, the trading summary and the filters are plain JavaScript
  modules with no DOM access, like the parsing, decoding and timeline logic.

### TR-005: Performance

- **Added:** for a 1,000-message log, order grouping, the trading summary and applying the filters each take
  under 1 second, measured on the logic modules.

### TR-006: Security

- **Added:** AC-033. The automated checks of AC-023 also fail the build on an inline `<script>` or `style`
  attribute in the page, and on `setAttribute` with a value that comes from pasted text.

## Delivery plan (added tickets)

| # | Ticket | Depends on |
|---|---|---|
| 9 | `^A` and `<SOH>` delimiters (TR-002) | |
| 10 | CancelRequest, ReplaceRequest and CancelReject timeline events (AC-009, AC-010) | |
| 11 | Order grouping module (AC-035) | |
| 12 | Trading summary module (AC-039 to AC-045) | |
| 13 | Filter module (AC-047 to AC-049, AC-053) | 11 |
| 14 | The presentation: layout, cards, timeline rows, summary strip, themes, the not-started message (US-006, AC-024) | 9, 10 |
| 15 | The order story on the page (US-007) | 11, 14 |
| 16 | The trading summary and the filters on the page (AC-046, AC-050 to AC-052) | 12, 13, 15 |

Ticket 8 was the v1.1 browser fix (dictionaries as JavaScript modules).

## Risks (added)

### Risk 4: The trading summary is read as a position report

- **Risk:** a technician treats the net figure as the client's position.
- **Mitigation:** the note of AC-045 under the table; the figures cover this log only and ignore trade cancels
  and corrections.

### Risk 5: Hidden tests tied to the old page structure

- **Risk:** the v1.1 acceptance tests describe the v1.1 page, so the presentation ticket would be reported as a
  regression.
- **Mitigation:** the harness gains a way to retire named hidden tests on purpose (harness change D19) before
  ticket 14 is loaded.
