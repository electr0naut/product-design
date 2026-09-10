# Project Initiation Prompt: FIX Engine

Paste this as the first message of a new session, in a fresh clone of the
`electr0naut/product-design` template renamed for this product.

## 0. Load my environment's rules before anything else

Do this first, and report what you found before doing any project work.

1. Read every governing document available in this environment, in this order:
   - `~/.claude/CLAUDE.md` and any other global memory or memory-stack files
     under `~/.claude/` (memory, rules, procedures, standards, playbooks).
   - `~/.claude/settings.json` and `~/.claude/skills/` (list the skills and
     when each applies).
   - The repo's `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`, and every
     file in `.claude/` (these define commands such as commit, review,
     deploy-check).
   - Any `docs/`, `procedures/`, or checklist files the repo or my environment
     defines, including `shared/checklists/phase-gate.md`.
2. Produce a short inventory: which rule sources exist, what each governs, and
   which ones bind this project.
3. Where this prompt conflicts with those rules, the rules win. Say which line
   of this prompt you are overriding and why. Do not silently reconcile.
4. Follow the repo's own commit, review, and gate procedures for every change
   from here on. Do not invent a parallel process.

## 1. What we are building

A production-grade FIX engine in Python.

It must:

- Act as an **acceptor**: listen on a socket, accept inbound sessions from a
  counterparty engine, and manage each session independently.
- Act as an **initiator**: establish and maintain outbound sessions against a
  remote FIX engine, including reconnect and scheduled session windows.
- Implement the **full FIX session layer**, not just message parsing:
  sequence-number management, gap detection, resend, gap fill, possible
  duplicates, heartbeats, test requests, session-level reject, logout,
  sequence persistence across restarts.
- Be **dictionary-driven**: message and field validation comes from a parsed
  FIX specification, never from hardcoded per-message logic.
- Be usable as an embedded **library** by an application that supplies
  callbacks for admin and application messages, and as a **standalone
  process** driven by configuration.

This is an infrastructure component for order flow. A silent
mis-sequencing, a dropped resend, or a mis-encoded price is a financial
incident, not a bug report. Treat correctness as the product.

## 2. Authoritative sources

**Specifications and tooling:** `https://github.com/jamesdbrock/hffix`
(branch `master`).

Use it as follows, and only as follows:

- `fixspec/` is the authoritative machine-readable spec source. It contains
  `FIXRepository`, `fix.4.2`, `fix.4.3`, `fix.4.4`, `fix.5.0.sp2`, and
  `spec-parse-fields`. Our dictionary loader is built against these files.
- `test/data`, `test/expected`, and `test/curl.cme.data.sh` are the
  authoritative sample-message corpora (JSE, CME, FixParser origin). Every
  one of these messages must parse and re-encode byte-identically.
- `util/src` provides `fixprint`. Build it and use it as a **differential
  oracle**: the same bytes through `fixprint` and through our decoder must
  yield the same field sequence after normalisation.
- `include/hffix.hpp` and `include/hffix_fields.hpp` are reference reading for
  encoding, framing, repeating groups, and data-length pairs.

hffix is **C++ and does message encoding/decoding only**. It states
explicitly that it does not manage sessions, does no socket I/O, and does no
threading. We are not binding to it, not wrapping it, and not porting it. It
is a spec source and a test oracle. Everything above the wire format is ours
to design and build.

**Second-order references** (to evaluate in the analysis and technical design
phases, not to copy): QuickFIX / quickfix-python, simplefix, the FIX Trading
Community session-level test cases, and any venue conformance guides relevant
to the counterparties we care about.

**Licensing is a real work item, not a footnote.** Before any spec file or
sample data is vendored into our repo, confirm the licence of hffix itself and
the redistribution terms of the FIX Repository / FIX specification documents it
bundles. Route this through the phase-02 legal analysis and record the outcome.

## 3. Hard rules for this project

1. **No spec constant from memory.** Every tag number, enum value,
   required-field rule, message-type code, and data-type constraint must be
   read from the vendored dictionary or the spec document, and the source must
   be cited in the design document and in the code comment where it matters.
   If you cannot cite it, you do not write it.
2. **Version differences are explicit.** Where 4.2, 4.4, and 5.0 differ, the
   difference is named in the design and encoded in the dictionary, never
   papered over with a "mostly compatible" assumption.
3. **No silent failure.** Every rejection path states what failed, which tag
   or sequence number caused it, and which spec rule was violated. No
   `except Exception: pass`, no swallowed protocol errors, no defaulting an
   unparseable field.
4. **Test before claim.** Do not report a phase or a story complete without
   showing the actual command output of the linter, type checker, and test
   run. "Should work" is not a status.
5. **Determinism in tests.** Clocks, sequence generators, and socket
   endpoints are injected. No `sleep` in a test, no dependence on wall time,
   no flaky timing assertions.
6. **Traceability.** Every PRD user story cites the BRD requirement it serves,
   the spec section it implements, and the conformance test id that proves it.

## 4. Release plan

- **Release 1 — FIX 4.2.** Complete session layer, complete message layer,
  acceptor and initiator, mock counterparty, full conformance suite. One
  version, done exhaustively.
