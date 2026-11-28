# D23, second part: the rerun tool keeps Stryker's raw report (D23-review2)

`agent-harness` branch `d23-static-mutants`, **final commit `6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953`**, one commit on `9e04d00`. **Not merged** (`master` is `0dee234`), not deployed, nothing live changed. Waiting for your review.

Diff from `9e04d00`: `tools/rerun_mutation.py` and `tests/test_d22.py`, nothing else.
- Stryker's whole `mutation.json` is copied byte for byte into the ticket's host records, as `<record name>.stryker-report`, and the tool prints its path as `raw_report` (`null` if no report was written).
- **The extension is deliberately not `.json`:** records are found by `*-mutation-rerun-*.json`, so a `.json` copy would be loaded as a second record and break the loader, and with it `STATE.md`. A test checks that one record loads.
- The source is in the container's work folder, so only a plain file whose real path is inside the throwaway tree is copied. A link, on the file or a folder above it, is not followed.

Fresh clone of `6c483e6`: format and ruff clean, **598 passed, 3 skipped**.
```
test_the_rerun_keeps_strykers_whole_report_beside_its_record PASSED [ 25%]
test_a_run_without_a_report_keeps_none PASSED         [ 50%]
test_a_raw_report_that_is_a_link_out_of_the_tree_is_not_copied[the report] PASSED [ 75%]
test_a_raw_report_that_is_a_link_out_of_the_tree_is_not_copied[a folder above it] PASSED [100%]
======================= 4 passed, 20 deselected in 0.99s =======================
```
These use the stand-in engine. That the real Stryker writes its report at this path is shown by my earlier throwaway-container runs, which I read from it. The tool itself has still not run against the live kit; the FXL-9 rerun after the deploy is its first real use.
