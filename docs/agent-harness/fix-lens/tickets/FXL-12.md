+++
key = "FXL-12"
title = "Trading summary: buys and sells per symbol, after trade cancels and corrections"
rank = 12
blocked_by = ["FXL-10"]
labels = []
+++
Add `src/summary.js`, following technical design section 13 (v1.2), steps 1 and 2: `tradeSummary(decoded, shown)`
returns `{ rows, unmatched }`. It is pure and has no DOM access. `decoded` is the whole `decoded` list of
`analyse()`. `shown` is a `Set` of message numbers, or `undefined` for all messages. It uses `executionKind` from
`src/execution.js` to tell a Fill from a TradeCancel and a TradeCorrect. The figures' formatting and the table on
the page are a later ticket.

No existing test file is expected to change. Add `test/summary.test.js`.

The three logs below are the reference. Each line is one valid message, numbered in log order; build each with
the test helper, adding 49, 56 and 34. The expected values were computed independently of the code.

**Log A (FIX.4.4):**
```
 1  35=D 11=C1 1=ACC1 55=VOD.L 54=1 38=1000
 2  35=8 37=O1 11=C1 17=E1 150=F 55=VOD.L 54=1 32=400 31=71.25
 3  35=8 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5
 4  35=8 43=Y 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5
 5  35=8 37=O1 11=C1 17=E3 19=E1 150=G 55=VOD.L 54=1 32=300 31=71.2
 6  35=8 37=O1 11=C1 17=E4 19=E2 150=H 55=VOD.L 54=1 32=0 31=0
 7  35=D 11=C2 1=ACC2 55=VOD.L 54=2 38=500
 8  35=8 37=O2 11=C2 17=E5 150=F 55=VOD.L 54=2 32=200 31=72
 9  35=8 37=O2 11=C2 17=E6 19=E5 150=G 55=VOD.L 54=2 32=250 31=72.1
10  35=8 37=O2 11=C2 17=E7 19=E6 150=G 55=VOD.L 54=2 32=260 31=72.2
11  35=8 37=O9 11=C9 17=E8 19=ZZ 150=H 55=VOD.L 54=1 32=0
12  35=8 37=O8 11=C3 17=E9 19=YY 150=G 55=BARC.L 54=5 32=50 31=2.5
13  35=D 11=C3 1=ACC1 55=BARC.L 54=5 38=50
14  35=8 37=O3 11=C4 17=E10 150=F 55=AZN.L 54=1 32=10
15  35=8 37=O3 11=C4 17=E11 150=F 55=AZN.L 54=8 32=10 31=100
16  35=8 37=O3 11=C4 17=E12 150=F 54=1 32=10 31=100
17  35=8 37=O3 11=C4 17=E13 150=F 55=AZN.L 54=1 32=0 31=100
18  35=8 37=O1 11=C1 17=E14 19=E2 150=G 55=VOD.L 54=1 32=999 31=1
19  35=8 37=O3 11=C4 17=E15 150=0 55=AZN.L 54=1 32=5 31=100
```

**Log B (FIX.4.4):**
```
 1  35=8 37=O1 11=C1 17=E1 150=F 55=VOD.L 54=1 32=100 31=10
 2  35=8 37=O1 11=C1 17=E2 19=E1 150=G 55=VOD.L 54=1 32=120 31=10.5
 3  35=8 37=O1 11=C1 17=E3 19=E2 150=H 55=VOD.L 54=1
```

**Log C (FIX.4.2):**
```
 1  35=8 37=O1 11=C1 17=X1 20=0 150=2 39=2 55=IBM 54=1 32=100 31=50
 2  35=8 37=O1 11=C1 17=X2 19=X1 20=1 150=2 39=2 55=IBM 54=1 32=100 31=50
 3  35=8 37=O1 11=C1 17=X3 150=1 39=1 55=IBM 54=1 32=40 31=51
 4  35=8 37=O1 11=C1 17=X4 19=X3 20=2 150=1 39=1 55=IBM 54=1 32=45 31=51.5
 5  35=8 37=O1 11=C1 17=0 20=3 150=2 39=1 55=IBM 54=1 32=45 31=51.5
```

