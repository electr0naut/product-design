# Independent FIX Log Analysis Tool: Validation and Stress Testing (scoped to the product)

Ubay Gonzalez's brief of 2026-11-27 (kept whole in `BRIEF-original.md`), cut down to what FIX Lens is meant to
do, on his instruction the same day: "dont include out of scope FIX versions" and "analyse the brief and take
out what is out of scope". Scope is taken from the PRD (`../prd.md`, "Scope", "Out of Scope" and the acceptance
criteria). Section numbers are the original's. What was removed, and why, is listed at the end; **nothing in
that list is to be tested.**

## 1. Role and objective
Act as a senior FIX protocol engineer, electronic trading systems engineer and independent QA specialist with
extensive experience in institutional trading infrastructure, exchange connectivity, order management systems
and post-trade reconciliation.

Your objective is to rigorously test the existing FIX log analysis tool, identify defects, expose incorrect
assumptions and determine its suitability for production use.

Do not assume that the current implementation is correct. Treat its output as untrusted until independently
verified. Your responsibility is to discover failures, not to demonstrate success.

## 2. Initial assessment
Before executing tests:
- Inspect the repository, architecture, source code, documentation, configuration and existing tests.
- Identify all supported FIX versions, log formats and advertised functionality.
- Understand how the tool parses, correlates, validates and presents FIX messages.
- Identify implicit assumptions regarding message direction, session identity, sequence numbers and order
  lifecycles.
- Establish a baseline by running existing tests.
- Record the current Git commit, runtime environment and dependency versions.

Distinguish between advertised functionality, implemented functionality and missing functionality.
Do not modify production source code during the initial testing phase.

## 3. External test data acquisition
Candidate sources of FIX 4.2 and FIX 4.4 logs and of engine-generated traffic. They are not guaranteed valid
or trustworthy: verify availability, licensing, protocol coverage, maintenance status and suitability first.

Existing FIX logs:
- https://github.com/siva-balan/Log-Analyzer/blob/main/sample_fix44.log
- https://github.com/vikram-dhamodaran/fix-log-analyzer/blob/main/sample_log.log
- https://github.com/backstreetbrogrammer/55_FIX_Protocol_Study_Guide
- https://fixtags.dev/

FIX engines and simulators:
- https://github.com/quickfix/quickfix
- https://github.com/quickfix-j/quickfixj
- https://github.com/FIXimulator/FIXimulator
- https://github.com/pigfox/fix-lab
- https://github.com/felipewind/fix-trading-simulator
- https://github.com/abhi-g80/pytradesimulator
- https://github.com/yaalalabs/fixyl

Inspect the QuickFIX and QuickFIX/J acceptance tests, test definitions, sample applications and the FIX 4.2 and
4.4 dictionaries. Search independently for additional public FIX 4.2 and 4.4 session logs and anonymised
datasets.

Record the source URL, repository commit, licence, acquisition date and SHA-256 checksum of every external
dataset. Do not assume publicly available FIX logs are protocol-compliant. Never upload proprietary source
code, credentials or internal FIX logs to external services.

## 4. FIX protocol coverage
Test independently:
- FIX 4.2
- FIX 4.4

Use the machine-readable dictionaries and the official FIX Trading Community specifications as the source of
truth. Respect the differences in enumerations and message semantics between the two versions; do not apply
FIX 4.4 assumptions to FIX 4.2 (ExecTransType and ExecType in particular).

A message with any other BeginString must be reported as an unsupported version for that message: check that
with two or three messages. A tag or an enumerated value that is not in the dictionary (a venue's custom tag,
for example) must be shown raw and labelled as unknown.

## 5. Synthetic data generation
Create an independent, deterministic FIX traffic generator or use established FIX engines to generate
controlled sessions. Prefer at least two independent methods:
1. Actual initiator/acceptor communication through an established FIX engine.
2. Deterministic synthetic message generation for precise edge-case control.

