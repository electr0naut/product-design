# FXL-1 landed: review of the code, and a pattern across tickets

FXL-1 landed after one review-triggered pass. The proven AC3 bug was fixed, and the stored proof passed. Reading
the first version and the fix of `src/framing.js` in `FXL-1.patch`, I find:
1. **The interface deviates from the ticket.** Candidates have no `end`, and fields use `offset` where the ticket
   says `position`.
2. **Messages with `=` in the prefix are dropped.** The AC3 fix treats any `=` before `8=FIX` on a line as "inside
   a value". A prefix such as `session=ABC 8=FIX...` therefore hides the message.
3. **A candidate without a CheckSum is dropped,** not returned. FXL-2 needs it in order to report
   `missing_checksum`.
4. **Inside an unterminated candidate, a new `8=FIX` after a delimiter is read as a field,** so two messages merge.

Items 3 and 4 overlap FXL-2, which is running now and may fix them. Item 2 is a new bug.

## The pattern

This is the second ticket in a row, after FXL-3, that passes the gates and a clean review while its **interface**
differs from the ticket. The reason is ours: the interfaces are written in the ticket prose, not in the
acceptance criteria. The gates check criteria, and the finder reviews against criteria, so the prose is never
enforced. I've now added an **AC0** to every ticket that hasn't started (FXL-3b, FXL-4 to FXL-7). Each AC0 is an
interface test: the import, the call shape, and the exact result keys.

## For the agent (approved; a board change on unstarted tickets)

1. **Let FXL-2 finish** on its current cards.
2. **Reload the unstarted tickets,** archiving and reloading their cards so the new criteria reach the cards:
   - FXL-3b and FXL-4 to FXL-7;
   - the new **FXL-1b** (`docs/agent-harness/fix-lens/tickets/FXL-1b.md`), right after FXL-2.

   The order becomes FXL-2, FXL-1b, FXL-3b, FXL-4, FXL-5, FXL-6, FXL-7. FXL-4, FXL-5 and FXL-6 must also wait on
   FXL-1b's `scribe`. Do this **while FXL-2 runs**, so nothing that has started is touched. If FXL-2 finishes
   first, wait to reload until FXL-1b's place in the queue is guaranteed.
3. **Copy the ticket files byte for byte,** as before, and log the card commands in `D6-morning.md`.

Mutation on FXL-1 reported 76 surviving mutants out of 278. That's report-only and consistent with items 2 to 4:
the tests don't pin down the boundary rules. FXL-1b's criteria do.
