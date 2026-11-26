# FIX Lens - Technical Design (copy of Confluence page 1409027, v1.2)

**Version:** 1.2, for PRD v1.2 (Gate 3 approved 2026-11-26).
**Status:** Approved by Ubay Gonzalez (2026-11-26). It replaces v1.1, which was approved under delegation on
2026-11-25.
**Built by:** the agent delivery harness. Tickets FXL-1 to FXL-8 are built. This version adds FXL-9 to FXL-16.

Sections marked **(changed)** differ from v1.1. Sections marked **(new)** are additions. Everything else is
unchanged from v1.1.

## 1. Shape (changed)

FIX Lens is one static page plus plain ES modules. There's no build step for the page itself: the browser loads
`index.html`, which loads `src/main.js` as a module. All logic modules are pure functions with no DOM access
(TR-004), so they're tested with Vitest in Node. Only `src/render.js` and `src/main.js` touch the DOM.

```
index.html              CSP meta tag, header, not-started message, textarea, Decode button, three sections
styles.css              layout and the two themes
src/framing.js          split a paste into messages, parse fields, check framing (TR-002)
src/limits.js           byte and message-count limits (US-004)
src/dictionary/fix42.js, fix44.js   generated, committed: `export default <JSON>;` and nothing else (TR-001)
src/dictionary.js       lookup by BeginString, tag and enum value
src/decode.js           field-by-field decode (US-001)
src/execution.js        what kind of ExecutionReport a message is (TR-003)                      new
src/timeline.js         session and order events, sequence gaps (US-002, TR-003)
src/orders.js           group messages into orders (US-007)                                    new
src/summary.js          executions, trade cancels and corrections, buys and sells (US-008)     new
src/filters.js          the five filters (US-009)                                              new
src/analyse.js          one entry point: limits, then framing, then decode and timeline
src/render.js           DOM output with text nodes and textContent only (TR-006)
src/main.js             wires the page to analyse() and render(); holds the view state
tools/build-dictionary.mjs   Orchestra XML to the two dictionary modules
vendor/orchestra/       OrchestraFIX42.xml, OrchestraFIX44.xml, LICENSE, NOTICE, SOURCE.md (pinned commit)
test/                   Vitest tests, one file per module, plus test/helpers/fix.js
```

The dictionaries are JavaScript modules, not JSON files: a JSON module import is a fetch, and the page's
`connect-src 'none'` blocks it.

## 2. Data model (changed)

All positions are **0-based character offsets into the pasted text** (JavaScript string indices), shown to the
user as 1-based.

- **Field:** `{ tag: number, value: string, position: number }`. `position` is where the tag starts.
- **Message:** `{ number, start, end, fields, beginString, msgType }`. `number` is 1-based, in order of
  appearance among all message candidates (valid or malformed). `start` and `end` are offsets in the paste.
- **ParseError:** `{ number, position, rule, text }`. `rule` is one of `field_without_equals`, `bad_tag`,
  `header_order`, `missing_checksum`, `checksum_format`, `body_length`, `checksum`. `text` is the plain-words
  message (AC-015).
- **DecodedField:** `{ tag, name, value, enumName, known }`. `name` is `"Unknown tag X"` when the tag isn't in
  the dictionary. `enumName` is null for non-enum fields, and `"unknown value"` for an enum value the dictionary
  doesn't list.
- **DecodedMessage:** `{ number, label, supported, fields }`, with `fields` the DecodedFields in message order.
- **TimelineEvent:** `{ number, kind, name, sendingTime, sender, target, seqNum, clOrdId, orderId, origClOrdId,
  execRefId, detail }`. `kind` is `session` or `order`. `origClOrdId` and `execRefId` are null when the message
  has no tag 41 or 19.
- **Analysis:** `{ ok, limit, messages, errors, decoded, timeline }`. When a limit is exceeded, `ok` is false,
  `limit` holds the measured size and count, and every other list is empty (AC-018).