Do not reuse the application under test's parser, serializer or business logic to construct expected results.
Generate both sides of each conversation using fictional counterparties, accounts, instruments and order
identifiers.

For valid wire-format messages, ensure: genuine ASCII SOH delimiters (0x01); correct BodyLength (9); correct
CheckSum (10); correct header and trailer fields; dictionary-compliant field values; independent incoming and
outgoing sequence numbers; coherent timestamps; correct order and execution state transitions.

Calculate BodyLength and CheckSum over the actual encoded bytes, not the pipe-delimited representation. Use
seeded randomness so that every dataset is reproducible. Intentionally invalid messages must be clearly
labelled in a separate ground-truth manifest.

## 6. Session-level testing
Test complete, bidirectional FIX sessions covering:
- Logon (35=A), Logout (35=5), Heartbeat (35=0), Test Request (35=1), Resend Request (35=2), Reject (35=3),
  Sequence Reset (35=4) in gap-fill and reset modes, Business Message Reject (35=j).
- Normal session establishment and termination; reconnections within one log.
- Missing messages (sequence gaps), duplicate sequence numbers, out-of-order messages.
- PossDupFlag (43). ResetSeqNumFlag (141). NewSeqNo (36).
- Sequence numbers across reconnections and resets.
- Multiple sessions using overlapping sequence numbers.
- Multiple sessions using overlapping order identifiers.

Verify that sequence analysis is scoped to the correct direction (SenderCompID and TargetCompID) and reset.
A retransmission must not be interpreted as a new business event.

## 7. Order lifecycle testing
Generate realistic order flows involving multiple clients, brokers, instruments and order types. Cover:
- New Order Single (35=D), Execution Report (35=8), Order Cancel Request (35=F), Order Cancel/Replace Request
  (35=G), Order Cancel Reject (35=9).
- Acknowledgements; execution reports of every other kind (pending new, rejected, expired, pending cancel,
  pending replace and so on), which the tool is meant to show as "ExecutionReport (ExecType X)".
- Single and multiple partial fills; full fills; partial fills followed by cancellation or by amendments;
  multiple consecutive amendments; rejected amendments and cancellations; fills while a cancel or replace is
  pending.
- Trade cancellations and corrections, in FIX 4.2 (ExecTransType) and FIX 4.4 (ExecType) form.
- Duplicate execution reports; late execution reports; execution reports that come before earlier lifecycle
  events in the input.
- ClOrdID values reused across distinct sessions.

Validate what the tool derives from: ClOrdID (11), OrigClOrdID (41), OrderID (37), ExecID (17), ExecRefID (19),
ExecType (150), ExecTransType (20), OrdStatus (39), OrderQty (38), CumQty (14), LastQty / LastShares (32),
LastPx (31), AvgPx (6), Side (54), Symbol (55), Account (1).

Verify that order correlation is appropriately scoped and that amendments preserve the logical order chain.
Check the trading summary per symbol (order counts, bought, sold, average prices, net) with decimal
arithmetic, including after trade cancels and corrections, with the filters and with one order selected. Do
not double-count fills or treat cumulative quantities as incremental fills.

## 8. Repeated tags
The tool does not group repeating groups; it must list repeated tags in order of appearance, without dropping
or overwriting any, and without calling them errors. Check that with messages that carry repeated tags.

## 9. Parsing and log format robustness
Test the same underlying FIX traffic as:
- Raw SOH-delimited FIX; pipe-delimited FIX; the text forms `^A` and `<SOH>`.
- QuickFIX and QuickFIX/J message logs; timestamp-prefixed, direction-prefixed and logger-prefixed lines.
- Mixed FIX and non-FIX application log lines.
- Multiple messages on a single line; multiple concatenated messages; messages spanning multiple lines.
- Windows CRLF and Unix LF; a UTF-8 BOM; empty input and empty lines; truncated input; no trailing newline.

Timeline events must stay in log order: they are never re-sorted by timestamp.

