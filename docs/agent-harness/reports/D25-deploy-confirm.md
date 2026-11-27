# `5b6c863` deployed and confirmed; the refused load; FXL-16 (D25-code-review2, steps 1 and 3)

Read-only.

## 1. The deploy
- Host kit checked out `5b6c863` at **15:58:00**; the container copy fast-forwarded the same second.
- **Nothing was running:** FXL-16's scribe had completed at 15:56:07 and `accept FXL-16` at 15:56:17. No card was running or ready, then or at this check. **No runner pass spanned the switch** (one ended 15:57:21, the next started 15:58:19).
- 159 tracked files, **0 differ** between host and container; the host tree is clean.
- Fresh-process imports: **29 of 29** with each interpreter. `--help`: **8 of 8** in each. The installed `harness-deploy` answers `--help`, and the deployed tool contains the running-card refusal.
- **One logged failure, harmless:** the first pass on the new kit (15:58:42) logged `publishing state failed (try 1): git push failed: the remote contains work that you do not have`. Your push of `D-20261127-11` landed at 15:58:39, three seconds earlier. The next pass published (`0aab16d`, 15:59:34); the outbox is empty. No other failure, error or traceback line since 15:55; nothing from the alert unit.
- Step 2 is dropped (`D25-code-review3.md`).

## 3. `D-20261127-11`, the load that had to be refused
The runner's PR comment (15:59:28), verbatim:
> `rejected D-20261127-11: already loaded, so nothing was loaded: FXL-16`

The decisions ledger says `rejected` with the same text. **Nothing was loaded:** the registry has 11 entries with one for FXL-16, and the board has one `FXL-16 · triage` card; no card is ready or running. This is the first run of the new path against the real board.

## FXL-16 landed
From the runner's records: **hidden 173 of 173**, no regression; D24: **`acc-trades.test.js` 14 of 14, met**; not held, no block. **Mutation:** `killed 136, survived 9, timeout 0, no tests 1, unrun 0, static (not measured) 19`; no error, complete, static check left out. No scoring folder left.
**Every ticket in the registry is finished and none is held.** No mutation run has errored since FXL-9, whose rerun is done.