- **OrderGroup:** `{ clOrdIds: string[], orderIds: string[], numbers: number[] }` (section 12).
- **Execution:** `{ number, symbol, side, qty, px }`, with `side` `"buy"` or `"sell"` (section 13).
- **TradeSummary:** `{ rows, unmatched }`. A row is `{ symbol, buy, sell }`, and each side is
  `{ orders, orderedQty, fills, filledQty, notional, pricedQty }`.
- **View:** `{ orderId: string | null, filters: { account, senderCompId, senderSubId, targetCompId,
  targetSubId } }`, each filter a string or null. It lives in `main.js`, in memory only.

## 3. Framing (TR-002) (changed)

Positions are offsets into the string given to `analyse()`, counted in JavaScript string units (UTF-16). The
textarea already turns CRLF into LF; `\r\n`, `\n` and `\r` all end a line. A message never crosses a line end.

1. **The four delimiter forms:** the SOH character (0x01), `|`, the two characters `^A`, and the five characters
   `<SOH>` (upper case only).
2. **Message start:** outside a message, `8=FIX` starts a candidate at the start of a line, after any delimiter
   form, or after a character that isn't a digit (so `448=FIXCLIENT` never starts one). Text before it on the
   line is ignored. Inside a candidate that hasn't reached its CheckSum, `8=FIX` starts a new candidate only
   right after a separator of that candidate (step 4).
3. **Delimiter per message:** scan from the candidate's start to the end of its line. The candidate's delimiter
   is the form whose first occurrence comes earliest. If none occurs, the candidate is the rest of the line and
   fails `header_order`.
4. **Separators:**
   - When the delimiter is the SOH character, every occurrence is a separator.
   - When it is a text form (`|`, `^A` or `<SOH>`), an occurrence is a separator only in one of these cases:
     it is followed by one or more digits and `=`; it is followed by a line end or by the end of the text; or it
     comes right after a CheckSum field, meaning `10=` and exactly 3 digits where the `10=` itself starts right
     after a separator. Any other occurrence is ordinary text in the value of the field it is in.
   - The other three forms are always ordinary text in that message.
5. **Message end:** a candidate ends after its CheckSum field: a field that starts right after a separator with
   `10=`, followed by 3 digits, then the delimiter, a line end or the end of the text. Failing that, it ends
   where the next candidate starts, or at the line end.
6. **Fields:** split the candidate at its separators. A trailing empty piece after the final separator is
   dropped. With the SOH character, an empty piece in the middle is a field without `=`. With a text form, an
   empty piece cannot occur.
7. **Byte counts.** Nothing is normalised in place, so offsets never move. For a field, its bytes are the UTF-8
   bytes of its text in the paste (`tag=value`, the value including any delimiter text that is not a separator),
   plus one byte, 0x01, for the separator that ends it.
8. **Rules, checked in this order; only the first failure is reported:**
   1. a field without `=`: `field_without_equals`;
   2. a tag that isn't a positive integer (digits only, no leading zero, at most 9 digits): `bad_tag`;
   3. fewer than three fields, or the first three tags aren't 8, 9, 35: `header_order`;
   4. the last field isn't tag 10: `missing_checksum`; tag 10 last but its value isn't exactly 3 digits:
      `checksum_format`;
   5. BodyLength 9 isn't a non-negative integer, or doesn't equal the sum of the bytes (step 7) of every field
      after field 9 and before field 10: `body_length`;
   6. the sum of the byte values (step 7) of every field before field 10, modulo 256 and written as 3 digits,
      isn't the value of tag 10: `checksum`.
9. **Error position:** the 1-based position of the failing field's first character; for `missing_checksum`, the
   candidate's end.
10. **Error text:** always `Message N: <problem> at position P`, for example `Message 5: missing CheckSum (tag
    10) at position 234` and `Message 2: BodyLength (9) says 112, actual 108 at position 12`.

A malformed candidate is kept as an error only. It isn't decoded and adds no timeline events (AC-013). Every
other candidate goes on normally (AC-014).

