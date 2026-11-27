# FXL-9 trial: `src/framing.js` mutants that were not killed (D23-review)

**From my trial run, not the official rerun:** the D22 code on FXL-9's landed range `e721f31..60b1211`, with `test/static-checks.test.js` left out, in a throwaway container. A list only: **I have not applied any of these by hand or judged which are equivalent.**
Totals for the file, changed lines only: killed 187, **survived 72 (70 not static, listed here; 2 static: lines 2 and 4)**, **without tests 25**, **timeout 32**.

Columns: "replaces" is the exact text the mutant replaces (from its line and column range), "with" is Stryker's replacement. A range over several lines is shown with ⏎. "tests" is the number of covering tests. Each source line is printed once, above its table.

## Survived, not static: 70

**Line 9** (2): `const isTag = tag => /^[1-9][0-9]{0,8}$/.test(tag);`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 22 | Regex | `/^[1-9][0-9]{0,8}$/` | `/[1-9][0-9]{0,8}$/` | 99 |
| 23 | Regex | `/^[1-9][0-9]{0,8}$/` | `/^[1-9][0-9]{0,8}/` | 99 |

**Line 10** (1): `const isChecksum = field => /^10=[0-9]{3}$/.test(field);`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 29 | Regex | `/^10=[0-9]{3}$/` | `/^10=[0-9]{3}/` | 101 |

**Line 14** (2): `while (start !== -1 && isDigitAt(text, start - 1)) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 35 | ConditionalExpression | `start !== -1` | `true` | 99 |
| 37 | UnaryOperator | `-1` | `+1` | 99 |

**Line 21** (1): `for (let i = start; i < limit && !isLineEnd(text[i]); i++) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 45 | EqualityOperator | `i < limit` | `i <= limit` | 101 |

**Line 23** (8): `if (text[i] === "^" && i + 2 <= limit && text.startsWith("^A", i)) return "^A";`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 60 | LogicalOperator | `text[i] === "^" && i + 2 <= limit && text.startsWith("^A", i)` | `text[i] === "^" && i + 2 <= limit \|\| text.startsWith("^A", i)` | 101 |
| 61 | ConditionalExpression | `text[i] === "^" && i + 2 <= limit` | `true` | 101 |
| 62 | LogicalOperator | `text[i] === "^" && i + 2 <= limit` | `text[i] === "^" \|\| i + 2 <= limit` | 101 |
| 63 | ConditionalExpression | `text[i] === "^"` | `true` | 101 |
| 66 | ConditionalExpression | `i + 2 <= limit` | `true` | 15 |
| 67 | EqualityOperator | `i + 2 <= limit` | `i + 2 < limit` | 15 |
| 69 | ArithmeticOperator | `i + 2` | `i - 2` | 15 |
| 71 | StringLiteral | `"^A"` | `""` | 15 |

**Line 24** (8): `if (text[i] === "<" && i + 5 <= limit && text.startsWith("<SOH>", i)) return "<SOH>";`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 75 | LogicalOperator | `text[i] === "<" && i + 5 <= limit && text.startsWith("<SOH>", i)` | `text[i] === "<" && i + 5 <= limit \|\| text.startsWith("<SOH>", i)` | 101 |
| 76 | ConditionalExpression | `text[i] === "<" && i + 5 <= limit` | `true` | 101 |
| 77 | LogicalOperator | `text[i] === "<" && i + 5 <= limit` | `text[i] === "<" \|\| i + 5 <= limit` | 101 |
| 78 | ConditionalExpression | `text[i] === "<"` | `true` | 101 |
| 81 | ConditionalExpression | `i + 5 <= limit` | `true` | 7 |
| 82 | EqualityOperator | `i + 5 <= limit` | `i + 5 < limit` | 7 |
| 84 | ArithmeticOperator | `i + 5` | `i - 5` | 7 |
| 86 | StringLiteral | `"<SOH>"` | `""` | 7 |

**Line 26** (1): `return "";`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 88 | StringLiteral | `""` | `"Stryker was here!"` | 2 |

**Line 31** (2): `while (i < limit && isDigitAt(text, i)) i++;`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 92 | ConditionalExpression | `i < limit` | `true` | 96 |
| 93 | EqualityOperator | `i < limit` | `i <= limit` | 96 |

**Line 32** (8): `return i > start && i < limit && text[i] === "=";`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 98 | LogicalOperator | `i > start && i < limit && text[i] === "="` | `i > start && i < limit \|\| text[i] === "="` | 96 |
| 99 | ConditionalExpression | `i > start && i < limit` | `true` | 96 |
| 100 | LogicalOperator | `i > start && i < limit` | `i > start \|\| i < limit` | 96 |
| 101 | ConditionalExpression | `i > start` | `true` | 96 |
| 102 | EqualityOperator | `i > start` | `i >= start` | 96 |
| 104 | ConditionalExpression | `i < limit` | `true` | 96 |
| 105 | EqualityOperator | `i < limit` | `i <= limit` | 96 |
| 107 | ConditionalExpression | `text[i] === "="` | `true` | 96 |

