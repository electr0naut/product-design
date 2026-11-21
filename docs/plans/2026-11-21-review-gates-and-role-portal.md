# Review Gates Hardening and Role Portal Plan

**Status:** revised after adversarial review; epic isolation decided as a
physical PRD split (Task 1.6).

**Goal:** Close the known gaps in the review-gate engine, then ship a role-based
review surface that shows each stakeholder what decision is pending and lets
them answer open questions — without pretending an unauthenticated page is an
approval.

**Architecture decisions**

1. **Python stays authoritative.** One function, `portal_view(manifest, role)`,
   emits the per-role read model. The UI renders it; it never computes
   readiness, blocked-by or pending-for.
2. **Feedback is a packet, not a write.** With no login there is no identity, so
   the page produces a review packet that `record_decision.py` verifies and
   records. No unauthenticated endpoint writes into `review/`.
3. **AI assists, never decides.** The helper answers one open question from
   question-anchored excerpts, returns verified quotes plus a draft, and is
   recorded as `ai_assisted` when its draft is used.
4. **Loopback only.** `next start -H 127.0.0.1`, Host-header check, no generated
   product data under `public/`. Remote access is a later, explicit decision.

**Tech stack:** Python 3.11 stdlib, Next.js 16 App Router, TypeScript, vitest,
Playwright + axe, existing `make check`.

---

## Part 0 — Specs first

`ENGINEERING.md` requires a spec per behaviour change. Create:

- `docs/specs/009-decision-ordering-and-recording.md`
- `docs/specs/010-append-only-feedback-and-changes.md`
- `docs/specs/011-implementation-gate.md`
- `docs/specs/012-open-questions.md`
- `docs/specs/013-portal-boundary-and-assist.md`
- amend `docs/specs/008-scoped-review-gates.md` if epic isolation changes lane
  artifacts.

Each task below starts by writing its spec and its failing tests.

---

## Part 1 — Correctness before surface

### Task 1.1 Decision ordering and `record_decision.py`

**Problem:** the evaluator takes the last decision in array order. Once packets
are recorded later than they were written, array order and time diverge.

- `validate()` rejects decisions for the same gate/lane/role whose
  `recorded_at` is not non-decreasing in file order.
- Decisions gain `source_commit` (the commit reviewed, supplied by the caller)
  and `recorded_by`.
- New `record_decision.py --packet <file> --evidence <channel-ref>`:
  re-hashes artifacts, rejects stale *approvals*, allows `--accept-stale` only
  for non-approval decisions, assigns decision and feedback IDs itself, stamps
  `attestation: "typed-name, unverified"`, refuses a packet whose `created_at`
  predates that role's latest decision, and appends atomically.
- Packet schema: product, gate, lane, role, decision, reviewer, artifact hashes,
  feedback text, created_at, source_commit. No IDs from the client.

**Acceptance:** a packet recorded out of order is refused; a stale approve is
refused without any write; a stale request_changes needs `--accept-stale`; IDs
are server-assigned and unique; the manifest file is replaced atomically.

### Task 1.2 Append-only feedback and changes (schema v2)

**Problem:** resolving feedback mutates the objection; `changes[].status` has
the same problem; v1 has no resolution provenance.

- Decisions keep immutable `feedback`. New top-level `feedback_events`:
  `{id, feedback_id, action: resolve|reopen, text, at, by, evidence}`.
  Status is derived from the latest event per feedback id.
- Changes become `change_events` with the same resolve/reopen model; the change
  record keeps its source, scopes and raised_at.
- `migrate_manifest.py`: v1 resolved comments become a `resolve` event with
  `at = decision.recorded_at`, `by = "migrated-v1"`,
  `evidence = "pre-v2; see git history"`; prints counts; idempotent.
- No dual reader: a v1 manifest fails with "run migrate_manifest.py".
- `EXAMPLE.json` migrated and asserted to produce identical gate results.

**Acceptance:** an objection resolved then reopened blocks again; migration is
idempotent and preserves outcomes; a v1 file is refused with the migration hint;
event ordering is validated.

### Task 1.3 Open questions as data

**Problem:** the portal is built around answering open questions, but they are
free text with no IDs, owner, or blocking semantics.