**What text cannot settle.** With a text delimiter, a value that contains the delimiter followed by digits and
`=` is read as a new field. BodyLength still matches, because both readings have the same number of bytes. The
CheckSum does not, so the message is reported with `checksum`. No other reading is tried.

## 4. Limits (US-004)

They're checked **before** framing.
- **Size:** `new TextEncoder().encode(paste).length > 1_048_576`.
- **Count:** the number of message candidates (section 3) `> 1_000`.

Over either limit, `analyse()` returns `ok: false` with both measured numbers and nothing else. The warning names
both numbers and suggests splitting the log (AC-016, AC-017).

## 5. Dictionary (TR-001) (changed)

- **Source:** `OrchestraFIX42.xml` and `OrchestraFIX44.xml` from github.com/FIXTradingCommunity/orchestrations,
  folder `FIX Standard`.
  - They're **vendored** into `vendor/orchestra/` at one pinned commit, recorded in `SOURCE.md` and as a constant
    in the build script.
  - The repository's `LICENSE` (Apache-2.0) and any `NOTICE` file are copied alongside, **and also into
    `src/dictionary/`** next to the generated files, with a `SOURCE.md` naming the pinned commit (TR-001).
  - Tests and builds never use the network.
- **`tools/build-dictionary.mjs`** reads the XML with a small streaming parser in the script itself, with no
  dependency. It writes `src/dictionary/fix42.js` and `fix44.js`. Each file is exactly `export default `, one
  JSON object, and `;`. The object has the form
  `{ "<tag>": { "name", "type", "enums": { "<value>": "<symbolicName>" } } }`.
  - `type` is the Orchestra datatype name. `enums` is present only for fields with a code set. Description text
    is never copied.
  - Keys are sorted, so the output is byte-for-byte reproducible.
- **Generated files are committed.** A test runs the build into a temp folder and checks the output is identical
  to the committed files, and that the licence files are present.
- **Lookup:** `lookup(beginString, tag)` and `enumName(beginString, tag, value)`. `FIX.4.2` and `FIX.4.4` are
  supported. Any other BeginString makes the message "unsupported version": its label is
  `Message N: unsupported version <value of 8>`, its fields are shown raw, and it still takes part in the
  timeline (section 7).

## 6. Decode (US-001)

`decode(message)` returns the DecodedFields in message order (AC-003, AC-004). Repeated tags stay in order and
aren't errors; an empty value such as `58=` is shown as empty. The message label is
`Message <number>: <MsgType name>`, where the name comes from the dictionary's enum for tag 35 (AC-005). If 35
repeats, the first value counts, here and in the timeline.

## 7. Timeline (US-002, TR-003) (changed)

The analysis walks the valid messages in log order (AC-007), keeping `expected` per **direction**, keyed by the
pair (SenderCompID 49, TargetCompID 56); a missing 49 or 56 is the empty string in the key. A direction counts as
**seen** only after its first message has been processed.

For each message (`seq` is 34 as a number; if 34 is missing or not a number, skip steps 1 to 3):
1. **Logon (35=A) with 141=Y:** set `expected[dir] = 1`.
2. **SequenceGap check:** only if the direction has been seen, 43 isn't `Y`, the message isn't a SequenceReset
   in Reset mode (35=4 without 123=Y; FIX ignores its MsgSeqNum), and `seq > expected[dir]`. The gap event comes
   **before** the message's own event, with `detail: "expected N, received M"`. The first message of a direction
   never makes a gap, even with 141=Y.
3. **Update `expected[dir]`:**
   - 43=Y: no change. This wins over NewSeqNo, so a resent GapFill changes nothing.
   - SequenceReset (35=4): `expected = 36` when 36 is a positive integer, otherwise `seq + 1`.
   - Otherwise, if `seq >= expected` or the direction hasn't been seen: `expected = seq + 1`. A lower number
     changes nothing and adds no event.
