# Handover prompt

Say "do the handover" to run this. It assumes the repo is the only context the
next session has.

---

Your context will be cleared after this turn. A fresh session will only have the
repo. Put anything it needs into `docs/plans/STATUS.md`: current task and next
step, open questions, gotchas, and any uncommitted or stashed work. Commit and
push, confirm the working tree is clean, then stop. Also save this handover
prompt as `docs/prompts/handover.md` so I can just say "do the handover" next
time.

---

Notes for the next session:

- Write the handover into the `## Handover` section at the top of
  `docs/plans/STATUS.md`, replacing the old one rather than appending.
- Include: `main` SHA and CI state, what is merged, the single next step, known
  gaps, environment gotchas (no `gh` CLI, no PyYAML, GitHub helper path, git
  identity, worktree layout), and an explicit statement about uncommitted,
  stashed or WIP work.
- Commit directly to `main` with a `Model: <model name>` trailer, as the owner
  asked, and confirm `git status` is clean afterwards.
