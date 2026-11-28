+++
key = "FXL-20"
title = "Paging module: which messages are on a page, and the page line"
rank = 20
blocked_by = []
labels = []
+++
Add `src/paging.js`, following technical design section 16 (v1.3): `PAGE_SIZE`, `pageOf(entries, page)` and
`pageLabel(info, narrowed)`. The module is pure: it imports nothing, has no DOM access and keeps no state.
`entries` is any array; the module never looks inside an entry. Nothing on the page changes in this ticket:
FXL-21 uses the module from `src/render.js`.

No existing file is expected to change. Add `src/paging.js` and `test/paging.test.js`.

The source rules of technical design section 8.4 apply to every file under `src/`: no assignment to `.id`,
`.name`, `.title`, `.src`, `.value`, `.style` or `.cssText`, no `setAttribute`, no `import(`. Build objects
with literals. `test/static-checks.test.js` enforces this.

Acceptance criteria
- AC0: A test imports `PAGE_SIZE`, `pageOf` and `pageLabel` from `src/paging.js`. `PAGE_SIZE` is `200`.
  `pageOf(entries, page)` returns an object with exactly the keys `page`, `pages`, `from`, `to`, `total` and
  `items`.
- AC1: `total` is `entries.length`, and `pages` is `Math.max(1, Math.ceil(total / PAGE_SIZE))`: 1 entry gives 1
  page, 200 give 1, 201 give 2, 400 give 2, 401 give 3 and 10,000 give 50.
- AC2: `items` holds the entries of the page, the same objects in the same order, and `from` and `to` are the
  positions of its first and last entry, counted from 1. For 450 entries: page 1 is entries 1 to 200, page 2 is
  entries 201 to 400, and page 3 is entries 401 to 450 with 50 items. For 201 entries, page 2 has one item and
  `from` and `to` are both 201.
- AC3: `page` in the result is the requested page made valid. A value that is not an integer number becomes 1:
  `undefined`, `null`, `NaN`, `1.5`, `Infinity` and the string `"2"` all give page 1 (`Number.isInteger` decides).
  An integer below 1 becomes 1. An integer above `pages` becomes `pages`: page 99 of 450 entries gives page 3,
  with `from` 401 and `to` 450.
- AC4: With no entries the result is `{ page: 1, pages: 1, from: 0, to: 0, total: 0, items: [] }`, whatever page
  is asked for.
- AC5: `pageOf` never changes `entries`: it works on a frozen array, and after the call the array holds the same
  entries in the same order. `items` is a new array, never `entries` itself.
- AC6: `pageLabel(info, narrowed)` returns `Messages <from> to <to> of <total>`, and adds ` shown` when
  `narrowed` is `true`. It reads only `from`, `to` and `total` of `info`. With `narrowed` `false` or left out,
  nothing is added.
- AC7: The three numbers are written with a comma between thousands, and the result is the same whatever the
  language of the browser (a bare `toLocaleString()` is not enough). `{ from: 201, to: 400, total: 10000 }`
  gives `Messages 201 to 400 of 10,000`; `{ from: 1, to: 200, total: 1240 }` with `narrowed` true gives
  `Messages 1 to 200 of 1,240 shown`; `{ from: 9801, to: 10000, total: 10000 }` gives `Messages 9,801 to 10,000
  of 10,000`; `{ from: 1, to: 200, total: 999 }` gives `Messages 1 to 200 of 999`; and
  `{ from: 0, to: 0, total: 0 }` gives `Messages 0 to 0 of 0`.
