# Product Requirements Document: FIX Lens

**Product:** FIX Lens
**Version:** 1.2 (Proof of Concept)
**Status:** Approved (Gate 3, 2026-11-26)
**BRD Status:** Approved by Risk Committee (2026-11-24)

> **Changes in v1.2:** logs that show the delimiter as `^A` or `<SOH>` are accepted, and a delimiter character inside a value no longer breaks the message. A page that was not opened through a web server says so. Cancel and replace requests, trade cancels, trade corrections and order status reports become timeline events, and a FIX 4.2 trade cancel or correction is no longer shown as a fill. Four stories are new: a designed presentation with light and dark themes (US-006), the story of one order (US-007), buys, sells and net per symbol (US-008), and filters (US-009). Tickets 9 to 16 are added to the delivery plan.
>
> **Changes in v1.1:** every story was pinned to the FIX 4.2/4.4 specification, so that each acceptance criterion can be tested and each story can become a delivery ticket.

## Product Overview

FIX Lens is a static web application that lets FIX support and client onboarding technicians paste raw FIX protocol logs and get a human-readable, field-by-field decode, with an explanation of session-level behaviour.

### Scope (Proof of Concept)

- **FIX versions:** 4.2 and 4.4, selected by BeginString (tag 8). Any other BeginString is reported as an unsupported version for that message.
- **Message structure:** top-level fields only. Repeated tags (for example, repeating-group members) are listed in order of appearance, without grouping, and are not errors.
- **Input:** raw FIX logs pasted into a textarea. Fields may be separated by SOH, by `|`, or by the text `^A` or `<SOH>`, as terminals and log viewers show the SOH byte.
- **Output:** a field-by-field decode, a session behaviour timeline, a summary of the log, a trading summary per symbol, filters, and a view of a single order, all viewable in the browser.
- **Max log size:** 1,048,576 bytes (UTF-8) or 1,000 messages.
- **Error handling:** malformed messages are rejected gracefully, with clear error messages.
- **Data handling:** in-memory processing only. No retention, no logging, no caching.
- **Delivery:** static web app (HTML/JS, no backend), served over HTTP or HTTPS. Opening the file from disk is not supported, and the page says so (AC-024).

### Out of Scope (Proof of Concept)

- FIX 5.0 support.
- Grouping repeating groups and nested structures (their fields are still shown, flat).
- Export functionality (PDF, CSV).
- Field-level validation against the FIX specification: required fields per message type, field formats and value ranges. Framing checks (TR-002) are in scope.
- Network connectivity or FIX engine functionality.
- Data persistence or storage, including remembering the theme, the filters or the selected order between visits.
- Length-prefixed data fields (for example RawData 95/96 and XmlData 212/213) whose content contains a delimiter. Pasted text cannot carry binary content reliably. Such a field is read like any other value.

## User Stories

### US-001: Paste and Decode FIX Log

**As a** FIX support technician
**I want to** paste a raw FIX log into a textarea and see every message decoded field by field
**So that** I can understand what each tag, field name, and value means without manual lookup

**Acceptance Criteria:**

- AC-001: The user can paste raw FIX log text into a textarea.
- AC-002: The user can click a "Decode" button to process the log.
- AC-003: Each message is displayed with its tag/value pairs decoded, in the order they appear in the message.
- AC-004: Each field shows its tag number, field name, raw value and, for enumerated fields, the value's meaning from the dictionary (TR-001). An unknown tag is shown as "Unknown tag X" with its raw value. An enum value missing from the dictionary is shown raw, with "unknown value".
- AC-005: Messages are separated visually, for example as cards or sections, each labelled with its message number in the log and its MsgType name.
- AC-006: Processing completes in under 5 seconds for a 100-message log.
- AC-024: If the page's script has not run, the page shows a visible message in place of the tool: "FIX Lens did not start. Open it through a web server, not as a file from disk." The message is part of the static HTML and is removed by the script when it starts.

### US-002: Session Behaviour Timeline

