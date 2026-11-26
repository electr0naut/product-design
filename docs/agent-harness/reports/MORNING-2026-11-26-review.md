# Morning steps for the user (2026-11-26): deploy `4b16baa` (D7 + D8 + D9)

The user runs these in the VM session, in order. The agent then continues on its own.

1. **Check that your clone sees the reviewed sha.** Expect `4b16baa9c88a6a6a365eb88016482e18257afd89`:
   `git -C ~/dev/agent-harness fetch -q origin && git -C ~/dev/agent-harness rev-parse origin/master`
2. **Host kit.** Undo: the same line with `c6451f50cc985c100a6c5859507a42c6e1eb6a3a`:
   `! cd ~/dev/agent-harness && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/deploy_host_kit.py 4b16baa9c88a6a6a365eb88016482e18257afd89`
3. **The container's copy**, with a bundle and the hardened flags. Expect the last line to print `4b16baa...`.
   Undo: `sudo git -C /srv/lab/agent-harness reset --hard c6451f5`:
   `git -C ~/dev/agent-harness bundle create /tmp/kit.bundle origin/master`
   `sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false fetch -q /tmp/kit.bundle refs/remotes/origin/master && sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false merge --ff-only FETCH_HEAD && sudo git -C /srv/lab/agent-harness rev-parse HEAD`
4. **The ledger migration:** first look, then run it. Undo: copy `fix-ledger.json.bak` back:
   `! cd ~/.local/share/agent-harness/kit && PYTHONPATH=src .venv/bin/python tools/migrate_fix_ledger.py --dry-run`
   `! cd ~/.local/share/agent-harness/kit && PYTHONPATH=src .venv/bin/python tools/migrate_fix_ledger.py`

## Then the agent (approved here)

1. **Verify:** the runner's journal shows `kit ... @ 4b16baa...`, and the container copy is byte-identical to a
   fresh clone.
2. **Reload FXL-1:** archive its cards and reload it alone. It reruns from scratch on the current trusted `main`,
   which now includes FXL-3.
3. **Load FXL-3b** right after FXL-1's place in the queue. FXL-4 then waits on FXL-3b's `scribe`, in addition
   to its own blockers.
4. **Carry on with FXL-2 to FXL-7 in order,** with per-ticket evidence as before.
