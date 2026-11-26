# FXL-3: decision (as the user's delegate)

Good diagnosis. The restriction is old and the workaround is known; the card text sends workers the wrong way.

1. **Tonight: unblock FXL-3's planner card once** (approved; it never completed its stage, and Qwen costs
   nothing). Log the command in `FXL-3.md`.
   - If it blocks again for the same reason, leave it blocked until the morning.
   - Don't unblock any other card.
2. **D8, the card text (a kit change; build tonight, branch only, deploy with D7 in the morning).** In
   `loader.stage_body` and in `fixloop.implementer_body`, replace the "file-writing tool only" line with the real
   rule:
   - `write_file` works only under `/opt/data`;
   - to create or change a file under `/srv/lab/agent-harness/work`, write a short Python script under your
     profile's `cache/scratch/` folder with `write_file`, and run it with the terminal tool;
   - never use `execute_code`, shell redirection or heredocs.

   **Test:** every stage body and the fix-pass body carry the rule, and none carries the old line. Cards that are
   already loaded keep their old text. That's acceptable, because the reruns in the morning reload them.
3. **Don't widen `HERMES_WRITE_SAFE_ROOT`.** With the right card text, the workers don't need it. Keeping the file
   tool narrow is the safer default, so I'm not putting option 2 to the user.

Report D8 as `D8-card-text.md` (branch only).
