# FXL-11 landed: reviewed, clean

Trusted `main` `fa78e7b`, evidence `fix-lens/runs/FXL-11.md`. Rebuilt here from the published patch. No fix
pass, no block, no reviewer finding.

| check | result |
|---|---|
| hidden suite, run here on the rebuilt tree | **98 pass**, the same as the runner's isolated run; `acc-orders` 10 of 10; no regression |
| the project's own tests | the 15 new tests pass |
| `orderGroups` and `findOrder` against the independent build, 60,000 random logs | the same groups, the same members and the same message numbers every time. **One difference in order only:** when a message has OrigClOrdID 41 before ClOrdID 11, FXL-11 lists them in field order and my build lists 11 first. The design says "order of first appearance" and does not pin it inside one message; FXL-11's reading is the literal one |
| does anything later depend on that? | no: with FXL-9, FXL-10 and FXL-11's modules put into the independent v1.2 build, every v1.2 hidden test still passes (163 of 166; the 3 that fail are the old `acc-render` page tests, due to be retired before FXL-14) |
| the argument is not changed; 1,000 messages | confirmed; 2 ms |

**The six listed survivors are equivalent mutants,** not gaps: they change the union-find's path compression
and union-by-size, which affect speed and never the result. Nothing to do.

**FXL-11 counts as landed clean** for `V12-go-review4.md`.
