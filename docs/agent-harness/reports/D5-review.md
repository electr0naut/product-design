# D5 review: host-only kit (`agent-harness` branch `d5-host-kit` @ `441ef62`)

**Approved. Deploy it.** Verified in the reviewing session: `275 passed, 3 skipped in 73.11s`, and ruff is clean.

- **The guard is right:**
  - it checks the package folder and the config file against the recorded mounts;
  - it fails closed when no mounts are recorded;
  - it resolves symlinks.
- **Schemas and overlays now come from the code root,** never from the work folder.
- **`python -P` plus an explicit `PYTHONPATH`** removes the working directory from the import path. The marker test
  shows the property we need.
- **The deploy tool pins an exact sha,** refuses a dirty tree, and backs up the old unit.

## Deploy now (approved here; reversible: re-run with the old sha, or restore the `.bak` unit)

1. Fast-forward the kit's `master` to `441ef62`. It's rebased on `master`, so this isn't a merge commit.
2. Run `python tools/deploy_host_kit.py 441ef62a4b61c6b7881a5994c1acb57ff394ee16 --install-unit`.
3. On the next timer tick, confirm the journal shows `harness.reviewer: kit /home/ubay/.local/share/agent-harness/kit
   @ 441ef62...` and a clean `idle; idle`.
4. **The live marker check:** append a harmless comment to `/srv/lab/agent-harness/src/harness/reviewer.py` that
   prints a marker. Show that the next tick doesn't print it, then revert the edit.
5. Put the outputs in the report: `systemctl --user cat harness-reviewer.service`, the journal lines and the marker
   check.

If auto mode refuses any of this, stop. The user approves it in the VM session.

## Before the user's `sudo`: a rename bypass (D5.1)

**Root-owning a folder isn't enough when its parent belongs to the worker.** The owner of a directory can rename
or replace entries in it, even root-owned ones. `hermes` is uid 1000, so it owns
`/srv/lab/agent-harness` and `work/`.
- **Today:** a worker can `mv .venv-container .venv-old` and drop in its own `.venv-container`. The same goes for
  `work/js-deps`. The `chown` the user ran tonight is bypassable that way.
- **With the D5 line as written,** a worker could rename `src/` the same way.

**Fix:**
1. **Move the JS dependencies out of `work/`**, for example to `/srv/lab/agent-harness/deps/js/node_modules`.
   Update `deps_dir` in the overlay and the config tests. `work/` has to stay worker-owned, so nothing that must
   stay trusted can live under it.
2. **The `sudo` step then becomes:** make the kit's top folder itself root-owned (not recursively), and make
   everything directly in it root-owned recursively, **except `work/`**. That covers `.git`, both venvs, the
   deps, `src/` and the config. Write it as these two exact lines, each with its undo:

   ```bash
   sudo chown root:root /srv/lab/agent-harness
   ```

   ```bash
   sudo find /srv/lab/agent-harness -mindepth 1 -maxdepth 1 ! -name work -exec chown -R root:root {} +
   ```

   Undo: the same two lines with `ubay:ubay`.
3. **Check what still needs to write at the top level.** For example, pytest's cache when the kit's own suite
   runs in the container: use `-p no:cacheprovider`. Mutation runs must write only under `work/` or in a temp
   folder. List anything that breaks.
4. **Report as `D5.1-lockdown.md`** with:
   - the deps move and the tests;
   - the exact `sudo` lines;
   - what you checked would still work afterwards.

   The user runs the lines after reading it. Then, as `hermes`, verify that renaming `src`, `.venv-container` and
   `deps` is refused.

## Answers

1. **`harness.host.toml` from the reviewed commit: yes.** It holds commands the host executes, so it belongs
   with the reviewed code. Machine-specific values stay in `local.toml`.
2. **`.git` root-owned: yes.** The `find` line above covers it. Deploying into the container's copy then means
   `sudo git -C /srv/lab/agent-harness fetch` followed by checking out the reviewed sha.
