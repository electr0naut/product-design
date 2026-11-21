# Review Gates Hardening and Role Portal Plan

**Goal:** Close the known gaps in the review-gate engine, then ship a role-based review surface that shows each stakeholder what decision is pending and lets them answer open questions — without pretending an unauthenticated web page is an approval.

**Architecture decisions**

1. **Python stays authoritative.** The portal renders `check_gate.py --json` output plus artifacts. Gate rules are never reimplemented in TypeScript, so status cannot drift between CLI and UI.
2. **Feedback is a packet, not a write.** With no login there is no identity, so the page produces a review packet (decision + comments + artifact hashes) that the maintainer verifies and commits. A later SSO phase adds an audited writer.
3. **AI assists, never decides.** The helper drafts an answer to an open question or a comment. It is labelled, server-side, rate-limited, never auto-submits, and never touches the manifest.
4. **Local-first deployment.** No-login pages expose confidential analysis. Default to `npm run dev` / localhost. Public hosting requires a deliberate, documented decision.

**Tech stack:** Python 3.11 stdlib, Next.js 16 App Router, TypeScript, existing `make check`.

---

## Part 1 — Fix the known limitations

### Task 1.1 Make per-epic invalidation real

**Problem:** every epic lane hashes the shared PRD and technical design, so one PRD edit stales every lane. Selective invalidation is currently a claim, not a property.

**Approach:** derive deterministic per-epic scope documents and review those.

- New `shared/scripts/epic_scope.py`: given the PRD and technical design, extract `E01`'s heading section and the design sections that reference `E01`, writing `06-backlog/<product>/scopes/E01.md`. Extraction is stable: same inputs → same bytes; a missing section is an error, not an empty file.
- Manifest lanes point `artifacts` at their scope document, not the whole PRD. Gate-level shared concerns get their own cross-cutting lane (for example `architecture`) that hashes the PRD and design.
- `generate_stories.py` writes scope files before the gate check and refuses if a scope file does not match its approved hash.
- Document the remaining truth plainly: editing PRD text shared by two epics changes both scopes.

**Acceptance:** editing E02's PRD section leaves E01 ready and blocks E02; editing a shared section blocks both; scope extraction is byte-identical across runs; a changed scope file is refused.

### Task 1.2 Append-only feedback resolution

**Problem:** resolving a comment mutates the decision that raised it, so the JSON cannot answer "who objected, and when did it clear".

- Schema v2: decisions keep immutable `feedback`; resolutions live in a top-level `feedback_resolutions` list (`feedback_id`, `resolution`, `resolved_at`, `resolved_by`, `evidence`).
- A resolution must be newer than the objection; duplicate resolutions are rejected. Status is derived from the latest resolution per feedback id.
- `migrate_manifest.py --from 1 --to 2` moves `status: resolved` entries into the new list and refuses ambiguous input. Reader supports v1 with a deprecation warning for one release.

**Acceptance:** an unresolved comment blocks even after a later approval; a resolution unblocks without editing the decision; resolution ordering is enforced; migration round-trips the fixture set.

### Task 1.3 Gate the implementation phase

**Problem:** `scaffold_code.py` has no gate; the backlog can be expanded into an implementation plan with no sign-off.

- Add `backlog-to-implementation` enforcement: sources are the story files for the selected epics plus the technical design; lane policy reuses the epic `epic: true` split, plus cross-cutting lanes.
- `validate_backlog.py` remains a separate traceability check; passing it is not approval.

**Acceptance:** a blocked lane refuses implementation-plan generation before any write; `--draft` remains explicit and labelled.

### Task 1.4 Durable draft status

**Problem:** `--draft` is only a stderr message; the sidecar and output look identical to an approved run.

- Provenance sidecar gains `review_status: "draft" | "gated"`, `gate`, `lanes` checked, and (when gated) the manifest digest.
- `--draft` output paths keep the canonical name but the sidecar records draft; `check_gate`/`review_pack` surface "draft exists, unapproved".
- Never write `review_status: "approved"` — approval lives only in decisions.

**Acceptance:** sidecar distinguishes draft from gated; a gated run records the manifest hash; no code path writes an approved status.

### Task 1.5 Review packs and a stale report

**Problem:** reviewers must read whole documents; nobody sees stale approvals until a generator refuses.

- `shared/scripts/review_pack.py --product X --role legal [--lane E02]` emits a Markdown pack: decision requested, artifacts with hashes, what changed since that role's last decision, open questions, assumptions expiring within 30 days, open changes, other roles' status.
- `check_gate.py --all --json` reports every gate/lane/product: ready, blocked reasons, drafts present, decisions older than their artifacts. Add a CI job that publishes it as an artifact (non-blocking).
- "What changed" uses the recorded decision's artifact hashes plus `git diff` when available; no hash history means "unknown, first review".

**Acceptance:** a pack for a blocked lane lists exactly the missing roles and open questions; the all-gates report finds a stale approval that a single gate check would miss; CI uploads it.

### Task 1.6 Evidence and provenance integrity

- Accept `evidence` as a URL or ticket reference; warn (not fail) when it is free text, so weak evidence is visible in packs.
- Record the model when the CLI can report it: pass `--output-format json` where supported, store `model` and `model_source`; otherwise keep `null`.
- Sidecar records the manifest digest used, so an approval cannot be silently re-pointed at different rules.

**Acceptance:** tests cover model-known and model-unknown paths; sidecar hash changes when the manifest changes.

---

## Part 2 — Role-based review pages (no login)

### Task 2.1 Read model generation