4. **The message's own event**, named from this fixed table (the PRD's names, not the dictionary's):

   | MsgType | Event | kind |
   |---|---|---|
   | A | Logon | session |
   | 5 | Logout | session |
   | 0 | Heartbeat | session |
   | 1 | TestRequest | session |
   | 2 | ResendRequest | session |
   | 4 | GapFill when 123=Y, otherwise Reset | session |
   | 3 | SessionReject | session |
   | j | BusinessReject | session |
   | D | NewOrder | order |
   | F | CancelRequest | order |
   | G | ReplaceRequest | order |
   | 9 | CancelReject | order |
   | 8 | `executionKind(message)`, below | order |

   Other MsgTypes add no event.
5. **`executionKind(message)`** in `src/execution.js` takes a Message or a DecodedMessage with MsgType 8 and
   returns the event name. It checks, in this order:
   1. on `FIX.4.2`, ExecTransType 20: `1` is `TradeCancel`, `2` is `TradeCorrect`, `3` is `OrderStatus`;
   2. on `FIX.4.4`, ExecType 150: `H` is `TradeCancel`, `G` is `TradeCorrect`, `I` is `OrderStatus`;
   3. ExecType 150: `0` is `Acknowledgement`; `1` or `2` on FIX.4.2, or `F` on FIX.4.4, is `Fill`; `4` is
      `Cancelled`; `5` is `Replaced`;
   4. anything else: `ExecutionReport (ExecType X)`; no 150: `ExecutionReport (no ExecType)`.

   For an unsupported version only step 3's `0`, `4` and `5` are mapped. The timeline and the trading summary
   both call this one function, so a Fill in the timeline is always an execution in the summary.
6. **Event fields:** each event carries the message number, the name, SendingTime 52 when present, 49, 56 and 34
   (blank when missing) (AC-010). Order events also carry ClOrdID 11, OrderID 37 and OrigClOrdID 41 when
   present. TradeCancel and TradeCorrect events also carry ExecRefID 19.

## 8. Page and security (TR-004, TR-006, US-005) (changed)

### 8.1 `index.html`

- has, as the **first element in `<head>`**, `<meta http-equiv="Content-Security-Policy" content="default-src
  'self'; connect-src 'none'; form-action 'none'">` (AC-020). It's the only CSP meta tag;
- has a `<header>` with the product name, the line of AC-025, and `<button id="theme-button" type="button">`;
- has `<p id="not-started">FIX Lens did not start. Open it through a web server, not as a file from
  disk.</p>` (AC-024). `main.js` removes this element as its first statement;
- has `<textarea id="paste" autocomplete="off" spellcheck="false" autocapitalize="off" autocorrect="off"
  translate="no">`. Turning spellcheck off matters: enhanced browser spellcheck can send the text to a service
  (AC-019, AC-020, AC-022);
- has `<button id="decode-button" type="button">Decode</button>`;
- has three sections: `<section id="summary">`, `<section id="timeline">` and `<section id="decode">`
  (AC-011);
- loads `src/main.js` as a module and `styles.css` as a stylesheet. There's **no inline script or style and no
  `style=` attribute**, because the CSP blocks them.

**The page must be served over HTTP.** Browsers block module scripts from `file://`; AC-024 is what the user
sees then.

### 8.2 What `render(result, view, handlers)` builds

`handlers` is `{ pick(id), clear(), setFilter(key, value) }`. `render.js` builds every node with
`document.createElement`, sets text with `textContent` only, and never calls `setAttribute`. The only element
properties it sets are `textContent`, `className` (from fixed strings, never from pasted text), `type`,
`disabled` and `selectedIndex`. It creates no links.

What is shown: `passing = applyFilters(decoded, view.filters)`; with `view.orderId`, `shown` is the messages of
`passing` that are in that order's group; otherwise `shown = passing`. The timeline shows the events whose
message number is in `shown`. `narrowed` is true when a filter is set or an order is selected.

Inside `#summary`, in this order:

