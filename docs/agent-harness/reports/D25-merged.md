# `5b6c863` merged; one of the after-deploy steps will not work as written (D25-code-review2)

## Merged
`agent-harness` `master` is fast-forwarded from `b20b702` to **`5b6c863f6cb4b61d41333d79b32e40276820238a`**. Checked right after the push: the host kit and the container copy are still `b20b702`. Not deployed.

## ⚠ After-deploy step 2: `--dry-run` will **not** show the refusal
In the approved commit a dry run **does not read the board at all** and judges nothing: it prints the command it would run. (`--dry-run` runs nothing, as it always has. I wrote "prints the board read and judges nothing" in `D25-deploy-refusal.md`; I should have said it more plainly.) Run at 15:42 with the branch's check function in dry-run mode, with FXL-16's reviewer running:
```
would run: docker exec -u hermes hermes hermes kanban list --json
(returned: no refusal)
```
So step 2 would end without a refusal, with or without a card running. That would not mean the check is broken. Options:
- **A. A real run of the same sha while a card runs** (`harness-deploy 5b6c863…`, no `--dry-run`). It should stop right after the password prompt, before the fetch, naming the card. **If the check were broken,** it would carry on and redeploy the commit that is already there, with a card running. It is a deploy command, so only Ubay can run it.
- **B. A small change first:** a dry run reads the board (read-only) and says whether it would refuse. A third commit and your review; it can go into this deploy or the next one.
- **C. Drop step 2:** my read-only run of the check function against the real board at 15:37 refused and named the card. That was the branch's code, not the installed tool.

**I suggest B, in a later deploy,** and C for now: no deploy command run as a test. I have changed nothing; tell me if you want B.

## For Ubay, as the review says
**The deploy that installs D25 is run by the old tool, which does not refuse.** Run it only after the reviewer's message that the board is idle.
