# FIX Lens PRD v1.2: changes from v1.1

**Status: draft for Gate 3, second revision. Not approved.** On approval, these changes are merged into the
Confluence PRD (page 557109) as v1.2. Everything in v1.1 that is not mentioned here stays as it is.

**Source:** Ubay's feedback on the landed v1.1 page and the presentation mock he approved on 2026-11-26
(`docs/agent-harness/fix-lens/mock/`), two defects found by running v1.1 in a real browser, and his decision of
2026-11-26 that cancel and replace requests, trade cancels and corrections, and delimiter characters inside
values are all in scope, because they are part of the protocol.

## Summary of changes

| # | Change | Kind |
|---|---|---|
| 1 | Logs that show the delimiter as `^A` or `<SOH>` are accepted | Fix to TR-002 |
| 2 | A delimiter character inside a field value no longer breaks the message | Fix to TR-002 |
| 3 | A page that was not opened through a web server says so | New AC under US-001 |
| 4 | Cancel and replace requests, trade cancels, trade corrections and order status reports are timeline events | Extension of US-002 and TR-003 |
| 5 | A designed presentation, with a light and a dark theme | New story US-006 |
| 6 | The whole story of one order, from any of its ids | New story US-007 |
| 7 | Buys, sells and net per symbol, after trade cancels and corrections | New story US-008 |
| 8 | Filters by account and by the four comp and sub ids | New story US-009 |

## Scope changes

- **Input** adds: fields may also be separated by the two-character text `^A` or the five-character text
  `<SOH>`, as terminals and log viewers show the SOH byte.
- **Output** adds: a summary of the log, a trading summary per symbol, filters, and a view of a single order.
- **Delivery** adds: the page is served over HTTP or HTTPS. Opening the file from disk is not supported, and
  the page says so (AC-024).
- **Out of scope, added:**
  - Length-prefixed data fields (for example RawData 95/96 and XmlData 212/213) whose content contains a
    delimiter. Pasted text cannot carry binary content reliably. Such a field is read like any other value.
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
  - CancelReject (35=9);
  - TradeCancel, TradeCorrect and OrderStatus, which are ExecutionReports mapped as in TR-003.
- **AC-010 (extended):** order events also show OrigClOrdID (41) when present. TradeCancel and TradeCorrect
  events also show ExecRefID (19).

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
- AC-041: Bought and sold are sums over executions as they stand at the end of the log. An execution is an
  ExecutionReport that is a Fill (TR-003) with LastQty (32) above zero. It is identified by its OrderID (37)
  and ExecID (17), and counted once, so a resent report is not counted twice.
- AC-042: A TradeCancel removes the execution that its ExecRefID (19) names.
- AC-043: A TradeCorrect replaces the quantity and price of the execution that its ExecRefID (19) names with
  its own LastQty (32) and LastPx (31). A later TradeCancel or TradeCorrect may name the original ExecID or the
  ExecID of an earlier correction of the same execution.
- AC-044: When the execution a report names is not in the log, a TradeCorrect counts as an execution with its
  own quantity and price, and a TradeCancel changes nothing. The table's note says how many such reports there
  were.
- AC-045: The average price is the sum of quantity times price over the side's executions, divided by the sum
  of their quantities, shown to at most 4 decimal places. A side with no executions shows a dash.
- AC-046: Net is bought minus sold.
- AC-047: Side 1 (Buy) and 3 (Buy minus) are buys. Side 2 (Sell), 4 (Sell plus), 5 (Sell short) and 6 (Sell
  short exempt) are sells. Messages with any other side, or with no Symbol, are not counted.
- AC-048: A note under the table says: "Bought and sold are filled quantities from execution reports in this
  log, counted once per ExecID, after trade cancels and corrections."
- AC-049: The table follows the filters (US-009) and the selected order (US-007).

### US-009: Filter the Log

**As a** FIX support technician
**I want to** narrow the log to one account or one counterparty
**So that** I can look at one client's or one desk's flow in a shared log

**Acceptance Criteria:**

- AC-050: Five filters are offered: Account (1), SenderCompID (49), SenderSubID (50), TargetCompID (56) and
  TargetSubID (57). Each is a list of the distinct values present in the log, sorted, with "All" first. A
  filter with no values in the log is shown disabled.
