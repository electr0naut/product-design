# FXL-9: the 70 trial survivors, classified by behaviour

Input: `FXL-9-trial-survivors.md` (the agent's trial run). Method, run in the reviewing session: each mutant is
applied to a copy of the landed `src/framing.js` (`60b1211`), and the mutated and the landed code are compared on
12,015 generated pastes (all four delimiter forms, delimiter characters and `8=FIX` inside values, bad tags, wrong
lengths and checksums, cut-off messages, mixed line ends). `splitMessages` and `checkMessage` results are compared in
full. A mutant that differs on at least one paste changes behaviour. Those were then run against the hidden
framing, delimiter, check, analyse, limits, decode and timeline tests.

| group | count |
|---|---|
| changes behaviour, and **neither** the project's tests **nor** the hidden suite notices | **28** |
| changes behaviour, the project's tests miss it, the hidden suite catches it | 7 |
| no difference on any generated paste (equivalent, or beyond my generator) | 35 |

## Changes behaviour, caught by nothing: 28

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 9 | 23 | `/^[1-9][0-9]{0,8}$/` | `/^[1-9][0-9]{0,8}/` | 2538 |
| 10 | 29 | `/^10=[0-9]{3}$/` | `/^10=[0-9]{3}/` | 600 |
| 14 | 37 | `-1` | `+1` | 1507 |
| 23 | 67 | `i + 2 <= limit` | `i + 2 < limit` | 1 |
| 24 | 82 | `i + 5 <= limit` | `i + 5 < limit` | 1 |
| 32 | 98 | `i > start && i < limit && text[i] === "="` | `i > start && i < limit \|\| text[i] === "="` | 5936 |
| 32 | 100 | `i > start && i < limit` | `i > start \|\| i < limit` | 5978 |
| 32 | 107 | `text[i] === "="` | `true` | 5936 |
| 37 | 113 | `end < limit` | `end <= limit` | 1597 |
| 41 | 143 | `next === limit` | `false` | 515 |
| 68 | 179 | `next === end && position < limit && isLineEnd(text[position])` | `false` | 1719 |
| 68 | 180 | `next === end && position < limit && isLineEnd(text[position])` | `next === end && position < limit \|\| isLineEnd(text[position])` | 4387 |
| 68 | 181 | `next === end && position < limit` | `true` | 4387 |
| 68 | 182 | `next === end && position < limit` | `next === end \|\| position < limit` | 4518 |
| 68 | 183 | `next === end` | `true` | 4387 |
| 68 | 184 | `next === end` | `next !== end` | 5593 |
| 79 | 208 | `typeof text !== "string" \|\| text.length === 0` | `false` | 2 |
| 79 | 209 | `typeof text !== "string" \|\| text.length === 0` | `typeof text !== "string" && text.length === 0` | 2 |
| 79 | 210 | `typeof text !== "string"` | `false` | 2 |
| 86 | 222 | `equals !== -1 && isTag(tag)` | `true` | 4529 |
| 86 | 224 | `equals !== -1 && isTag(tag)` | `equals !== -1 \|\| isTag(tag)` | 4529 |
| 114 | 253 | `"header order wrong"` | `""` | 3782 |
| 115 | 256 | `!delim \|\| pieces.length < 3` | `!delim && pieces.length < 3` | 2284 |
| 115 | 258 | `pieces.length < 3` | `false` | 2284 |
| 116 | 263 | `"9="` | `""` | 554 |
| 116 | 264 | `"35="` | `""` | 86 |
| 126 | 285 | `!/^[0-9]+$/.test(lengthValue)` | `false` | 992 |
| 144 | 318 | `"CheckSum mismatch"` | `""` | 45 |

## Changes behaviour, caught by the hidden suite only: 7

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 9 | 22 | `/^[1-9][0-9]{0,8}$/` | `/[1-9][0-9]{0,8}$/` | 2624 |
| 23 | 71 | `"^A"` | `""` | 44 |
| 24 | 86 | `"<SOH>"` | `""` | 1 |
| 116 | 261 | `["8=", "9=", "35="]` | `[]` | 640 |
| 117 | 267 | `!pieces[i].field.startsWith(tag)` | `false` | 640 |
| 121 | 276 | `"missing CheckSum (tag 10)"` | `""` | 4946 |
| 122 | 279 | `!isChecksum(checksum.field)` | `false` | 515 |

## No observable difference: 35

| line | id | replaces | with | pastes that differ |
|---|---|---|---|---|
| 14 | 35 | `start !== -1` | `true` | 0 |
| 21 | 45 | `i < limit` | `i <= limit` | 0 |
| 23 | 60 | `text[i] === "^" && i + 2 <= limit && text.startsWith("^A", i)` | `text[i] === "^" && i + 2 <= limit \|\| text.startsWith("^A", i)` | 0 |
| 23 | 61 | `text[i] === "^" && i + 2 <= limit` | `true` | 0 |
| 23 | 62 | `text[i] === "^" && i + 2 <= limit` | `text[i] === "^" \|\| i + 2 <= limit` | 0 |
| 23 | 63 | `text[i] === "^"` | `true` | 0 |
| 23 | 66 | `i + 2 <= limit` | `true` | 0 |
| 23 | 69 | `i + 2` | `i - 2` | 0 |
| 24 | 75 | `text[i] === "<" && i + 5 <= limit && text.startsWith("<SOH>", i)` | `text[i] === "<" && i + 5 <= limit \|\| text.startsWith("<SOH>", i)` | 0 |
| 24 | 76 | `text[i] === "<" && i + 5 <= limit` | `true` | 0 |
| 24 | 77 | `text[i] === "<" && i + 5 <= limit` | `text[i] === "<" \|\| i + 5 <= limit` | 0 |
| 24 | 78 | `text[i] === "<"` | `true` | 0 |
| 24 | 81 | `i + 5 <= limit` | `true` | 0 |
| 24 | 84 | `i + 5` | `i - 5` | 0 |
| 26 | 88 | `""` | `"Stryker was here!"` | 0 |
| 31 | 92 | `i < limit` | `true` | 0 |
| 31 | 93 | `i < limit` | `i <= limit` | 0 |
| 32 | 99 | `i > start && i < limit` | `true` | 0 |
| 32 | 101 | `i > start` | `true` | 0 |
| 32 | 102 | `i > start` | `i >= start` | 0 |
| 32 | 104 | `i < limit` | `true` | 0 |
| 32 | 105 | `i < limit` | `i <= limit` | 0 |
| 38 | 121 | `!delim \|\| text[end] !== delim[0]` | `!delim && text[end] !== delim[0]` | 0 |
| 38 | 123 | `text[end] !== delim[0]` | `false` | 0 |
| 40 | 129 | `next > limit` | `false` | 0 |
| 42 | 147 | `end - position === 6` | `true` | 0 |
| 64 | 172 | `next > end` | `true` | 0 |
| 64 | 174 | `next > end` | `next >= end` | 0 |
| 79 | 213 | `text.length === 0` | `false` | 0 |
| 86 | 225 | `equals !== -1` | `true` | 0 |
| 107 | 244 | `"field without '='"` | `""` | 0 |
| 116 | 262 | `"8="` | `""` | 0 |
| 126 | 286 | `/^[0-9]+$/` | `/[0-9]+$/` | 0 |
| 126 | 287 | `/^[0-9]+$/` | `/^[0-9]+/` | 0 |
| 137 | 304 | `separated` | `true` | 0 |
