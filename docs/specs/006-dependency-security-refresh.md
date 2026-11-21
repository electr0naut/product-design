# Dependency Security Refresh Specification

## Problem

The committed npm lockfile contains vulnerable Next.js and transitive dependency versions. GitHub Dependabot reports critical alerts for Next.js, and `npm audit` reports vulnerabilities in the current install graph.

## Scope

Update Next.js and the matching `eslint-config-next` to a non-vulnerable compatible 16.x release, refresh vulnerable transitive npm packages without a major application-framework migration, commit the resulting lockfile, and retain Next.js's regenerated `next-env.d.ts` type references.

## Non-goals

No product workflow, generated product artefact, Python package, or UI feature changes. The already-tracked Next.js declaration is regenerated as part of this framework update; changing its tracking policy is out of scope. Do not disable or dismiss security alerts to obtain a clean result.

## Invariants

- The existing product-design pipeline and Next.js overview behave as before.
- `package.json` and `package-lock.json` agree; a clean `npm ci` reconstructs the audited dependency graph.
- React remains on its current compatible version unless a security or peer-dependency requirement demands otherwise.

## Acceptance criteria

- [ ] `npm audit --audit-level=low` reports zero known vulnerabilities for the refreshed lockfile at review time.
- [ ] `npm ci` installs successfully, and a second `npm audit --audit-level=low` remains clean.
- [ ] `make check` passes, including Python tests, lint, typecheck, and Next.js production build.
- [ ] PR CI passes before merge; GitHub may recalculate Dependabot alerts asynchronously.

## Test plan

- Unit tests: existing Python suite through `make check`.
- Integration/CLI tests: `npm ci`, `npm audit --audit-level=low`, `make check`, and `git diff --check`.
- Fixtures or property tests: not applicable to dependency updates.

## Rollout and rollback

No data migration. Review the lockfile and CI before squash merge; revert the dependency commit if a runtime regression appears.