Acceptance criteria
- AC0: A test imports `tradeSummary` from `src/summary.js` and calls `tradeSummary(analyse(text).decoded)`. The
  result has exactly the keys `rows` and `unmatched`. A row has exactly `symbol`, `buy` and `sell`, and each side
  has exactly `orders`, `orderedQty`, `fills`, `filledQty`, `notional` and `pricedQty`, all numbers.
- AC1: For log A, `unmatched` is 2 and the rows are, in this order (numbers compared to 6 decimal places):
  - `AZN.L`: buy `{ orders: 0, orderedQty: 0, fills: 1, filledQty: 10, notional: 0, pricedQty: 0 }`; sell all zero;
  - `BARC.L`: buy all zero; sell `{ orders: 1, orderedQty: 50, fills: 1, filledQty: 50, notional: 125, pricedQty: 50 }`;
  - `VOD.L`: buy `{ orders: 1, orderedQty: 1000, fills: 1, filledQty: 300, notional: 21360, pricedQty: 300 }`;
    sell `{ orders: 1, orderedQty: 500, fills: 1, filledQty: 260, notional: 18772, pricedQty: 260 }`.
- AC2: What log A shows, each of which a test names:
  - message 4 repeats ExecID E2 for the same OrderID and is not counted again;
  - message 5 corrects E1 to 300 at 71.2, and message 6 cancels E2;
  - message 10 corrects through the ExecID of the earlier correction (E6), so the sell execution is 260 at 72.2;
  - messages 11 and 12 name executions that are not in the log: both are unmatched, the correction (12) counts
    as an execution with its own values, and the cancel (11) changes nothing;
  - message 14 has no LastPx: its quantity counts, and it is left out of `notional` and `pricedQty`;
  - messages 15 (Side 8), 16 (no Symbol) and 17 (LastQty 0) make no execution, and 19 is not a Fill;
  - message 18 corrects an execution that was already cancelled: nothing changes, and it is not unmatched.
- AC3: For log B the cancel names the ExecID of the correction, the execution is removed, and the result is
  `{ rows: [], unmatched: 0 }`.
- AC4: For log C (FIX 4.2), `unmatched` is 0 and the only row is `IBM` with buy
  `{ orders: 0, orderedQty: 0, fills: 1, filledQty: 45, notional: 2317.5, pricedQty: 45 }` and sell all zero.
  Message 2 (20=1) cancels X1, message 4 (20=2) corrects X3, and message 5 (20=3) is an order status and counts
  for nothing.
- AC5: `shown` limits what is counted, not what is computed. For log A with `shown` holding every number except 2:
  `VOD.L` buy is `{ orders: 1, orderedQty: 1000, fills: 0, filledQty: 0, notional: 0, pricedQty: 0 }`, because
  the corrected execution keeps the number of its original Fill, and the other rows and `unmatched` are as in
  AC1. With `shown` holding 7 to 12: `unmatched` is 2, the rows are `BARC.L` (sell
  `{ orders: 0, orderedQty: 0, fills: 1, filledQty: 50, notional: 125, pricedQty: 50 }`) and `VOD.L` (buy all
  zero, sell as in AC1), and there is no `AZN.L` row.
- AC6: Side 1 and 3 are buys; 2, 4, 5 and 6 are sells; any other side, or no Symbol, is not counted, for
  executions and for orders alike.
- AC7: A Fill that makes no execution (no Symbol, another side) is not remembered: a later TradeCancel that names
  its ExecID is unmatched.
- AC8: A report with no ExecID 17 is never matched and never treated as a resend: two identical Fills without
  tag 17 are two executions.
- AC9: Messages of an unsupported version count for nothing: their ExecutionReports make no execution and their
  NewOrderSingles are not counted as orders.
- AC10: Rows are sorted by symbol with plain string comparison: `Zeta` comes before `alpha`.
- AC11: A TradeCorrect that names an execution in the log, but whose own LastQty 32 is not a finite number above
  zero, changes nothing and is not unmatched. No figure in the result is ever `NaN`.
- AC12: An unmatched report is remembered by its OrderID and ExecID: a resend of an unmatched TradeCancel, or of
  an unmatched TradeCorrect, is not counted again in `unmatched`.
- AC13: An empty value counts as a missing tag for Symbol 55, ExecID 17 and ExecRefID 19: `55=` makes no
  execution and no order, and two Fills with `17=` are two executions.
- AC14: `tradeSummary` does not change its arguments. For 1,000 valid order messages it finishes in under 1
  second.