- Manifest gains `questions`: `{id: Q-001, gate, lane, role, text, source:
  {artifact, heading}, raised_at}` and append-only `question_answers`
  (`text`, `answered_by`, `answered_at`, `ai_assisted`, `evidence`).
- Unanswered questions block their lane. An answer alone does not unblock: the
  source document must be edited, which makes prior approvals stale and forces
  reapproval — the answer is evidence, not approval.
- `extract_questions.py` proposes questions from PRD `## Open Questions` and
  story `## Open Questions` sections, with stable IDs; the maintainer accepts
  them into the manifest.
- Portal shows questions for the role and anchors the source section.

**Acceptance:** unanswered blocks; answered-without-reapproval still blocks;
answer ordering and duplicate answers are rejected; extraction is deterministic
and never writes to the manifest.

### Task 1.4 Durable draft status and policy provenance

**Problem:** `--draft` is a stderr label; story output has no sidecar at all;
the manifest digest changes on every decision and proves nothing.

- Every generated output gets a sidecar, including one file per epic for
  `generate_stories`.
- Sidecar records `review_status: "draft" | "gated"`, gate and lane IDs, the
  decision IDs that released each lane, and a `policy_sha256` per lane
  (roles + artifacts + depends_on only).
- No path writes `review_status: "approved"`; approval lives only in decisions.

**Acceptance:** an epic draft has a sidecar marked draft; a gated run lists its
decision IDs; adding an unrelated decision leaves `policy_sha256` unchanged;
removing a required role changes it.

### Task 1.5 Implementation gate via a backlog lock

**Problem:** `scaffold_code.py` reads only the technical design; gating story
files it never consumes would be theatre.

- `validate_backlog.py` writes `06-backlog/<product>/backlog.lock.json` (sorted
  story path to SHA-256) only when validation passes.
- `scaffold_code.py` bundles design + lock + listed stories, calls
  `maybe_enforce_gate` and `verify_bundle`, and gains `--draft`.
- Manifest snapshot: lane artifacts are the lock file; the lock lists stories.

**Acceptance:** editing a story after approval blocks implementation-plan
generation before any write; `--draft` succeeds and is labelled; a failed
`validate_backlog` leaves no lock.

### Task 1.6 Epic isolation by splitting the PRD

**Problem:** epic lanes hash the shared PRD and design, so one PRD edit stales
every epic, and `--epic E01` still bundles the whole PRD — including unapproved
E02 edits.

**Chosen approach:** the PRD becomes one core document plus one file per epic.
Epic lanes hash only their epic file; shared concerns stay in a cross-cutting
lane.

**New document shape**

```text
04-prd/<product>/
  core.md            overview, personas, NFRs, data/privacy, UX, release, metrics
  epics/E01.md       epic goal, story table (IDs, persona, traces_to, priority),
                     epic-specific functional detail, open questions
  epics/E02.md
```

**Work**

1. Amend the PRD template: `prd-template.md` becomes `prd-core-template.md`;
   add `epic-template.md`. `generate_prd.py` gains `--format split` and emits
   core + epic files (plus sidecars); the monolithic `--format single` remains
   for exploration and is marked draft.
2. `split_prd.py` deterministically converts an existing monolithic PRD into
   core + epics, preserving bytes and stable IDs; it refuses ambiguous heading
   layouts and writes nothing on error. Run once per existing product.
3. `parse_story_map` reads the product directory (core + `epics/*.md`) instead
   of a single PRD heading tree. IDs remain globally unique across epics.
4. `generate_stories.py --epic E01` bundles `core.md` + `epics/E01.md` +
   technical design only. The whole-gate path bundles every epic file.
5. Manifest: epic lane artifacts are `epics/E01.md`; the cross-cutting
   `architecture` lane hashes `core.md` and the technical design; the design
   remains shared until the design template is split the same way (explicitly
   out of scope here, and stated as a limitation).
6. Spec 008 is amended: remove "section-hash parsing" from the non-goals and
   define epic-scoped artifacts. README documents the directory layout.

**Security/order invariant:** the gate runs before any write; the splitter is a
separate, explicit command and is never invoked implicitly by generation.

