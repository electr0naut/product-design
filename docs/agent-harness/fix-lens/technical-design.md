# FIX Lens - Technical Design (copy of Confluence page 1409027, v1.1)

**Version:** 1.1, for PRD v1.1 (Gate 3 approved 2026-11-25). Revised after an independent review against the PRD
and the FIX rules.
**Status:** Approved under delegation from the product owner (2026-11-25), to be confirmed by the owner
**Built by:** the agent delivery harness, as the 7 tickets of the PRD delivery plan

## 1. Shape

FIX Lens is one static page plus plain ES modules. There's no build step for the page itself: the browser loads
`index.html`, which loads `src/main.js` as a module. All logic modules are pure functions with no DOM access
(TR-004), so they're tested with Vitest in Node. Only `src/render.js` and `src/main.js` touch the DOM.

```
index.html              CSP meta tag, textarea, Decode button, two sections (decode, timeline)
src/framing.js          split a paste into messages, parse fields, check framing (TR-002)
src/limits.js           byte and message-count limits (US-004)
src/dictionary/fix42.json, fix44.json   generated, committed (TR-001)
src/dictionary.js       lookup by BeginString, tag and enum value
src/decode.js           field-by-field decode (US-001)
src/timeline.js         session and order events, sequence gaps (US-002, TR-003)
src/analyse.js          one entry point: limits, then framing, then decode and timeline
src/render.js           DOM output with text nodes and textContent only (TR-006)
src/main.js             wires the button to analyse() and render()
tools/build-dictionary.mjs   Orchestra XML to the two JSON files
vendor/orchestra/       OrchestraFIX42.xml, OrchestraFIX44.xml, LICENSE, NOTICE, SOURCE.md (pinned commit)
test/                   Vitest tests, one file per module, plus test/helpers/fix.js
```

## 2. Data model

All positions are **0-based character offsets into the pasted text** (JavaScript string indices), shown to the
user as 1-based.

- **Field:** `{ tag: number, value: string, position: number }`. `position` is where the tag starts.
- **Message:** `{ number, start, end, fields, beginString, msgType }`. `number` is 1-based, in order of
  appearance among all message candidates (valid or malformed). `start` and `end` are offsets in the paste.
- **ParseError:** `{ number, position, rule, text }`. `rule` is one of `field_without_equals`, `bad_tag`,
  `header_order`, `missing_checksum`, `checksum_format`, `body_length`, `checksum`. `text` is the plain-words message (AC-015).
- **DecodedField:** `{ tag, name, value, enumName, known }`. `name` is `"Unknown tag X"` when the tag isn't in
  the dictionary. `enumName` is null for non-enum fields, and `"unknown value"` for an enum value the dictionary
  doesn't list.
- **TimelineEvent:** `{ number, kind, name, sendingTime, sender, target, seqNum, clOrdId, orderId, detail }`.
  `kind` is `session` or `order`.
- **Analysis:** `{ ok, limit, messages, errors, decoded, timeline }`. When a limit is exceeded, `ok` is false,
  `limit` holds the measured size and count, and every other list is empty (AC-018).

## 3. Framing (TR-002)

Positions are offsets into the string given to `analyse()`, counted in JavaScript string units (UTF-16). The
textarea already turns CRLF into LF; `\r\n`, `\n` and `\r` all end a line.

1. **Delimiter per line:** a line that contains SOH (0x01) uses SOH, and any `|` on it is ordinary text. A line
   without SOH uses `|`. Working on a normalised copy where the delimiter is SOH, one character for one
   character, so offsets don't move.
2. **Message start:** outside a message, `8=FIX` starts a candidate at the start of a line, after SOH, or after a
   character that isn't a digit (so `448=FIXCLIENT` never starts one). Text before it on the line is ignored.
   Inside a candidate that hasn't reached its CheckSum, `8=FIX` starts a new candidate only right after SOH.
3. **Message end:** a candidate ends after its CheckSum field: a field that **starts** with `10=` (at a field
   boundary, never inside another field such as `110=` or a text value) followed by 3 digits, then SOH, a line
   end or the end of the text. Failing that, it ends where the next candidate starts, or at the line end.
