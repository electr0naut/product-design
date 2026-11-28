# Dependency audit notes

Checked 2026-11-21 against the committed `package-lock.json`.

## nanoid "DoS via infinite loop"

- Installed: `nanoid` 3.3.20, a single transitive copy
  (`@tailwindcss/postcss` → `postcss` → `nanoid`). There is no direct dependency.
- CVE-2026-67213 (zero size in `customAlphabet`/`customRandom`) affects
  3.0.0–3.3.17 and 5.0.0–5.1.6; 3.3.20 is outside the range.
- CVE-2026-67214 (negative size in `nanoid/non-secure`) affects versions below
  3.3.16 and 4.0.0–5.1.16; 3.3.20 is outside the range.
- `npm audit` reports 0 vulnerabilities across 430 dependencies at this commit.

No dependency change is required. Re-run `npm audit` after any lockfile update;
the 3.3.x line is already at its latest published version (3.3.20).