1. **The order banner**, only when an order is selected: `div.order-story` with the order's ClOrdIDs and
   OrderIDs joined by ` · ` in a `strong`, `span.order-terms`, `span.order-state`, and
   `button.show-all` with the text `Show all messages`, which calls `handlers.clear()`.
   - **Terms:** from the group's first NewOrder (35=D), or its first message when it has none: the meaning of
     54, the value of 38, the value of 55, `@ <44>` when 44 is present, the meaning of 40, joined by spaces.
   - **State:** from the group's last ExecutionReport (35=8): the meaning of 39, then, when 14 is a number above
     zero, ` · <14> filled @ <6>`. No ExecutionReport: no state.
   - "The meaning of" a tag is its `enumName`, or its value when it has none or the name is `unknown value`.
2. **The summary strip** `div.stats` of `span.stat` elements (AC-026, AC-053):
   - not narrowed: `N messages` (valid plus malformed), `N valid`, `N malformed`, `N sequence gaps`, `N orders`;
   - narrowed: `N of M messages`, then the sequence gaps and orders among the messages shown.
   - A count of one uses the singular: `1 message`, `1 sequence gap`, `1 order`.
3. **The trading summary** `div.trades` (section 13): a `table.trade-table` whose header cells are `Symbol`,
   `Buy orders`, `Bought`, `Avg buy`, `Sell orders`, `Sold`, `Avg sell`, `Net`; then `p.note` with the text of
   AC-048; then, when `unmatched` is above zero, `p.note.unmatched`: `N trade cancels or corrections refer to an
   execution that is not in this log.` (singular: `1 trade cancel or correction refers to ...`). With no rows:
   `p.empty` `No orders or fills in the messages shown.` and no table.
4. **The filters** `div.filters`: five `label.filter`, each with a `span` (the labels of AC-050) and a
   `select`. The first option is `All`; then one option per value, its text set with `textContent`. The chosen
   value is read from `selectedIndex`, never from an option's `value`. A filter with no values has
   `select.disabled = true`. When a filter is set, `button.clear-filters` with the text `Clear filters` calls
   `handlers.setFilter(null, null)`.

Inside `#timeline`: `ol.events` of `li.event`, each with `span.num` (`#N`), `span.time`, `span.badge` (the event
name), `span.dir` (`<sender> → <target>`), `span.seq` (`seq N`, empty when missing), one `button.order-link`
per id present, with the texts `ClOrdID <11>`, `OrderID <37>` and `OrigClOrdID <41>`, `span.ref`
(`ExecRefID <19>`) when present, and `span.detail`. The `li` also has one of the classes `gap` (SequenceGap),
`reject` (SessionReject, BusinessReject, CancelReject), `order` or `session`. With no events: `p.empty`.

Inside `#decode`, in log order: one `article.card` per shown message, and, when not narrowed, one
`article.card.malformed` per error (AC-029, AC-054).
- **A message card:** `header.card-head` with `span.num` (`#N`), `h3` (the label without its `Message N: `
  prefix), `span.dir`, `span.seq`, `span.time`; then `table.fields` with header cells `Tag`, `Field`, `Value`,
  `Meaning` and one row per field. The value of tag 11, 37 or 41 is a `button.order-link` whose text is the
  value alone.
- **A malformed card:** `span.num`, `h3` `Malformed message`, and `p.error-text` with the ParseError text.
- With nothing to show: `p.empty`, `No messages match the current filters.` when narrowed, otherwise
  `No FIX messages found in the pasted text.`

Every `button.order-link` calls `handlers.pick(id)` with the id alone. An OrderID that is not an identifier
(section 12) is plain text, not a button. `SendingTime` is shown as its time part: the text after the first `-`.

### 8.3 Themes (AC-031, AC-032)

- `styles.css` declares the colours as custom properties on `:root` (the light theme), again inside
  `@media (prefers-color-scheme: dark) { :root:not(.theme-light) { ... } }`, and again on `:root.theme-dark`.
  The two dark blocks hold the same values.