4. **Fields:** split the candidate on SOH. A trailing empty piece after the final SOH is dropped. An empty piece in
   the middle (`||`) is a field without `=`.
5. **Rules, checked in this order; only the first failure is reported:**
   1. a field without `=`: `field_without_equals`;
   2. a tag that isn't a positive integer (digits only, no leading zero, at most 9 digits): `bad_tag`;
   3. fewer than three fields, or the first three tags aren't 8, 9, 35: `header_order`;
   4. the last field isn't tag 10: `missing_checksum`; tag 10 last but its value isn't exactly 3 digits:
      `checksum_format`;
   5. BodyLength 9 isn't a non-negative integer, or doesn't equal the UTF-8 byte count of the normalised text
      from just after the SOH ending field 9, up to and including the SOH before `10=`: `body_length`;
   6. the sum of the UTF-8 bytes of the normalised text from the message start up to and including the SOH before
      `10=`, modulo 256 and written as 3 digits, isn't the value of tag 10: `checksum`.
6. **Error position:** the 1-based position of the failing field's first character; for `missing_checksum`, the
   candidate's end.
7. **Error text:** always `Message N: <problem> at position P`, for example `Message 5: missing CheckSum (tag 10)
   at position 234` and `Message 2: BodyLength (9) says 112, actual 108 at position 12`.

A malformed candidate is kept as an error only. It isn't decoded and adds no timeline events (AC-013). Every
other candidate goes on normally (AC-014).

## 4. Limits (US-004)

They're checked **before** framing.
- **Size:** `new TextEncoder().encode(paste).length > 1_048_576`.
- **Count:** the number of message candidates (section 3) `> 1_000`.

Over either limit, `analyse()` returns `ok: false` with both measured numbers and nothing else. The warning names
both numbers and suggests splitting the log (AC-016, AC-017).

## 5. Dictionary (TR-001)

- **Source:** `OrchestraFIX42.xml` and `OrchestraFIX44.xml` from github.com/FIXTradingCommunity/orchestrations,
  folder `FIX Standard`.
  - They're **vendored** into `vendor/orchestra/` at one pinned commit, recorded in `SOURCE.md` and as a constant
    in the build script.
  - The repository's `LICENSE` (Apache-2.0) and any `NOTICE` file are copied alongside, **and also into
    `src/dictionary/`** next to the generated files, with a `SOURCE.md` naming the pinned commit (TR-001).
  - Tests and builds never use the network.
- **`tools/build-dictionary.mjs`** reads the XML with a small streaming parser in the script itself, with no
  dependency. It writes `src/dictionary/fix42.json` and `fix44.json`, each in the form
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

## 7. Timeline (US-002, TR-003)

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

   | MsgType | Event |
   |---|---|
   | A | Logon |
   | 5 | Logout |
   | 0 | Heartbeat |
   | 1 | TestRequest |
   | 2 | ResendRequest |
   | 4 | GapFill when 123=Y, otherwise Reset |
   | 3 | SessionReject |
   | j | BusinessReject |
   | D | NewOrder |
   | 8 | from ExecType 150, below |

   ExecutionReport:
   - `0`: Acknowledgement;
   - `1` or `2` on FIX.4.2, or `F` on FIX.4.4: Fill;
   - `4`: Cancelled;
   - `5`: Replaced;
   - anything else: `ExecutionReport (ExecType X)`;
   - no 150: `ExecutionReport (no ExecType)`.

   For an unsupported version only 0, 4 and 5 are mapped. Other MsgTypes add no event.
5. **Event fields:** each event carries the message number, the name, SendingTime 52 when present, 49, 56 and 34
   (blank when missing) (AC-010). Order events also carry ClOrdID 11, and OrderID 37 when present.

## 8. Page and security (TR-004, TR-006, US-005)