**Acceptance:**
- Editing `epics/E02.md` leaves `generate_stories --epic E01` passing; the E01
  prompt contains no bytes from E02.
- Editing `core.md` blocks every epic lane (and the architecture lane).
- The splitter round-trips a fixture PRD byte-for-byte and is idempotent.
- A monolithic PRD is refused by generators that expect the split layout, with
  a message naming `split_prd.py`.

### Task 1.7 Review packs and the stale report

- `review_pack.py --product X --role legal [--lane E02]`: decision requested,
  artifacts + hashes + commit, what changed since this role's last decision
  (`git diff <source_commit>`; otherwise changed/unchanged only), open
  questions for the role, assumptions expiring, open changes, other roles.
- `check_gate.py --all --json --today YYYY-MM-DD` reports every product, gate
  and lane, including drafts, stale approvals, and lanes stale in another gate
  than the one being checked. `--today` is required for reproducible CI.
- CI uploads the report as an artifact (informative only).

**Acceptance:** a pack lists exactly the missing roles and questions; the
all-gates report finds a stale lane in gate B while checking gate A; the report
is deterministic for a fixed date.

### Task 1.8 Evidence quality

- Evidence accepts a URL or a configured ticket pattern (config, not code);
  free text is accepted with a warning surfaced in packs and the portal.
- No model capture in this increment (see cut list).

**Acceptance:** a configured pattern validates; free text warns but records.

---

## Part 2 — Role-based review pages

### Task 2.1 `portal_view` and the golden contract

- `portal_view(manifest, role)` returns: product, role, generated_at,
  `pending_for_role` (lanes requiring this role with status and reasons),
  `blocked_by_roles`, `questions_for_role`, artifact metadata (path, hash,
  source_commit, link token), assumptions, changes, and the draft/stale summary.
- No readiness logic in TypeScript. A grep/lint rule forbids status computation
  under `src/`.
- A golden JSON fixture is produced by Python tests and imported by a TypeScript
  shape test; both fail if the shape drifts.

**Acceptance:** fixture round-trip; a missing field fails typecheck; a role only
receives lanes where it is required plus read-only context.

### Task 2.2 JavaScript test harness

- Add vitest for route handlers and pure modules, Playwright + axe for smoke and
  accessibility, wired into `make check` and CI.
- Replace "manual accessibility check" with: axe reports zero serious/critical
  violations on the three routes; a keyboard-only Playwright run completes a
  packet.

**Acceptance:** the new tests run in `make check` and fail on a deliberate
regression.

### Task 2.3 Serving model

- No generated data under `public/`. Server components call Python
  (`execFile` with a fixed argument list, no shell) through a `server-only`
  module; results are request-time, so there is no stale banner.
- `next start -H 127.0.0.1`; `proxy.ts` rejects any `Host` other than
  `127.0.0.1:<port>` or `localhost:<port>`; the server refuses a non-loopback
  bind unless `REVIEW_PORTAL_TRUSTED_PROXY=1`.
- Product and role segments must match `^[a-z0-9-]+$` and exist in the listing;
  `EXAMPLE` is excluded from routing.

**Acceptance:** `Host: evil.example` returns 403; `public/` contains no product
data (CI grep); a path-traversal segment 404s.

### Task 2.4 Pages

- `/review` — products and gate progress.
- `/review/[product]/[role]` — that role's queue: awaiting me, blocked on
  others, ready (from `portal_view`).
- `/review/[product]/[role]/[gate]/[lane]` — decision requested, artifacts with
  hashes and links, what changed, questions for the role, assumptions, other
  roles, feedback box.

**Acceptance:** a role sees only its lanes; copy states that a packet is not an
approval; keyboard flow works end to end.

### Task 2.5 Packets and recording

- Form produces the packet from Task 1.1, with artifact hashes and
  `source_commit`; copy/download plus the exact `record_decision.py` command.
- `record_decision.py --verify` re-hashes and names changed files; stale
  approvals refused; non-approvals accepted with `--accept-stale` only.
- The page cannot be the security boundary; `record_decision` enforces role,
  staleness and ID assignment.