## 10. Malformed and adversarial input
Create dedicated negative-test fixtures containing:
- Incorrect BodyLength; incorrect CheckSum; missing or misordered BeginString, BodyLength or MsgType; missing
  trailer; truncated messages.
- Malformed tag-value pairs (no `=`, a tag that is not a positive integer); unexpected delimiters; embedded
  equals signs in values; a delimiter inside a value.
- Invalid message types; unknown tags; invalid enumerations; duplicate fields.
- Invalid numeric values, extremely large numeric values and negative quantities in the fields the trading
  summary uses.
- Excessively long field values.
- Binary garbage between valid messages; corrupted messages followed by valid traffic.

Verify that the tool: does not crash; does not hang; does not silently discard valid neighbouring messages;
reports malformed data accurately, with its message number, position and the rule that failed; does not mistake
invalid data for valid business activity; recovers parsing where safe; does not consume excessive resources on
hostile input. Distinguish protocol violations from unusual but valid FIX messages.

## 11. Multi-session and real-world scenarios
Construct pasted logs simulating institutional environments:
- Multiple clients connected to multiple venues; interleaved traffic from unrelated sessions.
- FIX 4.2 and FIX 4.4 sessions in the same log.
- The same execution seen twice (a drop copy, or a resend); the same ExecID on different orders.
- Identical SenderCompID and TargetCompID pairs told apart only by SubIDs.
- Sequence resets on one session while others remain active.
- Incomplete logs: a log that starts or ends mid-session, or that lacks the execution a correction names.
- A log merged from both sides of a connection.

Verify that unrelated sessions, orders and executions are not accidentally merged.

## 12. Performance and limits
The tool reads one pasted log of at most 1,000 messages or 1,048,576 bytes. Measure inside those limits:
- 100, 250, 500 and 1,000 messages, with realistic mixes of session messages, orders, executions, amendments
  and cancellations. Do not benchmark only repetitive, trivially parseable messages.
- At each limit: just under, at, and just over.
- Over the limit (10,000 messages, once): the tool must refuse clearly and quickly, with no partial output.
- **10,000 messages is the owner's maximum for now** (2026-11-27). With the limit lifted in a copy of the
  product, measure the logic modules and the page at 2,500, 5,000 and 10,000 messages. Report these as
  information for the planned limit, not as defects of v1.2, which refuses such logs by design.
- Hostile input inside the size limit: one very long message, very long values, very many fields, text built
  to make the framing rules backtrack.

Measure: total time; messages and megabytes per second; peak memory (resident memory for the logic modules
under Node, the JavaScript heap in the browser); initialisation time (page load to ready; first decode against
repeated decodes); time from pressing Decode to the first painted result; filter and order-selection latency;
error-handling overhead (a log with many malformed messages against the same log without them); behaviour as
the number of sessions and orders in the log grows.

Record hardware, OS, runtime, configuration and dataset characteristics. Repeat benchmarks enough to tell
stable results from noise. Investigate non-linear scaling, excessive memory retention, unnecessary copies,
inefficient regular expressions and quadratic algorithms.

Do not invent performance thresholds. Derive proposed acceptance criteria from the tool's requirements (under
5 seconds for 100 messages; under 1 second for each view at 1,000 messages) and the measured baseline.

## 13. Independent ground truth
Every deterministic synthetic dataset must include a machine-readable ground-truth manifest recording:
expected message count; valid and invalid message counts; session identities and directions, and their count;
expected sequence gaps; expected retransmissions; expected session resets; expected order count; logical order
amendment chains; final order states; individual executions; expected filled quantities; expected weighted
average prices; expected rejections and cancellations; expected anomalies.

Use an independent FIX engine or separately implemented validation logic to cross-check generated messages.
Ground truth must not be derived from the tool under test. For external datasets where complete ground truth
cannot be established, classify them as exploratory or compatibility tests rather than definitive correctness
tests.