- **`index.html`:**
  - has, as the **first element in `<head>`**, `<meta http-equiv="Content-Security-Policy" content="default-src
    'self'; connect-src 'none'; form-action 'none'">` (AC-020). It's the only CSP meta tag;
  - has `<textarea autocomplete="off" spellcheck="false" autocapitalize="off" autocorrect="off"
    translate="no">`. Turning spellcheck off matters: enhanced browser spellcheck can send the text to a service
    (AC-019, AC-020, AC-022);
  - has a Decode button and two sections, "Decode" and "Timeline" (AC-011);
  - loads `src/main.js` as a module and `styles.css` as a stylesheet. There's **no inline script or style and no
    `style=` attribute**, because the CSP blocks them.
- **`render.js`** builds every node with `document.createElement` and sets text with `textContent` only. It sets
  no attributes from pasted data and creates no links.
- **The page must be served over HTTP** (the internal web server, or any static server for local testing).
  Browsers block module scripts from `file://`.
- **The source check** (`test/static-checks.test.js`, AC-023):
  - **What it scans:** `index.html` and `src/**/*.js`, with comments stripped first, matching whole words or
    calls (for example `\bfetch\b`, `\bconsole\s*\.`).
  - **What fails it:**
    - **network or leaving the page:** `fetch`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `EventSource`,
      `window.open`, assignments to `location` or `.href`, `setAttribute(`;
    - **storage:** `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `cookieStore`, `caches`,
      `openDatabase`, `navigator.storage`, `serviceWorker`, `Worker(`, `SharedWorker`;
    - **logging and markup:** `console`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`,
      `DOMParser`, `createContextualFragment`, `setHTMLUnsafe`, `srcdoc`, `eval`, `new Function`.
  - **The CSP check** parses `index.html` and fails unless there is exactly one CSP meta tag, it's first in
    `<head>`, and its content is the exact string above.
  - **What it can't do:** it catches accidental use. It can't stop deliberate evasion such as
    `window['local'+'Storage']`. That's what the review is for.

## 9. Tests and tooling

- **Vitest**, with every test a top-level `test()` call (mutation testing reads them most reliably). Pure modules
  run in Node; `render.js` tests use Vitest's `jsdom` environment for that file only.
- **`test/helpers/fix.js`** builds valid messages from a field list, computing BodyLength and CheckSum, so tests
  never hard-code checksums by hand. Malformed cases are made by changing one thing in a valid message.
- **Performance (AC-006, TR-005):** a test builds 100 valid mixed messages and checks that `analyse()` finishes
  in under 5 seconds. Expect milliseconds.
- **Dev dependencies, all pinned in `package.json` from ticket 1 on:** `vitest`, `jsdom`,
  `@stryker-mutator/core`, `@stryker-mutator/vitest-runner` (10.x). No runtime dependencies.
- **Harness settings:** `[repos.fix-lens]` overlay with the Vitest commands (as `harness.js.toml`), with
  `test_dir = "test/"`. The JS dependencies are installed once into the root-owned dependencies folder.

## 10. Ticket order

The tickets follow the PRD delivery plan (FXL-1 to FXL-7). The harness runs them one at a time, in rank order,
each after its blockers. Each ticket lists its acceptance criteria as testable statements taken from the PRD.

## 11. Decisions the PRD left open

| Topic | Decision |
|---|---|
| Error position | 1-based position (UTF-16 units) in the string given to `analyse()`, of the failing field |
| Several failing rules | Only the first, in the order of section 3 |
| Unsupported BeginString | Labelled `unsupported version <8>`, fields shown raw, in the timeline with only ExecType 0/4/5 mapped |
| Pipe character inside a SOH-delimited line | Ordinary text; the pipe is a delimiter only on lines without SOH |
| Leading-zero or very long tags | `bad_tag` (stricter than "positive integer") |
| CheckSum present but not 3 digits | `checksum_format` |
| MsgSeqNum lower than expected | Ignored: no event, expected number unchanged |
| PossDupFlag on a SequenceReset | PossDupFlag wins: nothing changes |
| Missing 34, 49 or 56 | No sequence check; empty string in the direction key; shown blank |
| Repeated 35 | The first value counts |
| Dictionary source at build time | Vendored XML at a pinned commit; no network |
| CSP delivery | Meta tag, because a static server may not set headers |
