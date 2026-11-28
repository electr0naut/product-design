# Accepted security risks

Each entry is a finding the maintainer chose not to fix, with one plain-English
line saying why it does not apply or why the exposure is accepted.

- **The `/review` pages have no login.** Accepted: they listen on loopback only,
  are read-only, and cannot record decisions or change a file; exposing them on
  a network needs an authentication design first.
- **The AI assist endpoint is unauthenticated.** Accepted for the same reason:
  it is loopback-only and disabled unless `REVIEW_ASSIST_ENABLED=1` and the
  `claude` CLI is installed.