## 14. Differential and property-based testing
Where feasible:
- Compare parsing results with QuickFIX or QuickFIX/J (if neither can be run here, record it as BLOCKED).
- Compare independently reconstructed order states and trading figures.
- Implement property-based tests using Hypothesis or an equivalent framework.
- Generate randomised but valid order lifecycle sequences.
- Generate invalid scenarios through controlled mutations.
- Test deterministic output across repeated runs, and that decoding the same text twice gives the same result.
- Test equivalent representations of the same FIX message stream (the four delimiter forms, line prefixes,
  line endings): the results must be the same.

When comparing different implementations, investigate discrepancies rather than assuming either
implementation is automatically correct.

## 15. Test execution methodology
Execute in the following order:
1. Repository and architecture assessment.
2. Existing test suite baseline.
3. External dataset acquisition and validation.
4. Independent synthetic fixture generation.
5. Wire-format and parser correctness.
6. Session-level validation.
7. Order lifecycle validation.
8. Multi-session isolation.
9. Malformed input and recovery.
10. Differential and property-based testing.
11. Performance and limit testing.
12. Regression analysis.
13. Final assessment.

Use isolated environments and temporary directories. Do not install untrusted dependencies or execute
downloaded scripts without inspecting them. Do not connect to production trading systems. Do not modify
production data, configuration or credentials. Do not commit, push or deploy changes without explicit
approval. You may create test scripts, fixtures and supporting documentation in a dedicated testing directory.
If an environmental limitation prevents a test, record it as BLOCKED rather than PASS.

## 16. Defect classification
Classify every defect:
- **P0 (Critical):** silent data corruption, incorrect economic exposure, double-counted executions,
  cross-session contamination or materially incorrect order reconstruction.
- **P1 (High):** incorrect session recovery, significant data loss, incorrect protocol interpretation, crashes
  on valid traffic or materially incorrect metrics.
- **P2 (Medium):** limited compatibility, recoverable failures, misleading diagnostics or significant
  performance inefficiencies.
- **P3 (Low):** cosmetic issues, minor usability problems or documentation deficiencies.

For every defect, provide: a unique defect identifier; severity; affected component; affected FIX version; a
minimal reproducible fixture; the exact reproduction command; expected behaviour; actual behaviour; the
relevant source code location; supporting evidence; root cause, if established; operational or financial
impact; recommended remediation; a proposed regression test.

Separate confirmed defects from suspected defects and architectural risks.

## 17. Deliverables
A self-contained directory, here `docs/agent-harness/fix-lens/validation/`:

```
validation/
├── README.md
├── environment.json
├── sources/
│   └── manifest.json
├── dictionaries/
├── generators/
├── datasets/
│   ├── FIX42/
│   ├── FIX44/
│   ├── multi-session/
│   ├── malformed/
│   └── performance/
├── ground-truth/
├── tests/
├── reproductions/
├── benchmarks/
└── reports/
    ├── executive-summary.md
    ├── architecture-assessment.md
    ├── test-matrix.md
    ├── defects.md
    ├── results.json
    ├── benchmark-results.csv
    └── final-assessment.md
```

Large datasets should be reproducible from scripts and seeds rather than committed to source control.
`dictionaries/` holds third-party files only where their licence allows a copy; otherwise the source and
checksum in `sources/manifest.json`.

The test matrix must include: test identifier; feature; FIX version; dataset; expected result; actual result;
PASS / FAIL / BLOCKED / NOT APPLICABLE; evidence; associated defect identifier. Do not report a test as PASS
unless it has actually been executed and its assertions verified.

## 18. Final production-readiness assessment
Provide an evidence-based assessment of: protocol correctness; parsing reliability; session reconstruction;
order lifecycle reconstruction; execution and quantity accuracy; multi-session isolation; fault tolerance;
scalability within the stated limits; observability and diagnostics; maintainability; test coverage;
production readiness.

Assign a score from 0 to 10 for each applicable category, explaining the evidence and limitations behind each
score.