- AC-051: The Account filter keeps every message of every order (AC-035) that has at least one message with
  that Account. The other four keep the messages whose own field has the chosen value.
- AC-052: Filters combine: a message is shown only if it passes every filter that is set.
- AC-053: The timeline, the message cards and the trading summary all show the filtered log. While a filter is
  set or an order is selected, the summary strip shows "N of M messages" and the sequence gaps and orders among
  the messages shown, and leaves out the valid and malformed counts.
- AC-054: While a filter is set or an order is selected, malformed messages are not shown.
- AC-055: A "Clear filters" button resets all five. Decoding again also resets them.
- AC-056: Filtering never changes a result. Sequence gaps, message numbers, order grouping and the effect of
  trade cancels and corrections are computed on the full log (AC-038).

## Changes to technical requirements

### TR-002: Message Parsing and Framing

- **Delimiters (replaces the first bullet):** fields are separated by SOH (0x01), `|`, the text `^A` or the
  text `<SOH>`. The delimiter is chosen per message: it is whichever of the four follows the BeginString value
  of that message. Only that delimiter separates fields in that message.
- **A delimiter inside a value (new):** when the delimiter is one of the three text forms, an occurrence of it
  separates fields only if a tag and `=` follow it (one or more digits, then `=`), or if it ends the CheckSum
  field. Any other occurrence is part of the value of the field it is in. With the SOH byte itself, every
  occurrence separates fields, as the protocol requires.
- **Byte counts (replaces "treated as SOH"):** in length and checksum calculations, each occurrence that
  separates fields counts as the single byte 0x01. An occurrence that is part of a value counts as its own
  bytes.
- **The one case that text cannot settle:** a value that contains the delimiter followed by digits and `=` reads
  as a new field. BodyLength still matches and CheckSum does not, so the message is reported with a CheckSum
  error.
- **Positions:** character positions in error messages (AC-012) are positions in the pasted text, whatever the
  delimiter.

### TR-003: Session Behaviour Detection

- **ExecutionReport mapping (extended).** These are checked before the v1.1 mapping by ExecType:
  - **FIX 4.2**, by ExecTransType (20): `1` is TradeCancel, `2` is TradeCorrect, `3` is OrderStatus. `0`, or
    no tag 20, falls through to the ExecType mapping.
  - **FIX 4.4**, by ExecType (150): `H` is TradeCancel, `G` is TradeCorrect, `I` is OrderStatus.
- **Consequence:** a FIX 4.2 report with ExecType `1` or `2` is a Fill only when its ExecTransType is `0` or
  absent.

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
| 9 | `^A` and `<SOH>` delimiters, and a delimiter inside a value (TR-002) | |
| 10 | CancelRequest, ReplaceRequest, CancelReject, TradeCancel, TradeCorrect and OrderStatus events (AC-009, AC-010, TR-003) | |
| 11 | Order grouping module (AC-035) | |
| 12 | Trading summary module, with trade cancels and corrections (AC-039 to AC-048) | 10 |
| 13 | Filter module (AC-050 to AC-052, AC-056) | 11 |
| 14 | The presentation: layout, cards, timeline rows, summary strip, themes, the not-started message (US-006, AC-024) | 9, 10 |
| 15 | The order story on the page (US-007) | 11, 14 |
| 16 | The trading summary and the filters on the page (AC-049, AC-053 to AC-055) | 12, 13, 15 |

Ticket 8 was the v1.1 browser fix (dictionaries as JavaScript modules).

## Risks (added)

### Risk 4: The trading summary is read as a position report

- **Risk:** a technician treats the net figure as the client's position.
- **Mitigation:** the note of AC-048 under the table. The figures cover the executions in this log only, and a
  log that starts mid-session is missing earlier ones (AC-044 reports the cancels and corrections that point
  outside the log).

### Risk 5: Hidden tests tied to the old page structure

- **Risk:** the v1.1 acceptance tests describe the v1.1 page, so the presentation ticket would be reported as a
  regression.
- **Mitigation:** the harness gains a way to retire named hidden tests on purpose (harness change D19) before
  ticket 14 is loaded.