**Line 37** (1): `for (; end < limit && !isLineEnd(text[end]); end++) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 113 | EqualityOperator | `end < limit` | `end <= limit` | 101 |

**Line 38** (2): `if (!delim || text[end] !== delim[0] || !text.startsWith(delim, end)) continue;`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 121 | LogicalOperator | `!delim \|\| text[end] !== delim[0]` | `!delim && text[end] !== delim[0]` | 101 |
| 123 | ConditionalExpression | `text[end] !== delim[0]` | `false` | 100 |

**Line 40** (1): `if (next > limit) continue;`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 129 | ConditionalExpression | `next > limit` | `false` | 100 |

**Line 41** (1): `if (delim === SOH || next === limit || isLineEnd(text[next]) ||`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 143 | ConditionalExpression | `next === limit` | `false` | 96 |

**Line 42** (1): `(end - position === 6 && isChecksum(text.slice(position, end))) ||`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 147 | ConditionalExpression | `end - position === 6` | `true` | 96 |

**Line 64** (2): `pieces.push({ field, equals, position, separated: next > end });`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 172 | ConditionalExpression | `next > end` | `true` | 101 |
| 174 | EqualityOperator | `next > end` | `next >= end` | 101 |

**Line 68** (6): `if (next === end && position < limit && isLineEnd(text[position])) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 179 | ConditionalExpression | `next === end && position < limit && isLineEnd(text[position])` | `false` | 99 |
| 180 | LogicalOperator | `next === end && position < limit && isLineEnd(text[position])` | `next === end && position < limit \|\| isLineEnd(text[position])` | 99 |
| 181 | ConditionalExpression | `next === end && position < limit` | `true` | 99 |
| 182 | LogicalOperator | `next === end && position < limit` | `next === end \|\| position < limit` | 99 |
| 183 | ConditionalExpression | `next === end` | `true` | 99 |
| 184 | EqualityOperator | `next === end` | `next !== end` | 99 |

**Line 79** (4): `if (typeof text !== "string" || text.length === 0) return [];`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 208 | ConditionalExpression | `typeof text !== "string" \|\| text.length === 0` | `false` | 99 |
| 209 | LogicalOperator | `typeof text !== "string" \|\| text.length === 0` | `typeof text !== "string" && text.length === 0` | 99 |
| 210 | ConditionalExpression | `typeof text !== "string"` | `false` | 99 |
| 213 | ConditionalExpression | `text.length === 0` | `false` | 99 |

**Line 86** (3): `if (equals !== -1 && isTag(tag)) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 222 | ConditionalExpression | `equals !== -1 && isTag(tag)` | `true` | 95 |
| 224 | LogicalOperator | `equals !== -1 && isTag(tag)` | `equals !== -1 \|\| isTag(tag)` | 95 |
| 225 | ConditionalExpression | `equals !== -1` | `true` | 95 |

**Line 107** (1): `if (equals === -1) return error("field_without_equals", position, "field without '='");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 244 | StringLiteral | `"field without '='"` | `""` | 3 |

**Line 114** (1): `const headerError = offset => error("header_order", offset, "header order wrong");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 253 | StringLiteral | `"header order wrong"` | `""` | 1 |

**Line 115** (2): `if (!delim || pieces.length < 3) return headerError(start);`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 256 | LogicalOperator | `!delim \|\| pieces.length < 3` | `!delim && pieces.length < 3` | 41 |
| 258 | ConditionalExpression | `pieces.length < 3` | `false` | 41 |

**Line 116** (4): `for (const [i, tag] of ["8=", "9=", "35="].entries()) {`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 261 | ArrayDeclaration | `["8=", "9=", "35="]` | `[]` | 41 |
| 262 | StringLiteral | `"8="` | `""` | 41 |
| 263 | StringLiteral | `"9="` | `""` | 41 |
| 264 | StringLiteral | `"35="` | `""` | 41 |

**Line 117** (1): `if (!pieces[i].field.startsWith(tag)) return headerError(pieces[i].position);`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 267 | ConditionalExpression | `!pieces[i].field.startsWith(tag)` | `false` | 41 |

**Line 121** (1): `if (!checksum.field.startsWith("10=")) return error("missing_checksum", end, "missing CheckSum (tag 10)");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 276 | StringLiteral | `"missing CheckSum (tag 10)"` | `""` | 3 |

**Line 122** (1): `if (!isChecksum(checksum.field)) return error("checksum_format", checksum.position, "CheckSum format wrong");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 279 | ConditionalExpression | `!isChecksum(checksum.field)` | `false` | 38 |

**Line 126** (3): `if (!/^[0-9]+$/.test(lengthValue)) return error("body_length", bodyLength.position, "BodyLength (9) not a number");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 285 | ConditionalExpression | `!/^[0-9]+$/.test(lengthValue)` | `false` | 38 |
| 286 | Regex | `/^[0-9]+$/` | `/[0-9]+$/` | 38 |
| 287 | Regex | `/^[0-9]+$/` | `/^[0-9]+/` | 38 |

**Line 137** (1): `if (separated) sum++;`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 304 | ConditionalExpression | `separated` | `true` | 38 |

**Line 144** (1): `return error("checksum", checksum.position, "CheckSum mismatch");`

| id | mutator | replaces | with | tests |
|---|---|---|---|---|
| 318 | StringLiteral | `"CheckSum mismatch"` | `""` | 6 |

## Without tests (`NoCoverage`): 25
No test ran any of these, so there is no covering test to count (all 0).

**Line 68** (4): `if (next === end && position < limit && isLineEnd(text[position])) {`

| id | mutator | replaces | with |
|---|---|---|---|
| 185 | ConditionalExpression | `position < limit` | `true` |
| 186 | EqualityOperator | `position < limit` | `position <= limit` |
| 187 | EqualityOperator | `position < limit` | `position >= limit` |
| 188 | BlockStatement | `{ ⏎         position += text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit ? 2 : 1; ⏎       }` | `{}` |

**Line 69** (17): `position += text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit ? 2 : 1;`

| id | mutator | replaces | with |
|---|---|---|---|
| 189 | AssignmentOperator | `position += text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit ? 2 : 1` | `position -= text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit ? 2 : 1` |
| 190 | ConditionalExpression | `text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit` | `true` |
| 191 | ConditionalExpression | `text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit` | `false` |
| 192 | LogicalOperator | `text[position] === "\r" && text[position + 1] === "\n" && position + 1 < limit` | `text[position] === "\r" && text[position + 1] === "\n" \|\| position + 1 < limit` |
| 193 | ConditionalExpression | `text[position] === "\r" && text[position + 1] === "\n"` | `true` |
| 194 | LogicalOperator | `text[position] === "\r" && text[position + 1] === "\n"` | `text[position] === "\r" \|\| text[position + 1] === "\n"` |
| 195 | ConditionalExpression | `text[position] === "\r"` | `true` |
| 196 | EqualityOperator | `text[position] === "\r"` | `text[position] !== "\r"` |
| 197 | StringLiteral | `"\r"` | `""` |
| 198 | ConditionalExpression | `text[position + 1] === "\n"` | `true` |
| 199 | EqualityOperator | `text[position + 1] === "\n"` | `text[position + 1] !== "\n"` |
| 200 | ArithmeticOperator | `position + 1` | `position - 1` |
| 201 | StringLiteral | `"\n"` | `""` |
| 202 | ConditionalExpression | `position + 1 < limit` | `true` |
| 203 | EqualityOperator | `position + 1 < limit` | `position + 1 <= limit` |
| 204 | EqualityOperator | `position + 1 < limit` | `position + 1 >= limit` |
| 205 | ArithmeticOperator | `position + 1` | `position - 1` |

**Line 122** (2): `if (!isChecksum(checksum.field)) return error("checksum_format", checksum.position, "CheckSum format wrong");`

| id | mutator | replaces | with |
|---|---|---|---|
| 280 | StringLiteral | `"checksum_format"` | `""` |
| 281 | StringLiteral | `"CheckSum format wrong"` | `""` |

**Line 126** (2): `if (!/^[0-9]+$/.test(lengthValue)) return error("body_length", bodyLength.position, "BodyLength (9) not a number");`

| id | mutator | replaces | with |
|---|---|---|---|
| 290 | StringLiteral | `"body_length"` | `""` |
| 291 | StringLiteral | `"BodyLength (9) not a number"` | `""` |

(static among them: 0)

## Timeout: 32, per line

| line | timeouts | source line |
|---|---|---|
| 4 | 3 | `const isLineEnd = ch => ch === "\n" \|\| ch === "\r";` |
| 13 | 1 | `let start = text.indexOf("8=FIX", from);` |
| 15 | 1 | `start = text.indexOf("8=FIX", start + 1);` |
| 21 | 3 | `for (let i = start; i < limit && !isLineEnd(text[i]); i++) {` |
| 31 | 1 | `while (i < limit && isDigitAt(text, i)) i++;` |
| 37 | 6 | `for (; end < limit && !isLineEnd(text[end]); end++) {` |
| 38 | 2 | `if (!delim \|\| text[end] !== delim[0] \|\| !text.startsWith(delim, end)) continue;` |
| 39 | 1 | `const next = end + delim.length;` |
| 44 | 1 | `return { end, next };` |
| 50 | 1 | `return { end, next: end };` |
| 58 | 6 | `while (position < limit && !isLineEnd(text[position])) {` |
| 60 | 4 | `if (position !== start && text.startsWith("8=FIX", position)) break;` |
| 81 | 2 | `for (let start = findMessageStart(text, 0); start !== -1;) {` |
