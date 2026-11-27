+++
key = "FXL-14"
title = "The presentation: layout, message cards, timeline rows, summary strip and two themes"
rank = 14
blocked_by = ["FXL-9", "FXL-10", "FXL-11"]
labels = ["security"]
+++
Give the page the structure and style of technical design section 8 (v1.2): 8.1 for `index.html`, 8.2 for what
`render` builds, 8.3 for the themes and 8.4 for the source check. This ticket builds everything in 8.2 **except**
the order banner, the trading summary and the filters, and it shows order ids as plain text. Those come in
FXL-15 and FXL-16. The analysis does not change. All v1.1 security rules stay: text through `textContent` only,
no `setAttribute`, no inline script or style, the same CSP.

`index.html`, `styles.css`, `src/render.js`, `src/main.js`, `test/render.test.js`, `test/page.test.js` and
`test/static-checks.test.js` are expected to change in this ticket. The v1.1 render tests describe the old page
and are replaced.

Acceptance criteria
- AC0: A test imports `render` from `src/render.js` and `analyse` from `src/analyse.js`, loads `index.html` into
  jsdom, calls `render(analyse(text))`, and finds `#summary`, `#timeline` and `#decode`.
- AC1: `index.html` has, besides what it had: a `<header>` with the product name and the text `Runs entirely in
  this page. Nothing you paste is sent, stored or logged.`; `<button id="theme-button" type="button">`;
  `<p id="not-started">FIX Lens did not start. Open it through a web server, not as a file from disk.</p>`;
  `<section id="summary">`; and `#timeline` and `#decode` inside an element with class `results`, each starting
  with an `h2` (`Timeline`, `Decode`) that `render` keeps. The textarea, the Decode button, `#summary` and
  `.results` are inside `<main hidden>`, and `#not-started` is outside it, so that the message stands in place
  of the tool until the script runs. The CSP meta tag is unchanged and still first in
  `<head>`.
- AC2: `src/main.js` removes `#not-started` as its first statement, and then shows the tool by setting
  `hidden = false` on the `<main>` element. A test loads `index.html` without running the script and finds the
  message, its text, and the hidden `<main>`.
- AC3: After a decode, `#summary` holds `div.stats` with five `span.stat` elements, in this order: `N messages`
  (valid plus malformed), `N valid`, `N malformed`, `N sequence gaps`, `N orders` (the number of groups from
  `orderGroups`). A count of one is singular: `1 message`, `1 sequence gap`, `1 order`.
- AC4: `#timeline` holds `ol.events` with one `li.event` per event, in order. Each has `span.num` (`#N`),
  `span.time`, `span.badge` (the event name), `span.dir` (`<sender> → <target>`), `span.seq` (`seq N`, or empty
  when 34 is missing) and `span.detail`. When present, the ids follow as `span.id` elements with the texts
  `ClOrdID <11>`, `OrderID <37>` and `OrigClOrdID <41>`, and `span.ref` with `ExecRefID <19>`.
- AC5: Each `li.event` also has exactly one of these classes: `gap` for a SequenceGap; `reject` for SessionReject,
  BusinessReject and CancelReject; otherwise `order` or `session`, the event's kind. The badge text always names
  the event, so no event is told apart by colour alone.
- AC6: `#decode` holds, in log order, one `article.card` per valid message and one `article.card.malformed` per
  malformed message, at its place by message number.
  - A message card has `header.card-head` with `span.num` (`#N`), an `h3` (the label without its `Message N: `
    prefix), `span.dir`, `span.seq` and `span.time`, then `table.fields` with the header cells `Tag`, `Field`,
    `Value`, `Meaning` and one row per field.
  - A malformed card has `span.num`, an `h3` with `Malformed message`, and `p.error-text` with the error's text.
- AC7: `SendingTime` is shown as its time part, the text after the first `-`: `20261126-10:00:01.000` is shown as
  `10:00:01.000`.
- AC8: With no message at all, `#decode` shows `p.empty` with `No FIX messages found in the pasted text.`; with no
  events, `#timeline` shows a `p.empty`. Over a size limit, `#summary` and `#timeline` are empty apart from the
  heading, and `#decode` shows one `p.warning` with the warning text and nothing else.
- AC9: A second `render` replaces the first: nothing of the earlier output remains.
- AC10: Pasted markup stays text. For a message whose tag 58 is `<img src=x onerror=alert(1)>`, the card shows
  that text and the document has no `img` element. `render.js` never calls `setAttribute`, and sets no element
  property other than `textContent`, `className`, `type`, `disabled` and `selectedIndex`. Every `className` it
  sets is built from fixed strings.
- AC11: `styles.css` declares these custom properties on `:root`, again inside
  `@media (prefers-color-scheme: dark) { :root:not(.theme-light) { ... } }`, and again on `:root.theme-dark`, the
  two dark blocks with the same values: `--bg`, `--panel`, `--ink`, `--muted`, `--line`, `--soft`, `--accent`,
  `--accent-ink`, `--ok`, `--warn`, `--warn-bg`, `--bad`, `--bad-bg`, `--order`, `--order-bg`, `--session-bg`.
  Each value is a six-digit hex colour (`#rrggbb`). Every colour in the stylesheet is one of these properties:
  outside the three blocks there is no hex colour and no `rgb(`, `rgba(`, `hsl(` or `hsla(`.
- AC12: A test reads the three blocks and computes WCAG 2.1 contrast. Each of these pairs is at least 4.5 to 1 in
  the light and in the dark values: `--ink` on `--bg`, `--ink` on `--panel`, `--muted` on `--panel`, `--muted` on
  `--bg`, `--accent-ink` on `--accent`, `--ok` on `--panel`, `--warn` on `--warn-bg`, `--bad` on `--bad-bg`,
  `--order` on `--order-bg`, `--ink` on `--session-bg`.
- AC13: `#theme-button` sets `document.documentElement.className` to `theme-dark` or `theme-light` and its own
  text to the theme it would switch to (`Light theme` or `Dark theme`). Its first state comes from
  `matchMedia('(prefers-color-scheme: dark)')`. Nothing is stored.
- AC14: `.results` is a two-column grid from `min-width: 900px`, with `#timeline` sticky, and one column below
  that.
- AC15: `test/static-checks.test.js` also fails on: any `import(` call; any import of a path ending `.json`;
  an assignment to `.id`, `.name`, `.title`, `.src`, `.value`, `.style` or `.cssText` in `src/**/*.js`; and, in
  `index.html`, a `<script>` without `src`, a `<style>` element, a `style=` attribute or an `on...=` attribute.
  It checks that `src/dictionary/fix42.js` and `fix44.js` are each exactly `export default `, one JSON value and
  `;`. It passes on the delivered code.
