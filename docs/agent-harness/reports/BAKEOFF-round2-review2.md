# Bake-off round 2: two more candidates and a cost column

Round 2 stays as instructed. Add the following, after the current runs finish.

1. **Two more candidates, under the same conditions** (two runs each, no fallbacks, throwaway profiles, scratch
   clones, FXL-5 as first written, the design readable, no plan):
   - `deepseek-v4.1-flash-1017` through `alibaba-token-plan`;
   - `gpt-6.2-sol` through `openai-codex`.

   Run each only if it answered in the `MODELS-review.md` check. If one did not, say so in the report and skip
   it.
2. **A cost column for every run, old and new:** input tokens, cached input tokens and output tokens as the
   provider reports them, and wall-clock minutes. If the Alibaba plan shows what a run consumed from the quota
   (credits or requests), add that figure and say where you read it.

The question this answers: whether `qwen4-max` is worth its time and quota as the first fallback, or whether
`deepseek-v4.1-flash-1017` does the same ticket as well for less. Don't change any live profile from this.