- `shared/scripts/build_portal_data.py --out public/review-data` writes one JSON file per product: gates, lanes, status, roles, decisions, feedback, assumptions, changes, artifact paths and hashes, plus a `generated_at` and a `schema_version`.
- The page never reads the manifest directly. If the JSON is stale relative to the manifest, the page shows a banner with both hashes.
- Artifacts are copied or linked read-only; never served from a path the manifest does not declare.

**Acceptance:** deterministic JSON; stale data is detected; no undeclared artifact can appear; a Python test asserts the JSON shape the UI depends on.

### Task 2.2 Pages

Routes (App Router, server components):

- `/review` — product list with gate progress.
- `/review/[product]/[role]` — that role's queue: lanes awaiting their decision, lanes blocked on others, lanes ready.
- `/review/[product]/[role]/[gate]/[lane]` — the decision page.

Each decision page shows, in this order: the decision requested (approve / request changes / not applicable / cannot determine); the exact artifacts with hashes and links; what changed since this role's last decision; open questions addressed to this role; assumptions and their review dates; other required roles and their status; a feedback box.

**Acceptance:** a role sees only lanes where it is required, plus read-only context; the page states in plain language that a submitted packet is not an approval; keyboard navigation and heading order pass a manual accessibility check.

### Task 2.3 Feedback and decision packets

- The form records decision, comments per artifact section, and cited open-question IDs. It validates client-side and produces a packet:

```json
{
  "schema_version": 1,
  "product": "acme",
  "gate": "design-to-backlog",
  "lane": "E02",
  "role": "legal",
  "decision": "request_changes",
  "reviewer": "<typed name>",
  "artifact_sha256": { "...": "..." },
  "feedback": [{ "id": "F-003", "text": "..." }],
  "created_at": "..."
}
```

- Copy/download only in this phase. The page also prints the exact command a maintainer runs to validate and record it (`record_decision.py --packet ... --verify`), which re-checks hashes and refuses packets whose artifacts changed.
- No unauthenticated endpoint writes into `review/`.

**Acceptance:** a packet built from a page is accepted only if hashes still match; a stale packet is rejected with the changed files named; the page cannot produce an "approve" packet for a role it is not showing.

### Task 2.4 AI help for open questions

- `POST /api/assist` (server-side route): input is the lane id, role, the specific open question, and short artifact excerpts selected by the server from declared artifacts only. No arbitrary file paths, no whole-document upload from the client.
- Documents are wrapped as untrusted data with explicit delimiters; instructions inside documents are ignored. Output is a draft answer plus the sources it used; if the model cannot ground an answer it says so.
- Guardrails: env-gated (`REVIEW_ASSIST_API_KEY`), per-session rate limit, token cap, no logging of content, 60-second timeout, and a visible "AI draft — review before submitting" label. The draft lands in the feedback box; it never submits.
- If the key is absent the feature is hidden, not degraded silently.

**Acceptance:** route rejects missing/oversized input and undeclared artifacts; a prompt-injection fixture does not change system behaviour; no key means no UI; the AI draft is never auto-submitted; unit tests mock the provider.

### Task 2.5 Deployment and confidentiality boundary

- Default `npm run dev` on localhost. A build-time flag `REVIEW_PORTAL_PUBLIC=1` enables public hosting and requires an explicit banner: "unauthenticated, contains confidential material".
- Document that a no-login portal is a convenience surface for people already trusted with the material; it is not access control.
- CSP, no inline script from model output, Markdown rendered without raw HTML, no secrets in client bundles.

**Acceptance:** production build succeeds with and without the flag; a CSP header test; the public banner is present only when enabled.

---

## Part 3 — SSO and audited decisions (later)

Not in this increment, but the contract is reserved:

- OIDC (Google Workspace) login; role claims mapped to manifest roles; per-lane authorization.
- `POST /api/decisions` writes through an audited service: authenticated actor, server-computed artifact hashes, append-only event log, idempotency key.
- Reviewer identity stored as issuer + subject, not a typed name; decisions signed with a server key; optional e-signature integration for gates that need one.
- Portal writes and Git commits share one schema version so history remains reconstructable.

---

## Sequencing

1. 1.2, 1.4, 1.6 (schema and status integrity) — no UI depends on them, but they change the data contract.
2. 1.1 (scope documents) — makes swimlane invalidation real; changes lane artifacts.
3. 1.3, 1.5 — enforcement completeness and reviewer ergonomics.
4. 2.1 → 2.2 → 2.3 → 2.4 → 2.5.
5. Part 3 when reviewers are external or a gate needs a signature.

## Risks

- **Scope extraction drift:** heading edits silently change scope membership. Mitigate with golden fixtures and a warning when an epic heading disappears.
- **Two sources of truth:** if the UI ever computes status, it will disagree with the CLI. Keep the JSON contract and a shape test.
- **AI over-trust:** a fluent draft answer can look like advice. Label, cite, never submit, never write.
- **Confidentiality:** an unauthenticated page reproduces legal, risk and finance analysis. Localhost by default; public only by explicit decision.
- **Feedback mutation:** this plan removes it, but existing manifests may already contain edited history. Migration keeps what exists and warns.

## Open decisions (defaults proposed)

1. **Where the portal runs:** localhost only (default) or a private hosted URL. Affects confidentiality and whether API routes are acceptable.
2. **AI provider and data handling:** which provider may see legal/compliance excerpts. Default: same provider already used for generation, excerpts only, key server-side.
3. **Who verifies packets:** the maintainer commits decisions after hash verification (default), or a second reviewer is introduced when one exists.

## Verification

Every task ships with failing tests first and `make check` green. Part 1 is complete when the gate tests cover per-epic isolation, feedback resolution history, implementation gating, sidecar draft status, pack contents and the all-gates report. Part 2 is complete when a role page can be rendered from generated data, a packet round-trips through `record_decision.py`, the AI route is gated and tested, and the build passes with and without the public flag.
