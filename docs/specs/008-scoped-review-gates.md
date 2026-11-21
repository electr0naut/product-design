# Scoped stakeholder review gates

## Problem
Draft generation is not expert approval. A stakeholder's decision can apply to one product swimlane while an unrelated lane proceeds; revisions and changes must not silently reuse earlier sign-off.

## Scope
- Versioned JSON review manifest per product. Explicit gates, lanes, artefacts, required roles, dependencies, feedback, decisions, assumptions and change records. Review data is external to generated Markdown; it is a future portal's read/write contract, not an authentication system.
- Read-only CLI returns human and JSON status; exit 0 only when requested gate/lane(s) are ready. Missing/malformed data fails closed. The last recorded decision for a role controls it, never a previous approval. Each approval binds the exact byte hashes of its lane artefacts. Unresolved feedback, open changes and out-of-date decisions block. `not_applicable` and `cannot_determine` are not approval; adjust policy explicitly for an exception.
- A lane depends on upstream gate/lane scopes; a blocked or stale prerequisite blocks descendants, not unrelated lanes. Shared documents hashed by multiple lanes make all those lanes stale when edited. Selective invalidation requires distinct scoped review artefacts; never claim otherwise.
- Generator CLI discovers `review/<product>.json` when present and checks its outgoing gate before generation. `--review-manifest` selects a manifest explicitly; `--draft` permits exploratory generation only and labels it as such. Whole-document generation needs every configured lane ready; story generation can check selected epic IDs separately. No review file means legacy draft-only behavior, not approved status.
- Portal boundary: the manifest and status JSON identify reviewer roles, pending feedback, artefact paths, scope and status. A portal must authenticate actors, limit access to role-relevant exports, preserve decision history, and write through an audited service. Local JSON edits do not prove identity or meet formal signature rules.

## Non-goals
- No portal, SSO, email delivery, legal e-signatures, automatic regulation feeds, automatic semantic impact inference, section-hash parsing, or secure access control inside a Git repo.
- No guarantee that AI-generated claims are true or that manually named change scopes are complete.
- No partial BRD/PRD generation when a single shared source document is blocked.

## Invariants
- Paths in a manifest are relative to the checkout, inside it, regular files with no symlinked components or traversal; no user-supplied manifest path is written by the checker.
- Roles and lane dependencies must be explicit; no silence or unresolved comment advances a gate.
- The latest decision supersedes older ones, even if it is stale or negative.
- Changes require a source, date and explicit impacted scopes. A resolved change still requires a newer approval for impacted scopes. Dependencies propagate blocks.
- Existing generation remains possible as draft in unconfigured clones and with an explicit `--draft` flag; it must never be misreported as approved.

## Acceptance criteria
- [ ] Two independent lanes can have different status at the same gate; a blocked dependency affects only its descendants.
- [ ] Altering a reviewed artefact, replacing an approval with a request for changes, or leaving feedback unresolved blocks the scope.
- [ ] Open and resolved changes invalidate only declared scopes and descendants until newer approval; stale assumptions block linked scopes.
- [ ] Missing/wrong-role decisions, malformed paths/hash or dependency cycles fail closed with actionable errors.
- [ ] CLI JSON is deterministic and sufficient for a future role-based portal to render pending reviews and feedback.
- [ ] The story generator refuses blocked epics before writing anything while allowing an explicitly selected ready epic.
- [ ] Other generators refuse configured blocked gates; exploratory draft override is explicit.

## Test plan
Unit tests for complete and partial approvals, stale hashes, latest negative decisions, unresolved feedback, changes, dependencies, cycles and unsafe paths; CLI subprocess tests for exit/status; generator subprocess tests for release and draft paths. Run `make check`.

## Rollout and rollback
Opt-in by adding `review/<product>.json` from the example, customizing roles/lanes and collecting actual decisions. Existing clones remain draft-only. Removing the manifest disables enforcement; preserve history in Git and never present this as a valid production rollback for a regulated gate.
