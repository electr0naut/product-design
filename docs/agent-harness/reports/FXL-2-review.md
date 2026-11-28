# FXL-2 block: a transient finder failure, not a ticket problem

The retry's review never ran its finder: `reviewer profile call failed (1)`, which is the Qwen call through the
`reviewer` profile, and the runner blocked the card as `transient`. FXL-2's gates passed after its gate pass, so
the ticket is waiting only on its review.

## Decision (as the user's delegate)

1. **Find the cause, read-only.** Read that session's error in the reviewer profile's `state.db` and the gateway
   log at 03:46–03:47: a provider error (rate limit, quota on the token plan, timeout) or something local.
   Run one tiny `reviewer` profile call to check the provider answers. Report it in `FXL-2.md`.
2. **If the provider answers:** clear this card's entry in the reviewer attempts file, and unblock the card
   **once**, as in C2. The review reruns in full. One retry of a transient failure doesn't count as a fix pass,
   and changes nothing in the ledger.
3. **If the provider is out of quota or down:** leave the card blocked, and write down when the quota resets.
   Don't switch the finder to another provider tonight.

## Backlog (D10, after the pilot, not now)

**A transient block should retry by itself once,** after a delay of a few minutes, in deterministic runner code:
a timestamp in the attempts file, a maximum of one automatic retry, and a block after that. Tonight a
person had to decide a retry that the harness can decide.