**As a** FIX support technician
**I want to** see a timeline of session-level behaviour across all messages
**So that** I can understand the session flow: logon, heartbeats, sequence numbers, gaps, resends, rejects, and order lifecycle

**Acceptance Criteria:**

- AC-007: A timeline lists session events in the order they appear in the log. Events are not re-sorted by timestamp.
- AC-008: The session events are:
    - Logon (35=A)
    - Logout (35=5)
    - Heartbeat (35=0)
    - TestRequest (35=1)
    - ResendRequest (35=2)
    - SequenceReset (35=4), shown as GapFill when GapFillFlag (123)=Y, otherwise as Reset
    - SessionReject (35=3)
    - BusinessReject (35=j)
    - SequenceGap, as defined in TR-003
- AC-009: The order lifecycle events are:
    - NewOrder (35=D)
    - CancelRequest (35=F)
    - ReplaceRequest (35=G)
    - CancelReject (35=9)
    - ExecutionReport (35=8), mapped as in TR-003: Acknowledgement, Fill, Cancelled, Replaced, TradeCancel, TradeCorrect or OrderStatus. Any other ExecType is shown as "ExecutionReport (ExecType X)".
- AC-010: Each event shows its message number in the log, the event name, SendingTime (52) when present, the sender and target (49 and 56) and MsgSeqNum (34). Order events also show ClOrdID (11) and, when present, OrderID (37) and OrigClOrdID (41). TradeCancel and TradeCorrect events also show ExecRefID (19).
- AC-011: The timeline is in a separate section or tab from the field-by-field decode.

### US-003: Handle Malformed Messages

**As a** FIX support technician
**I want to** see clear error messages when my log contains malformed or incomplete messages
**So that** I can identify where the problem is and fix it

**Acceptance Criteria:**

- AC-012: A malformed message (as defined in TR-002) produces an error giving the message number, the character position in the pasted log, and which rule failed.
- AC-013: A malformed message is not decoded and adds no timeline events.
- AC-014: Valid messages before and after a malformed one are still decoded and still appear in the timeline.
- AC-015: Error messages name the problem in plain words, for example "Message 5: missing CheckSum (tag 10) at position 234" or "Message 2: BodyLength (9) says 112, actual 108".

### US-004: Handle Large Logs

**As a** FIX support technician
**I want to** be informed if my log exceeds the maximum size
**So that** I can split it into smaller chunks

**Acceptance Criteria:**

- AC-016: If the pasted text is larger than 1,048,576 bytes (UTF-8) or contains more than 1,000 messages, the tool shows a warning with the measured size and message count.
- AC-017: The warning suggests splitting the log into smaller chunks.
- AC-018: A log over either limit is not decoded at all, and no partial output is shown.

### US-005: No Data Retention

**As a** FIX support technician
**I want to** be confident that my pasted log is not stored or logged
**So that** I can safely paste logs that may contain client information

**Acceptance Criteria:**

