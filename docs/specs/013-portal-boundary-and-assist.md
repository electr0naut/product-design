# Review Portal Boundary and AI Assist

## Problem

Stakeholders need to see what decision is pending and answer open questions
without reading whole documents, and without a login system that does not exist
yet. A web page must not become an approval mechanism by accident.

## Scope

- Local Next.js pages under `/review`: products, roles, queues and a decision
  page per gate/lane.
- Data comes from `check_gate.py --role`, which uses the same evaluator as the
  CLI. TypeScript performs no readiness logic.
- Decision pages show artifacts, their SHA-256, the source commit, blocking
  reasons, other roles' decisions, questions for the role, and a form that
  builds a packet.
- Packets are downloaded or copied; `record_decision.py` verifies and records
  them. There is no unauthenticated write endpoint.
- `/api/assist` answers one question from its cited section using the local
  `claude` CLI with no tools, an empty working directory and delimited untrusted
  text. Quotes are kept only if they appear verbatim in the excerpt.

## Non-goals

- Authentication, role-based access control, signatures.
- Public hosting. The server binds to loopback and rejects foreign `Host`
  headers.
- Rendering raw HTML from artifacts or model output; artifacts are shown as
  escaped text.

## Invariants

- No generated product data under `public/`; pages read the repository at
  request time.
- Product, role, gate, lane and artifact identifiers are validated and resolved
  through a manifest lookup, never used as filesystem paths directly.
- Assist is disabled unless `REVIEW_ASSIST_ENABLED=1`; it requires a JSON content
  type, a custom request header and a same-origin `Origin`.
- Assist output is labelled, never auto-submitted, and records no content.

## Acceptance criteria

- [ ] `/review`, product, role and lane pages render for a configured manifest.
- [ ] A foreign `Host` header receives 403; loopback requests succeed.
- [ ] Assist returns 403 on cross-origin, 415 without JSON, 503 when disabled,
      and only verbatim quotes when enabled.
- [ ] A packet produced from the page is accepted by `record_decision.py` only
      while the artifact hashes still match.
- [ ] The build succeeds with the portal routes present.

## Test plan

Manual verification with a fixture manifest plus `curl`: page status codes,
foreign-host rejection, assist quote filtering and cross-origin rejection,
recording two roles and observing the gate stay blocked on an open question.
Automated browser tests remain a follow-up (see the plan's test-harness task).
