# FXL-22 and FXL-23 blocked at triage: the card context cuts the ticket at 4 KB

**Nothing was changed or unblocked by me.** At 00:25 the queue is stopped: FXL-22 and FXL-23 triage blocked (`needs_input`), nothing running, FXL-24 waits on `accept FXL-22`. The runner posted both blocks.

## The likely cause
The loader hands the ticket to triage in the parent card's result. `hermes kanban context` cuts each such field: `_CTX_MAX_FIELD_BYTES = 4 * 1024` (`hermes_cli/kanban_db_context.py:25`).

| card | ticket (characters) | what its context shows now |
|---|---|---|
| FXL-22 triage | 7,779 | `… [truncated, 3620 chars omitted]`. **The signature `findOrder(groups, id, number)` is nowhere in the context;** the ticket gives it, and AC8 defines it. The block asks exactly for it (it calls the intro sentence "AC10") |
| FXL-23 triage | 4,527 | AC9 cut: `a fi… [truncated, 368 chars omitted]`. The block reason quotes this line |

- The tickets themselves and the parent cards hold the full text. **So the answers to both questions are already in the tickets.**
- **An unblock alone would probably meet the same cut** (my inference).
- **FXL-26 is 5,981** characters, so it is exposed too. FXL-24 (2,830) and FXL-25 (3,452) are under the limit.
- **Earlier long tickets:** the context Hermes builds **now** for FXL-12, FXL-14 and FXL-21 is cut too, and they passed. **I have not checked what their triage, planner or implementer received then, or whether they read the full parent card.** Worth checking: a role may have worked from part of a ticket. (The review's spec pass reads the host's full copy.)

Possible fixes, your choice, none tried: the card text tells each role to read the parent card in full; the loader puts the ticket where it is not cut (a body is cut at 8 KB, so FXL-22 would only just fit); a ticket file in the work folder.

## FXL-23 started while FXL-22 was blocked: the runner, by its rule
`queue.relink_bounced`: a ticket **blocked at triage** is skipped if the next one declares no dependency on it. At 00:19:23 it unlinked FXL-23 from `accept FXL-22` and triage started (log 00:20:11). **Had FXL-23 passed triage, it would have been built before FXL-22,** not in the order of `AWAY-plan.md` row 4. When FXL-23 blocked too, the same rule moved FXL-24 onto `accept FXL-22` (00:24:18), which stopped the queue. If the v1.4 order is required, it needs declared dependencies or a hold; check this before unblocking.

(My first look took the missing link for an unexplained board change; the runner's log shows it.)
