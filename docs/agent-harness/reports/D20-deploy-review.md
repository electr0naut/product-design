# D20 deployed by Ubay: two things to confirm with the live checks (instruction)

Ubay ran `harness-deploy c06cd273c5c47dec63a9c008c4206f9e5c53525f --install-unit`. The output was:

```
deployed: host kit c06cd273c5c4, container c06cd273c5c4, alert script unchanged
undo: harness-deploy c06cd273c5c47dec63a9c008c4206f9e5c53525f  and  sudo git -C /srv/lab/agent-harness reset --hard c06cd273c5c47dec63a9c008c4206f9e5c53525f  (the reset needs sudo)
```

Read-only, and report with the three live checks of `D20-code-review.md`:

1. **The units.** The output does not mention them. Show `systemctl --user cat harness-reviewer.service` and
   `harness-reviewer-alert.service`: the runner's unit names `OnFailure=harness-reviewer-alert.service`, and
   both run the host kit at `c06cd27`. If the alert unit is missing, say so and stop; installing it is Ubay's.
2. **The undo line.** It names the commit that was just deployed, not the one before it (`76b094f`). Find out
   whether the command had already been run once, or whether the tool prints the new commit as the undo. If it
   is the tool, note it for the next kit change: the undo must name the previous commit.

The fixture ticket of check 1 still needs Ubay's yes in your session.
