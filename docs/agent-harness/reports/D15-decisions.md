# D15: the host runner applies the reviewer's decision files (D15-review.md)

Branch `d15-decisions` in agent-harness, on top of master `8f9f21f`, at **`3a0ec24a337de2374c59a52f1ffce993cfa50e96`**. Fresh clone: 400 passed, 3 skipped; ruff check and format clean. Not merged, not deployed. Deploy between tickets with `harness-deploy`.

## How it works
- **Where:** `docs/agent-harness/decisions/D-<yyyymmdd>-<n>.json` on `claude/amazing-gauss-xk4abw`. Settings are the new `[decisions]` table in `harness.host.toml` only.
- **Each pass,** before the gate and review work, the runner fetches the branch into a host-only **bare** repository (`~/.local/state/agent-harness/decisions.git`, hooks and fsmonitor off, nothing checked out), lists the folder with `ls-tree` and reads files with `git show`. Only regular files named like an id are read; over 64 KB is rejected.
- **Once, in id order** (date, then number as a number: `-2` before `-10`). The result is kept in host-only `decisions-state.json`. A decision is recorded **before** it is acted on: a crash can lose one (it stays `applying` and is not retried), never apply it twice. A corrupt state file applies nothing.
- **Journal and PR:** one line per decision (`decision applied D-…: …` / `decision rejected D-…: …`), also posted on PR #47 with `gh`. A failed post is only logged. The posted text is one line, with `@` and backticks removed.
- **A decision never stops the review pass.** A fetch or config problem prints `decisions skipped: …` and the pass goes on.

## Format (strict: extra or missing fields are rejected)
All need `id` (equal to the file name), `action`, `key`, `reason`.

| action | also needs | rejected when |
|---|---|---|
| `unblock_once` | `card` | the card is not on the board, is not a stage card of `key`, or is not blocked |
| `approve_test_edit` | `head` (40 hex), `files` (list) | the D13 function refuses it |
| `reset_attempt` | | the D11 function refuses it |
| `hold` | | `key` has no triage card, triage is not `todo`, or a live hold exists |
| `release` | | there is no hold, or it is already done |

- `reason` is required for **every** action (your list marks it without `?`).
- The hold card is titled `hold before <KEY>`, not `<KEY> · …`, so nothing takes it for a stage card. It is unassigned and linked as a parent of the triage card.
- `release` releases only holds made this way, not the older hand-made hold cards.
- The base of an approval or reset is the trusted `main` of `[decisions] work_repo` (`fix-lens`), as in the two tools.
- A rejected id stays rejected. To correct it, write a new id.
- **Several decisions in one go** are applied in id order in the same pass, so an approval (`-1`) before its unblock (`-2`) works.

## Limits
- "Within a minute" holds only while the runner is idle. A running review keeps the one-shot service busy, and decisions wait for the next pass (the service allows an hour).
- `approve_test_edit` is not checked against a blocked card; it only has an effect on the exact key, base, head and files.
- The evidence driver still exits when a ticket blocks, so after an `unblock_once` it has to be restarted by hand. If you want the loop closed, the driver should keep waiting on a blocked ticket instead (a change on `d6-driver`; not made here).

## Tests (`tests/test_d15.py`, 29)
Each action applied once; replay changes nothing; unknown action, missing field, extra field, bad id, key, card or sha rejected with nothing done; wrong-state cards rejected; id order; corrupt, oversized and foreign files don't block the others; state is host-only and survives a restart; corrupt state applies nothing; a crash while applying never applies twice; a failed PR comment is only logged; the runner hook never raises; the table is in the host config only. The git part runs against a real local repository; the board and `gh` are fakes. I also checked that the real remote fetches from the runner's bare environment (service `PATH`, only `HOME` set); the decisions folder does not exist yet, so the list is empty. **Not tested live:** `kanban create` without an assignee through this path, and a real `gh` post from the service.

## Trust
**Anyone who can push to the product-design branch can write a decision, and that includes the VM agent.** This is not a new power: today the agent runs `approve_test_edit` and the unblocks itself, on your instructions. But decisions are **not separated** from the agent. What a real separation would need (not built):
- **Signed commits:** the reviewing session holds a signing key the VM never has; the runner keeps the public key in host-only config and applies a file only if the commit that last changed it verifies (`git verify-commit` against an allowed-signers file). Checking only the branch tip is not enough, because the agent pushes to the same branch.
- **Or a reviewer-only GitHub identity:** decisions on a branch only that identity can push to (branch protection), which the agent's token cannot change. Author and committer names in a commit are not proof.
- **In both cases** the agent must also lose the other route: it runs as the same host user as the runner, so it can edit the ledger, the state file and the kit directly. Real separation needs the runner and its state under a different OS user, with the agent unable to `sudo` or write there.