- The properties are `--bg`, `--panel`, `--ink`, `--muted`, `--line`, `--soft`, `--accent`, `--accent-ink`,
  `--ok`, `--warn`, `--warn-bg`, `--bad`, `--bad-bg`, `--order`, `--order-bg`, `--session-bg`. Every colour in
  the stylesheet is one of them.
- `#theme-button` sets `document.documentElement.className` to `theme-dark` or `theme-light`, and its own text to
  the theme it would switch to: `Light theme` or `Dark theme`. Its first state comes from
  `matchMedia('(prefers-color-scheme: dark)')`. Nothing is stored.
- **Contrast pairs, at least 4.5 to 1 in both themes:** `--ink` on `--bg`, `--ink` on `--panel`, `--muted` on
  `--panel`, `--muted` on `--bg`, `--accent-ink` on `--accent`, `--ok` on `--panel`, `--warn` on `--warn-bg`,
  `--bad` on `--bad-bg`, `--order` on `--order-bg`, `--ink` on `--session-bg`. A test reads the three blocks
  from `styles.css` and computes each ratio with the WCAG 2.1 formula.
- **Layout (AC-027):** `.results` is a two-column grid at `min-width: 900px`, with `#timeline` sticky; one column
  below that.

### 8.4 The source check (`test/static-checks.test.js`, AC-023, AC-033)

- **What it scans:** `index.html` and `src/**/*.js`, with comments stripped first, matching whole words or
  calls (for example `\bfetch\b`, `\bconsole\s*\.`). The two dictionary modules are checked separately: each
  must be exactly `export default `, one JSON value, and `;`.