- AC-019: All processing is in memory, in the page.
- AC-020: The page cannot send data anywhere. Its Content-Security-Policy is `default-src 'self'; connect-src 'none'; form-action 'none'`, and the code makes no network calls (`fetch`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`).
- AC-021: Nothing is logged, cached or persisted. The code doesn't use `localStorage`, `sessionStorage`, IndexedDB, cookies or service workers, and doesn't log any input.
- AC-022: Refreshing the page clears all data, and the textarea is not restored by the browser (`autocomplete="off"`).
- AC-023: Automated checks fail the build if any API listed in AC-020 or AC-021 appears in the source, or if the CSP is missing or different.

### US-006: A Clear, Themed Presentation

**As a** FIX support technician
**I want** the page laid out and styled so that the session, the orders and the errors stand out
**So that** I can read a log quickly, in a light or a dark room

**Acceptance Criteria:**

- AC-025: The page has a header with the product name and the line "Runs entirely in this page. Nothing you paste is sent, stored or logged."
- AC-026: After a decode, a summary strip shows five counts for the log: messages, valid, malformed, sequence gaps, orders.
- AC-027: On a window 900 px wide or more, the timeline and the decoded messages are side by side, and the timeline stays in view while the messages scroll. Under 900 px they are one column.
- AC-028: Each decoded message is a card with a header (message number, MsgType name, sender to target, MsgSeqNum, SendingTime) and a table of its fields with four columns: tag, field, value, meaning.
- AC-029: A malformed message appears as an error card at its place in log order, with the text AC-012 requires.
- AC-030: Each timeline row shows the message number, the time, the event name as a badge, the direction, the sequence number and the order ids. Order events, sequence gaps and rejects are each marked differently, and never by colour alone: the badge text always names the event.
- AC-031: The page has a light and a dark theme. On load it follows the system setting (`prefers-color-scheme`). A button switches the theme. The choice is not stored, so a reload returns to the system setting.
- AC-032: In both themes, text meets WCAG 2.1 AA contrast (4.5 to 1) against its background.
- AC-033: The presentation keeps the v1.1 security rules (TR-006), and adds: no inline script or style, and no HTML attribute is ever set from pasted text.

### US-007: The Story of One Order

**As a** FIX support technician
**I want to** click any order id and see everything that happened to that order
**So that** I can follow one order through acknowledgement, fills, replaces and cancels without reading the whole log

**Acceptance Criteria:**

- AC-034: Every ClOrdID (11), OrigClOrdID (41) and OrderID (37) value shown in the timeline or in a message card is a button.
- AC-035: Messages belong to the same order when they share a ClOrdID (11) or an OrderID (37), or are linked by an OrigClOrdID (41) that equals another message's ClOrdID, directly or through other messages. A cancel/replace chain is therefore one order.
- AC-036: Activating an id shows only that order's messages and timeline events, under a banner with:
    - every ClOrdID and OrderID of the order;
    - its terms, from its first message: side, quantity, symbol, price when present, order type;
    - its latest state, from its last ExecutionReport: OrdStatus (39) and, when CumQty (14) is above zero, the filled quantity and AvgPx (6).
- AC-037: The banner has a "Show all messages" button that returns to the full log. Decoding again also returns to the full log.
- AC-038: Message numbers, sequence gaps and every other result are those of the full log. Selecting an order only changes what is shown.

### US-008: Buys, Sells and Net per Symbol

**As a** FIX support technician
**I want** a table of what was bought and sold in the log, per symbol
**So that** I can check a client's activity against what they expect, at a glance

**Acceptance Criteria:**

- AC-039: After a decode, a table has one row per Symbol (55), sorted by symbol, with: buy orders, bought, average buy price, sell orders, sold, average sell price, net.
- AC-040: Buy orders and sell orders count NewOrderSingle messages (35=D) by Side (54).
- AC-041: Bought and sold are sums over executions as they stand at the end of the log. An execution is an ExecutionReport that is a Fill (TR-003) with LastQty (32) above zero. It is identified by its OrderID (37) and ExecID (17), and counted once, so a resent report is not counted twice.
- AC-042: A TradeCancel removes the execution that its ExecRefID (19) names.
- AC-043: A TradeCorrect replaces the quantity and price of the execution that its ExecRefID (19) names with its own LastQty (32) and LastPx (31). A later TradeCancel or TradeCorrect may name the original ExecID or the ExecID of an earlier correction of the same execution.
- AC-044: When the execution a report names is not in the log, a TradeCorrect counts as an execution with its own quantity and price, and a TradeCancel changes nothing. The table's note says how many such reports there were.
- AC-045: The average price is the sum of quantity times price over the side's executions, divided by the sum of their quantities, shown to at most 4 decimal places. A side with no executions shows a dash.
- AC-046: Net is bought minus sold.
- AC-047: Side 1 (Buy) and 3 (Buy minus) are buys. Side 2 (Sell), 4 (Sell plus), 5 (Sell short) and 6 (Sell short exempt) are sells. Messages with any other side, or with no Symbol, are not counted.
- AC-048: A note under the table says: "Bought and sold are filled quantities from execution reports in this log, counted once per ExecID, after trade cancels and corrections."
- AC-049: The table follows the filters (US-009) and the selected order (US-007).

### US-009: Filter the Log

**As a** FIX support technician
**I want to** narrow the log to one account or one counterparty
**So that** I can look at one client's or one desk's flow in a shared log

**Acceptance Criteria:**

- AC-050: Five filters are offered: Account (1), SenderCompID (49), SenderSubID (50), TargetCompID (56) and TargetSubID (57). Each is a list of the distinct values present in the log, sorted, with "All" first. A filter with no values in the log is shown disabled.
- AC-051: The Account filter keeps every message of every order (AC-035) that has at least one message with that Account. The other four keep the messages whose own field has the chosen value.
- AC-052: Filters combine: a message is shown only if it passes every filter that is set.
- AC-053: The timeline, the message cards and the trading summary all show the filtered log. While a filter is set or an order is selected, the summary strip shows "N of M messages" and the sequence gaps and orders among the messages shown, and leaves out the valid and malformed counts.
- AC-054: While a filter is set or an order is selected, malformed messages are not shown.
- AC-055: A "Clear filters" button resets all five. Decoding again also resets them.
- AC-056: Filtering never changes a result. Sequence gaps, message numbers, order grouping and the effect of trade cancels and corrections are computed on the full log (AC-038).

## Technical Requirements

### TR-001: FIX Field Dictionary

- **Coverage:** a dictionary for FIX 4.2 and FIX 4.4, mapping each tag number to its field name and data type, and each enumerated value to its symbolic name.
- **Source:** generated by a build script from the official FIX Trading Community Orchestra files, `OrchestraFIX42.xml` and `OrchestraFIX44.xml`. They live in the `FIX Standard` folder of github.com/FIXTradingCommunity/orchestrations, are licensed Apache-2.0, and were translated from the FIX Unified Repository 2010 Edition. The repository's licence and copyright notice are kept alongside the generated file.
- **Content:** field names, types, and enum values with their symbolic names only. No specification prose or descriptions are copied (Legal brief).
- **Version:** the dictionary is chosen per message from BeginString (8): `FIX.4.2` or `FIX.4.4`.
- **Pinning:** the source files are pinned to a specific commit of that repository, recorded in the build script, so the dictionary is reproducible.

### TR-002: Message Parsing and Framing

- **Delimiters:** fields are separated by SOH (0x01), `|`, the text `^A` or the text `<SOH>`. The delimiter is chosen per message: it is whichever of the four follows the BeginString value of that message. Only that delimiter separates fields in that message.
- **A delimiter inside a value:** when the delimiter is one of the three text forms, an occurrence of it separates fields only if a tag and `=` follow it (one or more digits, then `=`), or if it ends the CheckSum field. Any other occurrence is part of the value of the field it is in. With the SOH byte itself, every occurrence separates fields, as the protocol requires.
- **Byte counts:** in length and checksum calculations, each occurrence that separates fields counts as the single byte 0x01. An occurrence that is part of a value counts as its own bytes.
- **The one case that text cannot settle:** a value that contains the delimiter followed by digits and `=` reads as a new field. BodyLength still matches and CheckSum does not, so the message is reported with a CheckSum error.
- **Message boundaries:** a message starts at `8=FIX` and ends after its CheckSum field (`10=` followed by 3 digits). Text before `8=FIX` on a line (timestamps, direction markers) is ignored. Several messages on one line, and one message per line, are both supported.
- **Malformed:** a message is malformed if any of these holds:
    - its first three fields are not 8, 9 and 35, in that order;
    - it has no CheckSum (10) as its last field;
    - a field has no `=`;
    - a tag is not a positive integer;
    - BodyLength (9) doesn't equal the byte count from after the delimiter that ends field 9, up to and including the delimiter before `10=`;
    - CheckSum (10) doesn't equal the sum of all bytes before `10=`, modulo 256, written as 3 digits.
- **Positions:** character positions in error messages (AC-012) are positions in the pasted text, whatever the delimiter.
- **Routing:** the message type (tag 35) selects the decoder and the timeline handling.

### TR-003: Session Behaviour Detection

- **Message types:** session events and order events follow the MsgType mapping in AC-008 and AC-009.
- **ExecutionReport mapping.** These are checked first:
    - **FIX 4.2**, by ExecTransType (20): `1` is TradeCancel, `2` is TradeCorrect, `3` is OrderStatus. `0`, or no tag 20, falls through to the mapping by ExecType.
    - **FIX 4.4**, by ExecType (150): `H` is TradeCancel, `G` is TradeCorrect, `I` is OrderStatus.
- **Then, by ExecType (150):**
    - `0` is Acknowledgement;
    - `1` or `2` (FIX 4.2) and `F` (FIX 4.4) are Fill;
    - `4` is Cancelled;
    - `5` is Replaced.
- **Consequence:** a FIX 4.2 report with ExecType `1` or `2` is a Fill only when its ExecTransType is `0` or absent.
- **Sequence numbers:** sequence numbers (34) are tracked separately for each direction, meaning each SenderCompID (49) / TargetCompID (56) pair.
    - A **SequenceGap** is a message whose MsgSeqNum is greater than the expected next number, which is the last MsgSeqNum seen for that direction plus one.
    - Messages with PossDupFlag (43)=Y don't advance or reset the expected number.
    - A SequenceReset (35=4) sets the expected next number to NewSeqNo (36).
    - A Logon with ResetSeqNumFlag (141)=Y resets the direction's expected next number to 1.

### TR-004: User Interface

- **Page:** a single-page static web app (HTML/JS, no backend), with a textarea and a "Decode" button.
- **Layout:** as US-006 describes.
- **Browsers:** current desktop Chrome, Firefox, Safari and Edge.
- **Code structure:** the parsing, decoding and timeline logic, order grouping, the trading summary and the filters are plain JavaScript modules with no DOM access, so they can be tested without a browser.

### TR-005: Performance

- **Speed:** a 100-message log is processed in under 5 seconds, measured on the logic modules.
- **Views:** for a 1,000-message log, order grouping, the trading summary and applying the filters each take under 1 second, measured on the logic modules.
- **Limits:** logs up to the limits in Scope are handled without crashing. Larger logs are refused, as AC-016 to AC-018 describe.

### TR-006: Security

- **No network:** no data is sent to external servers (AC-020).
- **No persistence:** nothing is logged, cached or persisted (AC-021).
- **Output:** all output is rendered with text nodes or `textContent`, never `innerHTML` or `insertAdjacentHTML`, so pasted content can't inject markup. AC-023 also checks this.
- **Page:** no inline script or style, and no HTML attribute is ever set from pasted text (AC-033). The automated checks of AC-023 also fail the build on an inline `<script>` or `style` attribute in the page, and on `setAttribute` with a value that comes from pasted text.
- **Input:** input is framed and validated (TR-002) before decoding.

## Success Metrics

### North Star Metric

Time from paste to understandable decode: under 5 seconds for a 100-message log.

### Leading Indicators

- Number of fields correctly decoded
- Number of session-level events correctly identified
- Number of malformed messages correctly rejected with clear error messages

### Lagging Indicators

- Reduction in time-to-diagnosis for FIX session issues (measured after 30 days of use)
- Number of support technicians using the tool weekly

## Delivery Plan

The agent delivery harness builds FIX Lens as ordered tickets. Each one goes through triage, planning, implementation, the deterministic gates, the cross-lab review and a handoff. Tickets 1 to 8 are v1.1 and are built. Tickets 9 to 16 are v1.2.

| # | Ticket | Depends on |
| --- | --- | --- |
| 1 | Log splitting and field parsing (TR-002 framing, delimiters, boundaries) |  |
| 2 | Malformed-message detection and error messages (US-003, TR-002) | 1 |
| 3 | FIX 4.2/4.4 dictionary generation from the Orchestra files and lookup, with enums and unknown tags (TR-001) |  |
| 4 | Field-by-field decoder (US-001 AC-003 to AC-006) | 1, 3 |
| 5 | Session timeline and sequence-gap detection (US-002, TR-003) | 1 |
| 6 | Size limits (US-004) | 1 |
| 7 | The page: textarea, Decode button, sections, safe rendering, CSP and no-retention checks (TR-004, TR-006, US-005) | 2, 4, 5, 6 |
| 8 | The dictionaries as JavaScript modules, so that the page works under its own CSP in a real browser | 7 |
| 9 | `^A` and `<SOH>` delimiters, and a delimiter inside a value (TR-002) |  |
| 10 | CancelRequest, ReplaceRequest, CancelReject, TradeCancel, TradeCorrect and OrderStatus events (AC-009, AC-010, TR-003) |  |
| 11 | Order grouping module (AC-035) |  |
| 12 | Trading summary module, with trade cancels and corrections (AC-039 to AC-048) | 10 |
| 13 | Filter module (AC-050 to AC-052, AC-056) | 11 |
| 14 | The presentation: layout, cards, timeline rows, summary strip, themes, the not-started message (US-006, AC-024) | 9, 10 |
| 15 | The order story on the page (US-007) | 11, 14 |
| 16 | The trading summary and the filters on the page (AC-049, AC-053 to AC-055) | 12, 13, 15 |

Deployment to the internal web server follows after the user has tested with real FIX logs.

## Risks and Mitigations

### Risk 1: FIX Dictionary Completeness

- **Risk:** the dictionary may not cover every field used in real logs, such as custom or user-defined tags.
- **Mitigation:** generate the dictionary from the official FIX 4.2 and 4.4 Orchestra files, and show unknown tags as "Unknown tag X" with their raw values. The FIX Trading Community notes that these files are frozen, and that some FIX 4.2 repeating-group identities were aligned with later versions. That doesn't affect top-level field and enum lookup.

### Risk 2: Performance with Large Logs

- **Risk:** the tool may be slow, or crash, with large logs.
- **Mitigation:** hard limits of 1,048,576 bytes and 1,000 messages; linear-time parsing; a performance test on the logic modules.

### Risk 3: Malformed Message Handling

- **Risk:** malformed messages could crash the tool or produce wrong output.
- **Mitigation:** framing checks (TR-002) before decoding, malformed messages isolated from the rest, and clear errors with their positions.

### Risk 4: The Trading Summary Is Read as a Position Report

- **Risk:** a technician treats the net figure as the client's position.
- **Mitigation:** the note of AC-048 under the table. The figures cover the executions in this log only, and a log that starts mid-session is missing earlier ones (AC-044 reports the cancels and corrections that point outside the log).

### Risk 5: Hidden Tests Tied to the Old Page Structure

- **Risk:** the v1.1 acceptance tests describe the v1.1 page, so the presentation ticket would be reported as a regression.
- **Mitigation:** the harness gains a way to retire named hidden tests on purpose (harness change D19) before ticket 14 is loaded.

## Dependencies

- **FIX Trading Community Orchestra files** (`OrchestraFIX42.xml` and `OrchestraFIX44.xml`, in github.com/FIXTradingCommunity/orchestrations, Apache-2.0): the source for the field dictionary
- **Internal web server:** for deploying the static web app
- **Real FIX logs:** for testing before deployment (provided by the support team)

## Approvals

- **BRD:** Approved by Risk Committee (2026-11-24). Refreshed for the extended functionality of v1.2; the refresh was approved on 2026-11-26.
- **PRD:** v1.2 approved by Ubay Gonzalez (2026-11-26). v1.1 approved by Ubay Gonzalez (2026-11-25).
- **Technical Design:** v1.2 approved by Ubay Gonzalez (2026-11-26) (see the child page FIX Lens - Technical Design). It replaces v1.1, which was approved under delegation on 2026-11-25.
- **Implementation:** v1.1 is built: tickets 1 to 8 are on the trusted main (2026-11-26). It has not yet been tested with real logs or deployed. v1.2 is pending.
