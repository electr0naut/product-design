# D18 review (`agent-harness` branch `d18-data-modules` @ `0f8acf4`)

**Approved. Fast-forward `master` to `0f8acf41f0e5d76549c02f0a80ced235bee91bdc`.** Verified in the reviewing
session on a fresh worktree: ruff check and format are clean; `440 passed, 3 skipped, 1 error` (the error is a
test defect, below, not a code defect).

- **The check is right.** It reads the blob from the commit, refuses symlinks and executable files, and accepts
  only `export default ` plus one JSON object or array plus one optional `;`. I ran eleven more texts against
  `data_only` (trailing comma, single quotes, template literal, a call on the next line, `.map` on the next line,
  hex number, getter, computed key, trailing comment, a newline after `default`, `;` on its own line): only the
  last is accepted, and it is still pure data.
- **The `__proto__` limit is accepted.** It cannot run code, and it gives nothing that writing wrong data directly
  would not. The data in these files is guarded by the ticket's reproducibility test and the hidden dictionary
  tests, not by the review.

## One test defect (fix in the next kit change; it does not hold this deploy)

`test_anything_but_pure_data_is_reviewed` errors here with `OSError: [Errno 7] Argument list too long: 'git'`
for the deep-nesting case. The parameter is 200,000 characters, pytest 9.1.1 uses it as the test id, and the id
goes into `PYTEST_CURRENT_TEST`, which is over the kernel's limit for one environment string when the fixture
starts `git`. Under a short id the case passes (`data_only` returns "not one JSON value"). Give that parameter
`pytest.param(..., id="deep-nesting")`.

## Deploy (the user runs this; the queue is blocked, so now is fine)

```
harness-deploy 0f8acf41f0e5d76549c02f0a80ced235bee91bdc
```

## After the deploy (approved here, once)

When the journal shows the runner on kit `0f8acf4`, unblock `t_fec12d61` once and log the command. No decision
file is needed for this one. If the review blocks again for any reason, don't unblock a second time: report it.

Then, when FXL-8 lands, write the evidence and patch as usual. I run the real-browser check on the landed code
from the reviewing session.
