# D27 part 2 proposal: how a Qwen model would review while Claude is at its limit (D27-go-review2)

**Nothing is built. The model is not chosen** (`D27-bakeoff.md`).

## The path
When part 1 raises a usage limit (nothing else does this), and the ticket is not high tier, and an independent model is left, the runner **starts the review again from the first Claude step on the fallback**: one reviewer per review, never half and half. The fallback is a function with `claude`'s signature, calling **a new profile `reviewer-fallback`** (cloned from `triage`, one model, **no `fallback_providers`**, so no silent switch), named in the deploy note. No new credential or host; no live profile changes.

| step | Claude today | fallback | |
|---|---|---|---|
| refute | `--tools Read` in a worktree at the head | **no file tool.** The host puts the sources at the reviewed commit, from the trusted repo, into the prompt | shown in the bake-off |
| spec pass | ticket, design (about 35,000 characters), diff, `Read` | the same text plus that source pack; over a size limit set in config, **wait for Claude** | **not measured** |
| prove | `Read`, `Write`, `Edit` in a scratch worktree | answers with the usual fields **plus the test's source**; the host writes it, no links followed, to **one new file** matching the test globs; then the same confined run and the same judgement. One or two existing tests are in the pack for the style | **not measured**; narrower than today |

## Confinement
- The model gets text and returns text. With `-t todo` it can still see a to-do list and a tool search (`qwen4-max` used the search 30 times). **The build must offer no tool if Hermes allows it,** and in any case read the session afterwards: **any tool message other than those two discards the answer** (a fault).
- **This is weaker than "cannot":** it rests on Hermes' tool settings, inside the live container where the profiles' secrets are. A direct call to the provider with no agent would be stronger but needs the runner to hold the key: a new handling of a credential, **not proposed**.
- **Schemas** are not enforced by the provider as `--json-schema` is: the kit validates, asks once more, then treats it as a fault and **waits for Claude**. A time-out, a non-zero exit or a repetition loop: the same. A fault never lands anything.
- **No dollar cap.** Instead a limit on calls per card (proposed 12) and 900 s per call. The fallback hitting a limit of its own: wait.

## Independence (rule 3)
Excluded: the finder's model and every model that planned or implemented the ticket, **as actually used**. The session table is not enough (FXL-16: a switch in mid-session does not show). The runner would count the model of **each API call** in the ticket's profile logs; **if that cannot be established, the ticket waits.** From today's settings: the planner and the finder fall back to `qwen3.7-plus`; the implementer to `deepseek-v4.1-flash-1017`, then `qwen4-max`. So `qwen4-max` is excluded only after the implementer's second fallback. Of the ten v1.2 tickets, going by the session tables, your landing reviews and `FXL-16-fallback.md`: `qwen4-max` was eligible on all, `qwen3.7-plus` on all but FXL-16. **For both,** I have not rechecked the other tickets' logs for a switch in mid-session.

## Visible (rule 5)
`review.json`, the evidence file, `STATE.md` and the landing comment: "reviewed on the fallback model `<name>`, Claude at its usage limit since `<time>`", with the exclusion check (which models the ticket used).

## What cannot be made equal
Reading on demand (the pack works because FIX Lens is small; a larger repository needs a rule for choosing files, or waits); enforced output; a spending cap; writing and fixing a test in place; and judgement, **measured for one step of three**. The design, ticket and sources go to Alibaba, as they do when a Qwen model plans or implements. The same plan is the implementer's fallback, so when Codex and Claude are both limited, both loads land on it; its quota is not visible to me.

## For you to decide
1. **When to switch:** at the first limit, or only if the named reset is further off than some time (say 1 hour)? A short wait keeps Claude as reviewer at little cost. I propose the threshold.
2. **Before the model choice:** a second free bake-off on the **spec pass and prove**, on states with proven bugs (FXL-1 and FXL-1B) and a few clean ones. I propose it; I have not started it.
