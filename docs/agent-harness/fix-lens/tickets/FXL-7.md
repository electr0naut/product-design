+++
key = "FXL-7"
title = "The page: input, Decode, two sections, safe output and no-retention checks"
rank = 7
blocked_by = ["FXL-2", "FXL-4", "FXL-5", "FXL-6"]
labels = ["security"]
+++
Following technical design sections 1, 2, 4 and 8. Add `src/analyse.js` (limits first, then framing, checks,
decode and timeline, as `{ ok, limit, messages, errors, decoded, timeline }`), add `index.html`, `src/render.js` and `src/main.js`, and add
`test/static-checks.test.js`.

Acceptance criteria
- AC1: `index.html` has, first in `<head>`, exactly one CSP meta tag with exactly `default-src 'self'; connect-src
  'none'; form-action 'none'`, a `<textarea autocomplete="off" spellcheck="false" autocapitalize="off"
  autocorrect="off" translate="no">`, a Decode button, and separate "Decode" and "Timeline" sections; it loads
  `src/main.js` as a module and `styles.css` as a stylesheet, with no inline script, inline style or `style=`
  attribute.
- AC2: `analyse()` on a log over a limit returns `ok: false`, the limit details and empty lists, and decodes
  nothing.
- AC3: `analyse()` on a log with valid messages around a malformed one decodes the valid ones, lists them in the
  timeline, and gives one error for the malformed one, which adds no event and no decode.
- AC4: `render.js` (tested with the jsdom environment) shows one card per message labelled as in FXL-4, one row
  per field, the errors, the size warning when the limit is hit (and nothing else), and the timeline in its own
  section.
- AC5: Pasted text containing `<img src=x onerror=alert(1)>` in a field value appears as literal text in the
  output and creates no element.
- AC6: `test/static-checks.test.js` strips comments, matches whole words, and fails if `index.html` or any
  `src/**/*.js` contains any API listed in technical design section 8, or if the CSP check there fails; a test
  shows it catches `window.fetch (`, `console .log` and a second CSP meta tag, and ignores the words in a
  comment. It passes on the delivered code.
- AC7: Clicking Decode a second time replaces the previous output; nothing from the paste is written anywhere
  except the two sections.
