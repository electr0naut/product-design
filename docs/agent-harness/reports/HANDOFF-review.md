# Write a handoff file, so a fresh session can take over (instruction)

**Why:** the VM session has run for more than a day. It is to be restarted from files, not from its memory.
The standing rules are drafted in `docs/agent-harness/RULES.md` (Ubay is reviewing it). What that file cannot
hold is the current state of the VM, which only you know.

**Do this now; it is read-only on the VM apart from writing the file.** It does not wait for FXL-8.

Write `docs/agent-harness/HANDOFF.md` with only what a new session could not find out from the repositories:

1. **What is running and how it was started:** the evidence driver (command line, start file, log path, how you
   check it is alive), the watcher loop, the tmux sessions, timers and services, anything else left in the
   background.
2. **Where things are:** the kit development folders and their branches, the host kit, the container copy, the
   host-only state folder and what each file in it is for, the scratch clones and throwaway profiles that still
   exist, and the two `/tmp/dsprobe.py` files.
3. **Work in flight:** each instruction file that has no report yet, with its state. The bake-off runs done and
   pending. FXL-8's state.
4. **How you do the recurring jobs, as commands:** loading tickets, restarting the driver, running the hidden
   suite on a head, publishing evidence, commenting on the pull request.
5. **Anything you do by habit that is in no file.** If `RULES.md` contradicts a habit, or misses a rule you
   follow, list it under "Differences from RULES.md". Don't change `RULES.md`.

No secret values. Paths and names only. Comment on pull request #47 when it is pushed.