**Acceptance:** a packet from the page is recorded only when hashes match; a
tampered packet naming another role is refused; an edit after packet creation is
reported by file name.

### Task 2.6 AI help for one question

- `POST /api/assist`: input is product, gate, lane, question ID, role, and a
  choice of length. The server loads only that question's anchored section (max
  N KB) from declared artifacts. No client paths, no whole-document upload.
- Runs the local Claude CLI with tools disabled in an empty temporary working
  directory (same data path and login as generation — no second provider key).
  Documents are delimited and labelled untrusted; delimiter collisions are
  escaped.
- Output: relevant quotes (each verified by exact substring match; unverified
  quotes removed and flagged), a draft answer separated into "grounded" and
  "needs your knowledge", and a list of missing information.
- Guardrails: per-process token bucket plus a daily budget, `Content-Type:
  application/json`, a custom header and same-origin `Origin` check, 60s
  timeout, no content logging, feature hidden when the CLI is unavailable.
- If the draft is used, the packet records `ai_assisted: true`, the model, and
  the excerpt hashes.

**Acceptance:** quoted evidence not present in the excerpt is removed; oversized
input is rejected; a cross-site POST without the header is rejected; the feature
is absent without the CLI; a fixture document containing instructions cannot
alter the server's file access (tools disabled, fixed cwd); the draft never
submits.

### Task 2.7 Rendering safety

- react-markdown without raw HTML; remote images stripped; `javascript:` links
  rejected; links resolve through an artifact index, never a path parameter.
- CSP with a per-request nonce: `default-src 'self'; script-src 'self'
  'nonce-…'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none';
  form-action 'self'`.

**Acceptance:** a fixture with `<script>`, `onerror=`, a `javascript:` link and a
remote image renders inert and makes no external request (Playwright).

---

## Part 3 — SSO and audited decisions (later)

Reserved, not built now:

- OIDC (Google Workspace) with role claims mapped to manifest roles and
  per-lane authorization.
- `POST /api/decisions` through an audited service: authenticated actor,
  server-computed hashes, append-only events, idempotency keys.
- Identity as issuer + subject, not a typed name; server-signed decisions;
  optional e-signature for gates that need one.

---

## Sequence

1. Specs (Part 0).
2. 1.1 ordering and `record_decision.py`.
3. 1.2 append-only events and migration.
4. 1.3 questions.
5. 1.4 sidecar/draft status.
6. 1.5 implementation gate.
7. 2.1 `portal_view` + fixture.
8. 2.2 test harness.
9. 2.3 serving model, 2.7 rendering safety.
10. 2.4 pages, 2.5 packets.
11. 2.6 assist.
12. 1.7 packs and report.
13. 1.6 PRD split (schedule after the portal read model is testable; it changes
    document layout, not gate logic).

The portal does not depend on epic isolation; running 1.6 last stops the hardest
document-format question from blocking the surface.

## Cut from this increment

- `REVIEW_PORTAL_PUBLIC` and any public hosting story.
- A dual v1/v2 manifest reader.
- Model capture from `--output-format json`.
- Per-epic implementation plans.
- CI upload of the stale report (keep the command; upload later).

## Risks

- **Document split (1.6) is a contract change.** Mitigate with a splitter, a
  golden fixture, and the rule that section extraction never loses bytes.
- **Question extraction proposes wrong owners.** It proposes; a human accepts.
- **AI over-trust.** Verified quotes, grounded/ungrounded split, `ai_assisted`
  recorded, never auto-submitted.
- **Confidentiality.** Loopback only, no `public/` data, no remote images, no
  telemetry. Sharing requires network-level access, documented later.
- **Two sources of truth.** One Python `portal_view`; TypeScript shape test; grep
  guard against status logic in `src/`.

## Verification

Every task: failing test first, then `make check` green. Part 1 is complete when
tests cover decision ordering, event migration idempotence, question blocking,
draft sidecars for epics, lock-file gating, packs and the all-gates report.
Part 2 is complete when `portal_view` has a frozen contract, the JS harness runs
in CI, the server refuses foreign hosts, rendering is inert, packets are
verified, and assist is quote-grounded, rate-limited and recorded.