Provide a final verdict: PRODUCTION READY, CONDITIONALLY READY, NOT PRODUCTION READY or INSUFFICIENT EVIDENCE.
A confirmed unresolved P0 defect must prevent a production-ready verdict. Identify the highest-risk remaining
failure modes and prioritise remediation.

Clearly distinguish: what was tested; what passed; what failed; what could not be tested; what functionality
is outside the advertised scope; what remains uncertain.

## 19. Operating principles
Be exceptionally critical. Challenge assumptions. Prefer reproducible evidence over subjective impressions.

Do not confuse a successfully parsed message with a correctly interpreted business event. Do not confuse
protocol compliance with correct economic reconstruction. Do not treat the absence of exceptions as proof of
correctness. Do not modify tests merely to make them pass.

Do not silently expand the production tool's advertised scope or classify unsupported optional features as
implementation defects.

Do not fix production defects during the independent validation phase. Report them first so that remediation
and subsequent regression testing remain independently auditable.

Begin by inspecting the repository and establishing the baseline. Then proceed autonomously through the
validation phases, producing tangible evidence and reproducible results rather than merely proposing a testing
strategy.

## Taken out as out of scope (not to be tested)
These are not dropped: on Ubay's instruction they are the candidate scope of phase 2
(`../phase-2-scope.md`), after this first deliverable.

| From | Removed | Why |
|---|---|---|
| 3 | Wireshark sample captures; the two hosted sandboxes | PCAP is not an input the tool reads; the sandboxes need an account |
| 4, 11 | FIX 5.0 SP2 over FIXT 1.1, DefaultApplVerID, ApplVerID | the product supports FIX 4.2 and 4.4 only |
| 4 | Required fields per version; venue-specific dictionaries | field-level validation and custom dictionaries are out of scope; an unknown tag is only labelled |
| 5 | "Valid repeating-group structures" as a requirement on generated data | groups are not analysed (see section 8) |
| 6 | Heartbeat timeouts; unexpected disconnections as something to detect; bounded and unbounded resend ranges; PossResend (97); OrigSendingTime (122); resets "across trading days" | the tool shows these messages and fields but does no timing or resend-range analysis |
| 7 | Order Status Request (35=H) as a lifecycle event; IOC and FOK behaviour; orders spanning multiple log files; LeavesQty (151); quantity invariants (CumQty, LeavesQty) and their exceptions | the tool does not validate quantities or order-type behaviour and reads one paste; 35=H is decoded but is not a timeline event |
| 8 | All market data testing (35=V, W, X, Y, subscriptions, order books) | no market data analysis; only the repeated-tags rule is kept |
| 9 | JSON-wrapped messages; TCP payloads and PCAP; rotated and compressed files; timestamp precisions, time zones, clock skew; latency metrics; classifying unsupported formats | input is pasted text in four delimiter forms; the tool computes nothing from times |
| 10 | Missing mandatory fields (beyond 8, 9, 35 and 10); invalid timestamps; repeating-group counts, order and nesting; length-delimited DATA fields containing delimiters; inconsistent execution quantities | field-level and group validation are out of scope; DATA fields with delimiters are excluded by the PRD |
| 11 | Market-data and order-entry session mixes; drop-copy reconciliation as a feature; multiple trading days, midnight boundaries, clock discrepancies | no market data, no reconciliation feature, nothing computed from times |
| 12 | Datasets of 100,000, 1,000,000 and 10,000,000+ messages; market data in the mixes | far over the stated limit of 1,000 messages per paste, and not feasible as pasted text in a browser page; one over-limit check is kept |
| 12 | CPU utilisation; temporary disk usage; warm-cache against cold-cache | a single-threaded page that writes nothing to disk; first decode against repeated decodes is kept instead |
| 13 | Expected remaining quantities; market data state; timestamps and latency metrics | the tool reports none of these |
| 14 | Results across log rotation and file partitioning | the tool reads one paste; splitting a log changes its results by design |
| 15 | The market data validation step | no market data analysis |
| 17 | `datasets/FIX50SP2/` and `datasets/market-data/` | out of scope, as above |