- **What fails it:**
  - **network or leaving the page:** `fetch`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `EventSource`,
    `window.open`, assignments to `location` or `.href`, `setAttribute(`, any `import(` call, and any import of
    a path ending `.json`;
  - **storage:** `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `cookieStore`, `caches`,
    `openDatabase`, `navigator.storage`, `serviceWorker`, `Worker(`, `SharedWorker`;
  - **logging and markup:** `console`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`,
    `DOMParser`, `createContextualFragment`, `setHTMLUnsafe`, `srcdoc`, `eval`, `new Function`;
  - **attributes from data:** assignments to `.id`, `.name`, `.title`, `.src`, `.value`, `.style` or
    `.cssText` in `src/**/*.js`;
  - **in `index.html`:** a `<script>` without `src`, a `<style>` element, a `style=` attribute, or an `on...=`
    attribute.
- **The CSP check** parses `index.html` and fails unless there is exactly one CSP meta tag, it's first in
  `<head>`, and its content is the exact string above.
- **What it can't do:** it catches accidental use. It can't stop deliberate evasion such as
  `window['local'+'Storage']`. That's what the review is for.

## 9. Tests and tooling (changed)

- **Vitest**, with every test a top-level `test()` call (mutation testing reads them most reliably). Pure modules
  run in Node; `render.js` tests use Vitest's `jsdom` environment for that file only.
- **`test/helpers/fix.js`** builds valid messages from a field list, computing BodyLength and CheckSum, so tests
  never hard-code checksums by hand. It takes the delimiter form as an option. Malformed cases are made by
  changing one thing in a valid message.
- **Fixed reference messages.** Every ticket that touches framing or the trading summary carries messages and
  expected results written out in the ticket, computed independently of the code and of the helper. The helper
  alone is never the oracle.
- **Performance (AC-006, TR-005):** a test builds 100 valid mixed messages and checks that `analyse()` finishes
  in under 5 seconds. A second test builds 1,000 valid order messages and checks that `orderGroups`,
  `tradeSummary` and `applyFilters` each finish in under 1 second.
- **Dev dependencies, all pinned in `package.json`:** `vitest`, `jsdom`, `@stryker-mutator/core`,
  `@stryker-mutator/vitest-runner` (10.x). No runtime dependencies.
- **Harness settings:** `[repos.fix-lens]` overlay with the Vitest commands, with `test_dir = "test/"`. The JS
  dependencies are installed once into the root-owned dependencies folder.

## 10. Ticket order (changed)

FXL-1 to FXL-8 are built. FXL-9 to FXL-16 follow the PRD v1.2 delivery plan, tickets 9 to 16, in that order.
The harness runs them one at a time, each after its blockers. Each ticket lists its acceptance criteria as
testable statements taken from the PRD, starts with its interface criterion, and names the test files it is
expected to change.

## 11. Decisions the PRD left open (changed)

| Topic | Decision |
|---|---|
| Error position | 1-based position (UTF-16 units) in the string given to `analyse()`, of the failing field |
| Several failing rules | Only the first, in the order of section 3 |
| Unsupported BeginString | Labelled `unsupported version <8>`, fields shown raw, in the timeline with only ExecType 0/4/5 mapped. Its ExecutionReports are never executions in the trading summary |
| No delimiter form after BeginString | The candidate is the rest of the line and fails `header_order` |
| Another delimiter form inside a message | Ordinary text |
| `<soh>` in lower case, `\x01` or `\u0001` written as text | Not delimiters |
| Leading-zero or very long tags | `bad_tag` (stricter than "positive integer") |
| CheckSum present but not 3 digits | `checksum_format` |
| MsgSeqNum lower than expected | Ignored: no event, expected number unchanged |
| PossDupFlag on a SequenceReset | PossDupFlag wins: nothing changes |
| Missing 34, 49 or 56 | No sequence check; empty string in the direction key; shown blank |
| Repeated 35 | The first value counts |
| Repeated 11, 37, 41, 17, 19, 32, 31, 54, 55, 1 | The first value counts, in grouping, the summary and the filters |
| Dictionary source at build time | Vendored XML at a pinned commit; no network |
| CSP delivery | Meta tag, because a static server may not set headers |
| OrderID `NONE` | Not an identifier (section 12) |
| Numbers in the trading summary | Section 13, "Figures" |
| A filter and a selected order together | Both apply: the order's messages that pass the filters |
| Decode pressed again | The selected order and the filters are cleared |

## 12. Orders (US-007) (new)

`orderGroups(decoded)` in `src/orders.js` returns the OrderGroups in order of first appearance. It is pure.

- **Keys of a message:** `C:<value>` for its ClOrdID 11 and for its OrigClOrdID 41, and `O:<value>` for its
  OrderID 37. An empty value gives no key.
- **OrderID `NONE` is not an identifier.** FIX uses `37=NONE` when there is no order to name, for example in a
  CancelReject for an unknown order. It gives no key and is never a button. The comparison is exact and
  case-sensitive.
- **Grouping:** all keys of one message are joined. Groups are the connected sets (union-find). A message with
  no key is in no group.
- **A group** lists its ClOrdIDs (from 11 and 41) and OrderIDs in order of first appearance, without repeats,
  and its message numbers in log order.
- `findOrder(groups, id)` returns the first group whose `clOrdIds` or `orderIds` contains `id`, or null.

Grouping always runs on the whole `decoded` list (AC-038, AC-056).

## 13. Trading summary (US-008) (new)

`tradeSummary(decoded, shown)` in `src/summary.js` is pure. `decoded` is the whole list. `shown` is a `Set` of
message numbers, or `undefined` for all. It returns `{ rows, unmatched }`.

**Step 1: executions, over the whole `decoded` list, in log order.** Only supported versions take part. The
state is a list of executions and a map from a report key to an execution or to `cancelled`. A report's key is
`<37>|<17>`; a missing 37 is the empty string; a report with no 17 has no key and is never matched or
deduplicated. For each ExecutionReport, by `executionKind`:

- **Fill** with LastQty 32 a finite number above zero: if its key is already in the map, skip it (a resend).
  Otherwise add an Execution `{ number, symbol: 55, side, qty: 32, px: 31 }` and map its key to it.
- **TradeCorrect:** if its own key is already in the map, skip it. Otherwise look up `<37>|<19>`:
  - **found, an execution:** set that execution's `qty` and `px` to this report's 32 and 31. Its `number`,
    `symbol` and `side` stay. Map this report's own key to the same execution.
  - **found, `cancelled`:** nothing changes. Map its own key to `cancelled`.
  - **not found:** it is **unmatched**. When its 32 is a finite number above zero, add an Execution from its own
    fields, as for a Fill. Map its own key to it.
- **TradeCancel:** if its own key is already in the map, skip it. Otherwise look up `<37>|<19>`:
  - **found, an execution:** remove it from the list. Map every key that pointed to it, and this report's own
    key, to `cancelled`.
  - **found, `cancelled`:** nothing changes.
  - **not found:** it is **unmatched**. Nothing else changes.
- Any other kind: nothing.

`side` is `"buy"` for Side 54 `1` or `3`, `"sell"` for `2`, `4`, `5` or `6` (AC-047). A report with another
side, or with no Symbol 55, makes no execution. `px` is 31 as a number, or null when it isn't a finite number.

**Step 2: rows.** With `shown`, keep the executions whose `number` is in it, and count as `unmatched` only the
unmatched reports whose number is in it.
- For each kept execution, in its symbol's row and side: `fills += 1`, `filledQty += qty`, and, when `px` is
  not null, `notional += qty * px` and `pricedQty += qty`.
- For each NewOrderSingle (35=D) among the shown messages, with a Symbol and a buy or sell side:
  `orders += 1` and `orderedQty += 38` when 38 is a finite number.
- Rows are sorted by symbol with plain string comparison (`<`), not locale order.

**Figures** (in `render.js`):
- `format(n)`: `n` rounded to 4 decimal places, written without trailing zeros and without a thousands
  separator. `1500` is `1500`; `71.25` is `71.25`; `0.1 + 0.2` is `0.3`.
- Bought and Sold: `format(filledQty)`. Average: `format(notional / pricedQty)`, or `–` (an en dash) when
  `pricedQty` is zero. Net: `format(buy.filledQty - sell.filledQty)`, with a leading `+` when above zero.

## 14. Filters (US-009) (new)

`src/filters.js` is pure.

- `FILTERS`: `account` (tag 1, `Account`), `senderCompId` (49, `SenderCompID`), `senderSubId` (50,
  `SenderSubID`), `targetCompId` (56, `TargetCompID`), `targetSubId` (57, `TargetSubID`), in that order.
- `filterOptions(decoded)` returns, per key, the distinct non-empty values in the whole log, sorted with plain
  string comparison.
- `applyFilters(decoded, chosen)` returns the messages that pass every key whose chosen value is not null
  (AC-052):
  - `account`: the messages of every OrderGroup (section 12) that has at least one message with that Account,
    plus any message outside all groups that carries that Account itself (AC-051);
  - the other four: the messages whose own field has that value.
- With every chosen value null it returns `decoded` unchanged.

## 15. What changes in v1.1 behaviour (new)

These are deliberate, and the tests that describe the old behaviour change with them:

| v1.1 | v1.2 |
|---|---|
| The delimiter is chosen per line | It is chosen per message (section 3, step 3) |
| With `\|`, an empty piece (`\|\|`) is a field without `=` | The first `\|` is part of the value |
| With `\|`, a piece without `=` is `field_without_equals` | It is part of the previous value; the rule then usually fails on `body_length` or `checksum` |
| A FIX 4.2 report with ExecType 1 or 2 is always a Fill | Not when ExecTransType 20 is 1, 2 or 3 |
| A FIX 4.4 report with ExecType G, H or I is `ExecutionReport (ExecType X)` | TradeCorrect, TradeCancel, OrderStatus |
| 35=F, G and 9 add no event | CancelRequest, ReplaceRequest, CancelReject |
| The page has two sections, with paragraphs for the timeline | Section 8.2 |
| Errors are listed apart from the messages | Error cards in log order |
