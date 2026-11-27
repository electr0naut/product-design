# FXL-9: the 70 trial survivors, classified by behaviour (corrected)

**This replaces the first version of this file.** Its numbers (35 behaviour-changing, 28 caught by nothing) came
from a comparison whose random generator was faulty: it almost always chose the first of any list with an even
number of entries, so nearly every generated message used `|`. See `FUZZ-correction.md`. The figures below are
from the corrected generator.

Input: `FXL-9-trial-survivors.md` (the agent's trial run). Method, run in the reviewing session: each mutant is
applied to a copy of the landed `src/framing.js` (`60b1211`), and the mutated and the landed code are compared on
12,015 generated pastes (all four delimiter forms, delimiter characters and `8=FIX` inside values, bad tags, wrong
lengths and checksums, cut-off messages, mixed line ends). A mutant that differs on at least one paste changes
behaviour. Those were then run against the hidden suite as it was, and against it with the new
`acc-framing-rules.test.js` (11 tests).

| group | count |
|---|---|
| changes behaviour | **44** of 70 |
| of those, caught by the hidden suite as it was | 5 |
| of those, caught once `acc-framing-rules.test.js` is added | 23 |
| of those, still caught by nothing | **21** |
| no difference on any generated paste (equivalent, or beyond my generator) | 26 |

Six rows replace a text that occurs more than once on its line; for those I tried each occurrence and used the
first that changes behaviour, so their classification is approximate.

**The 21 still caught by nothing**, by reason:
- lines 68, 79, 86 (12): places the design does not pin (a candidate's `end` after a CheckSum with no delimiter;
  input that is not a string; whether pieces with a bad tag appear in `fields`);
- line 126 (1): only the wording of one problem text changes; the rule and position do not;
- lines 23 and 24 (8): the detection of `^A` and `<SOH>` at the very end of the text, or with a lone `^` or `<`
  before any delimiter. Not pinned by a test; candidates for the follow-up ticket.

## Still caught by nothing: 21

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 23 | 60 | `text[i] === "^" && i + 2 <= limit && text.startsWith("^A", i)` | `text[i] === "^" && i + 2 <= limit \|\| text.startsWith("^A", i)` | 1 |
| 23 | 62 | `text[i] === "^" && i + 2 <= limit` | `text[i] === "^" \|\| i + 2 <= limit` | 1 |
| 23 | 67 | `i + 2 <= limit` | `i + 2 < limit` | 1 |
| 23 | 71 | `"^A"` | `""` | 4558 |
| 24 | 75 | `text[i] === "<" && i + 5 <= limit && text.startsWith("<SOH>", i)` | `text[i] === "<" && i + 5 <= limit \|\| text.startsWith("<SOH>", i)` | 3 |
| 24 | 77 | `text[i] === "<" && i + 5 <= limit` | `text[i] === "<" \|\| i + 5 <= limit` | 3 |
| 24 | 82 | `i + 5 <= limit` | `i + 5 < limit` | 2 |
| 24 | 86 | `"<SOH>"` | `""` | 4627 |
| 68 | 179 | `next === end && position < limit && isLineEnd(text[position])` | `false` | 1931 |
| 68 | 180 | `next === end && position < limit && isLineEnd(text[position])` | `next === end && position < limit \|\| isLineEnd(text[position])` | 7319 |
| 68 | 181 | `next === end && position < limit` | `true` | 7319 |
| 68 | 182 | `next === end && position < limit` | `next === end \|\| position < limit` | 7456 |
| 68 | 183 | `next === end` | `true` | 7319 |
| 68 | 184 | `next === end` | `next !== end` | 8338 |
| 79 | 208 | `typeof text !== "string" \|\| text.length === 0` | `false` | 2 |
| 79 | 209 | `typeof text !== "string" \|\| text.length === 0` | `typeof text !== "string" && text.length === 0` | 2 |
| 79 | 210 | `typeof text !== "string"` | `false` | 2 |
| 86 | 222 | `equals !== -1 && isTag(tag)` | `true` | 6587 |
| 86 | 224 | `equals !== -1 && isTag(tag)` | `equals !== -1 \|\| isTag(tag)` | 6457 |
| 86 | 225 | `equals !== -1` | `true` | 159 |
| 126 | 285 | `!/^[0-9]+$/.test(lengthValue)` | `false` | 492 |

## Caught only by the new hidden tests: 18

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 9 | 23 | `/^[1-9][0-9]{0,8}$/` | `/^[1-9][0-9]{0,8}/` | 2881 |
| 10 | 29 | `/^10=[0-9]{3}$/` | `/^10=[0-9]{3}/` | 764 |
| 14 | 37 | `-1` | `+1` | 1617 |
| 32 | 98 | `i > start && i < limit && text[i] === "="` | `i > start && i < limit \|\| text[i] === "="` | 3980 |
| 32 | 99 | `i > start && i < limit` | `true` | 1589 |
| 32 | 100 | `i > start && i < limit` | `i > start \|\| i < limit` | 4003 |
| 32 | 101 | `i > start` | `true` | 1589 |
| 32 | 102 | `i > start` | `i >= start` | 1589 |
| 32 | 107 | `text[i] === "="` | `true` | 2930 |
| 37 | 113 | `end < limit` | `end <= limit` | 1027 |
| 41 | 143 | `next === limit` | `false` | 140 |
| 107 | 244 | `"field without '='"` | `""` | 654 |
| 114 | 253 | `"header order wrong"` | `""` | 1073 |
| 115 | 256 | `!delim \|\| pieces.length < 3` | `!delim && pieces.length < 3` | 646 |
| 115 | 258 | `pieces.length < 3` | `false` | 646 |
| 116 | 263 | `"9="` | `""` | 197 |
| 116 | 264 | `"35="` | `""` | 7 |
| 144 | 318 | `"CheckSum mismatch"` | `""` | 3836 |

## Caught by the hidden suite as it was: 5

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 9 | 22 | `/^[1-9][0-9]{0,8}$/` | `/[1-9][0-9]{0,8}$/` | 4612 |
| 116 | 261 | `["8=", "9=", "35="]` | `[]` | 204 |
| 117 | 267 | `!pieces[i].field.startsWith(tag)` | `false` | 204 |
| 121 | 276 | `"missing CheckSum (tag 10)"` | `""` | 1610 |
| 122 | 279 | `!isChecksum(checksum.field)` | `false` | 1232 |

## No observable difference: 26

| line | id | replaces | with |
|---|---|---|---|
| 14 | 35 | `start !== -1` | `true` |
| 21 | 45 | `i < limit` | `i <= limit` |
| 23 | 61 | `text[i] === "^" && i + 2 <= limit` | `true` |
| 23 | 63 | `text[i] === "^"` | `true` |
| 23 | 66 | `i + 2 <= limit` | `true` |
| 23 | 69 | `i + 2` | `i - 2` |
| 24 | 76 | `text[i] === "<" && i + 5 <= limit` | `true` |
| 24 | 78 | `text[i] === "<"` | `true` |
| 24 | 81 | `i + 5 <= limit` | `true` |
| 24 | 84 | `i + 5` | `i - 5` |
| 26 | 88 | `""` | `"Stryker was here!"` |
| 31 | 92 | `i < limit` | `true` |
| 31 | 93 | `i < limit` | `i <= limit` |
| 32 | 104 | `i < limit` | `true` |
| 32 | 105 | `i < limit` | `i <= limit` |
| 38 | 121 | `!delim \|\| text[end] !== delim[0]` | `!delim && text[end] !== delim[0]` |
| 38 | 123 | `text[end] !== delim[0]` | `false` |
| 40 | 129 | `next > limit` | `false` |
| 42 | 147 | `end - position === 6` | `true` |
| 64 | 172 | `next > end` | `true` |
| 64 | 174 | `next > end` | `next >= end` |
| 79 | 213 | `text.length === 0` | `false` |
| 116 | 262 | `"8="` | `""` |
| 126 | 286 | `/^[0-9]+$/` | `/[0-9]+$/` |
| 126 | 287 | `/^[0-9]+$/` | `/^[0-9]+/` |
| 137 | 304 | `separated` | `true` |