- **Release 2 — FIX 4.4.** Added as a dictionary and a set of
  version-parameterised session rules, not a fork of the code.
- **Release 3 and beyond — FIX 5.0 SP2 with FIXT.1.1**, then 4.3 if a
  counterparty demands it. FIXT.1.1 splits transport from application version
  and is a genuinely different session model; plan for it architecturally in
  Release 1 but do not build it.

Design Release 1 so that Releases 2 and 3 are additive: a dictionary loader,
a version-parameterised session state machine, and a codec that takes its
rules from data. If adding 4.4 requires editing session logic, the Release 1
abstraction was wrong.

## 5. Process

Follow the template's staged pipeline in `README.md` and `CLAUDE.md`. Do not
skip a phase, do not work ahead, and do not edit an approved document from an
earlier phase without telling me first.

```
01-ideation/          idea canvas
02-analysis/          legal, compliance, risk, ops, product, bizdev, finance
03-brd/               business requirements
04-prd/               user stories, acceptance criteria, NFRs
05-technical-design/  architecture, engine API, data models, integration
06-implementation/    scaffold, then the engine itself
```

Generation commands (add `--prompt-only` to inspect the assembled prompt):

```bash
python shared/scripts/generate_analysis.py --idea 01-ideation/fix-engine.md
python shared/scripts/generate_brd.py --idea 01-ideation/fix-engine.md --analysis 02-analysis/
python shared/scripts/generate_prd.py --brd 03-brd/fix-engine-brd.md
python shared/scripts/generate_technical_design.py --prd 04-prd/fix-engine-prd.md
python shared/scripts/scaffold_code.py --technical-design 05-technical-design/architecture/fix-engine-technical-design.md
```

**Stop at every gate.** Work `shared/checklists/phase-gate.md` and present the
checklist filled in. I approve each gate before the next phase starts. Never
generate the next phase from an unapproved document.

## 6. What each phase must contain for this project

**01 Ideation.** Copy `01-ideation/templates/idea-canvas.md` to
`01-ideation/fix-engine.md`. The template is written for a commercial product;
adapt honestly rather than fabricating market data. Competitive landscape is
build-vs-buy: QuickFIX, commercial engines, venue-supplied APIs. Success
metrics are conformance coverage, session uptime, and defect escape rate, not
revenue.

**02 Analysis.** The seven roles are generic; reframe each to this project:
- Legal: hffix and FIX Repository licensing, redistribution of spec files.
- Compliance: counterparty and venue certification requirements, message
  retention and audit-log obligations, clock-synchronisation obligations.
- Risk: failure modes of a mis-sequenced or duplicated order, resend storms,
  split-brain on reconnect, sequence-reset misuse.
- Operations: runbooks for sequence reset, gap recovery, forced logout,
  end-of-day and weekly reset, monitoring and alerting.
- Product: who consumes the engine, embedded-library vs standalone-process
  ergonomics.
- Business development: which counterparties and versions are actually
  required, and by when.
- Finance: build vs buy, licence costs of commercial engines, engineering cost.

**03 BRD.** Business requirements, prioritised, each one testable.

**04 PRD.** This is where the protocol scope becomes user stories. Every story
gets Given/When/Then acceptance criteria, MoSCoW priority, a BRD trace, a spec
citation, and a conformance test id. Section 7 below is the raw material.

**05 Technical design.** Architecture, engine API, dictionary model,
concurrency model, persistence model, failure model, performance strategy.

**06 Implementation.** Scaffold, then build story by story with the tests
written against the spec, not against the implementation.

## 7. Scope to carry into the PRD

Do not treat this as the complete requirement set. It is the floor. Read the
4.2 spec and expand it.

**Message layer.**
- Tag=value framing with SOH delimiters; correct handling of a buffer that
  splits a message, concatenates several, or truncates one.
- `BeginString(8)`, `BodyLength(9)`, `MsgType(35)` as the first three fields
  in that order; `CheckSum(10)` last. BodyLength and CheckSum computed and
  verified per spec, with the exact byte ranges the spec defines.
- Data-length pairs where the length field must immediately precede the data
  field and the data may legally contain SOH: `RawDataLength`/`RawData`,
  `XmlDataLen`/`XmlData`, `SecureDataLen`/`SecureData`,
  `SignatureLength`/`Signature`.
- Repeating groups: count field, delimiter field, nested groups, field order
  within an instance, count mismatch detection.
- Every FIX data type with its exact lexical rules, including UTCTimestamp
  precision variants, price and quantity representation without locale or
  exponent, Boolean, MultipleValueString, MonthYear, LocalMktDate.
- Validation producing the correct session-level reject reason for each class
  of error: invalid tag, undefined tag, tag not defined for this message type,
  required tag missing, tag without value, value out of range, bad data
  format, duplicate tag, tag out of order, repeating-group order and count
  errors, embedded SOH in a non-data field, invalid MsgType. Take the exact
  enumerated set from the version's dictionary. The 4.2 set is not the 4.4 set.

