# FXL-12 landed: reviewed, clean; one reading of the design to settle. And the D23 deploy

## The deploy of `6c483e6`
`D23-deploy-confirm.md` is accepted. Ubay ran the deploy line, and it switched host and container at 13:41:18,
between FXL-12's gate (13:40:59) and FXL-13's triage (13:41:23): no worker card was running. The deployed commit
is the one approved in `D23-code-review.md`. FXL-12's gates ran on the old kit and FXL-13 runs wholly on the new
one. Run `tools/rerun_mutation.py FXL-9` when FXL-13 has landed and no card is running, as you plan.

## FXL-12
Trusted `main` `ea0b353`, evidence `fix-lens/runs/FXL-12.md`. Rebuilt here from the published patch. No fix pass,
no block, no reviewer finding.

| check | result |
|---|---|
| hidden suite, run here on the rebuilt tree | **115 pass**, the same as the runner's isolated run; `acc-summary` 17 of 17; no regression |
| the project's own tests | the 24 new tests pass |
| `tradeSummary` against the independent build, 100,000 random logs (15,937 with fills, 46,032 with unmatched reports), with and without `shown` | **one difference in reading**, below; 0 differences once the independent build takes FXL-12's reading |
| later tickets | with FXL-12's module in the independent v1.2 build, every v1.2 hidden test still passes |
| the arguments are not changed; no `NaN` in any result | confirmed |

**FXL-12 counts as landed clean** for `V12-go-review4.md`.

## The reading the design does not settle
Design section 13 says an unmatched TradeCancel or TradeCorrect "is remembered by its OrderID and ExecID, so a
resend of it is not counted again". It does not say what happens when a **later** report names that remembered
ExecID in its ExecRefID.
- **FXL-12:** the remembered key is only for spotting a resend. A later report that names it has named no
  execution, so it is unmatched too, and a TradeCorrect then makes an execution from its own fields.
- **The independent build:** the remembered key counts as `cancelled`, so the later report changes nothing and
  is not unmatched.

In 100,000 random logs the two differ in about 3 in 1,000; in real logs it needs a cancel or correction that
points at another cancel or correction which itself pointed at nothing. No hidden test covers it. I think
FXL-12's reading is the better one: the report does name something that is not an execution in the log, and the
note on the page exists to say so. It is a design clarification, so it goes to Ubay; nothing is changed
meanwhile.

## Mutation
187 killed, 19 survived (FXL-12's gates ran before D23, so static mutants are not yet counted apart). I have not
classified these 19; the comparison above says the behaviour is right. They go to the follow-up ticket's list.
