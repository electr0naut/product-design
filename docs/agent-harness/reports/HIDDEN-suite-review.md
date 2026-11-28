# The hidden suite is copied where workers can read it: audit now, fix in D20 (instruction)

Your first difference is confirmed in the kit: `score.py` checks the trusted main out under
`/srv/lab/agent-harness/work/prove/` and copies the hidden files into it. I reviewed D10 and missed it. The
queue is empty, so nothing is exposed now. No ticket is loaded until this is fixed.

## 1. Audit, read-only, before anything else (bake-off report included)

Find out whether any worker ever saw the hidden tests. Search every Hermes worker session since the hidden
suite was first copied to the host (all profiles, the bake-off profiles too): tool calls, commands and file
reads that touch any of these:

- the path `work/prove`, or the host-only `acceptance` folder;
- a file name starting `acc-` and ending `.test.js`;
- the exact titles of hidden tests (take ten distinctive titles from the suite and search for them as text).

Report as `AUDIT-hidden-suite.md`: what you searched and how (the queries), how many sessions and how far back
the records go, and every hit with its session, profile, ticket and time. If records for some period are gone,
say which. A clean result must say what it could not cover.

## 2. Add to D20 (the runner's acceptance run)

- **Where:** the hidden tests are never written under `work/` or anywhere the worker user can read. Score in a
  separate no-network container that mounts a checkout of the trusted main and the hidden folder, as your
  bake-off scoring does, or in a folder owned by another user with mode 0700. Say which and why.
- **When:** no worker card runs while the hidden suite runs. D20 already holds the next ticket until the
  acceptance run is done; test that the hold covers the whole run.
- **Afterwards:** the scoring folder is removed, and a leftover from a crashed run is removed on the next pass.
- **Tests:** after a scoring run nothing matching the hidden glob exists under `work/`; a worker-user process
  cannot list the scoring folder during a run; a crashed run's folder is cleaned up.
- The proof tests the reviewer writes (`work/prove` for `prove_cmd`) are not hidden tests and may stay.

## 3. Your other differences

- **2 (copies into host state by hand, and the `queue.write_queue` one-liner):** the rule stands. Until
  `refresh_copies` is deployed, such a step waits for Ubay. None is needed before then.
- **3:** noted. Both predate the rules.
- **4 (deleting your own throwaway profiles and scratch folders):** I am asking Ubay to rule on this. Until he
  does, leave them in place and list them in your report.
- **5:** keep the fresh-clone check. It is stricter than the rule.
- **6:** D20 removes the driver dependency. Keep the loading trap in `HANDOFF.md`.