**Session layer.**
- Admin messages: Logon, Logout, Heartbeat, TestRequest, ResendRequest,
  Reject, SequenceReset. Business-level reject for application messages.
- Logon exchange for both roles, HeartBtInt negotiation, EncryptMethod = none,
  ResetSeqNumFlag semantics.
- Heartbeat timing and TestRequest escalation on inbound silence, with the
  spec's tolerance, then disconnect.
- Inbound sequence number too high: queue and issue ResendRequest, then
  process the queue in order. Too low without PossDupFlag: logout and
  disconnect.
- Resend handling: replay from the message store, gap-fill administrative
  messages via SequenceReset with GapFillFlag, set PossDupFlag and
  OrigSendingTime on replays, honour the open-ended EndSeqNo convention for
  the version.
- SequenceReset in reset mode versus gap-fill mode, including the illegal
  cases.
- CompID validation, BeginString mismatch, SendingTime accuracy check, each
  with the spec-mandated response and disconnect behaviour.
- Logout handshake with timeout, and unilateral disconnect handling.
- Sequence-number and message persistence that survives process restart, plus
  the scheduled reset policy (daily, weekly, or on logon).

**Transport and runtime.**
- asyncio-based acceptor and initiator, one state machine per session,
  multiple concurrent sessions, backpressure on slow consumers.
- Reconnect with bounded backoff; session schedules with start and end times,
  days of week, and timezone.
- Optional TLS. No encryption at the FIX layer.
- Structured event logging plus a raw inbound/outbound FIX message log
  suitable for audit and replay.
- Metrics: message rates, end-to-end latency percentiles, reject counts, gap
  and resend counts, disconnect causes, session state.
- Admin surface for forced logout, sequence reset, and manual resend.

## 8. Testing and mock-counterparty doctrine

This is a first-class deliverable, planned in the PRD and built alongside the
engine, not bolted on at the end.

1. **Mock counterparty engine.** A scriptable peer that can act as either
   acceptor or initiator, and that can be told to misbehave on purpose: skip a
   sequence number, resend a duplicate without PossDupFlag, answer a
   ResendRequest with a bad gap fill, send a malformed body length, a bad
   checksum, an unknown tag, a message split across TCP segments, a truncated
   message, silence past the heartbeat interval, a half-closed socket, a
   logout without a reply. Live code testing runs the real engine against this
   peer over a real socket, in CI, with no external dependency.
2. **Differential testing against hffix.** Build `fixprint` in CI. For every
   message in `test/data` and every message our encoder produces, compare our
   decode against `fixprint` output after normalisation. Any divergence is a
   defect in us until proven otherwise.
3. **Round-trip and property tests.** With Hypothesis: decode then encode is
   byte-identical; BodyLength and CheckSum invariants hold for generated
   messages; the framer handles arbitrary chunk boundaries and arbitrary
   garbage without raising anything but our own typed errors.
4. **Session conformance suite.** Encode the FIX session-level test cases as
   executable scenarios, one test per numbered case, each asserting the exact
   response message and the resulting session state. This suite is the
   definition of done for the session layer.
5. **Fuzzing.** Continuous fuzzing of the framer and decoder against the
   corpus as a seed set.
6. **Performance harness.** Throughput and latency benchmarks with recorded
   baselines, run on demand, with regressions reported as numbers.
7. Follow the repo's Gate 6 bar: unit coverage above 80%, integration tests
   passing, runbook written, monitoring defined. Inject dependencies rather
   than mocking code we own.

## 9. Conflicts with the template you must resolve

`shared/prompts/05-technical-design.md` and `shared/prompts/06-scaffold-code.md`
assume a FastAPI web service with SQLAlchemy models, Alembic migrations, and an
OpenAPI spec. This project is a protocol engine and a library. There is no HTTP
API at its core.

Do not edit the shared template prompts in place. Create project-local
overrides in the cloned repo and use those, keeping the template generic. In
the overrides:

- Replace "API design (OpenAPI 3.0)" with the engine's public Python API, the
  application-callback contract, and the configuration schema. If an
  operational HTTP or CLI admin surface is justified, specify it separately and
  keep it out of the hot path.
- Replace SQLAlchemy data models with the dictionary model, the message store
  model, and the session state model.
- Keep the Python stack, type hints, structured logging, dependency injection,
  Docker, and CI requirements.

State this override explicitly in the technical design so the deviation from
the template is recorded rather than implied.

## 10. First turn

Do only this, then stop and wait for me:

1. Section 0: load and inventory the governing rules, and flag conflicts.
2. Confirm the repo is the cloned template on the correct branch, and report
   its current state.
3. Fetch and read the hffix repository. Report concretely what is in
   `fixspec/`, `test/data`, `test/expected`, and `util/src`, what its licence
   is, and how you intend to vendor or reference it.
4. Draft `01-ideation/fix-engine.md` from
   `01-ideation/templates/idea-canvas.md`, filled in for this project, with
   open questions listed rather than guessed.
5. Give me the Gate 1 checklist from `shared/checklists/phase-gate.md` with
   your assessment of each item.

Do not generate phase 02. Do not write engine code. Do not create a pull
request.
