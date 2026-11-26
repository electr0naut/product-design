# AUDIT: did any worker see the hidden tests? (HIDDEN-suite-review.md)

Read-only, run 2026-11-27 about 00:00 to 00:15 CET.

## Answer
**In every record that still exists, I found no sign that a worker saw the hidden tests.** No hidden test file name, no host-only `acceptance` path, no `work/prove` access since the suite existed, and **no distinctive line of hidden test code** anywhere.
**This is not a clean bill for all workers:** the session records of the **ten round 1 bake-off runs are gone** (I deleted their profiles), and several of those runs were active while hidden files were on disk. Nor can session records show what code run by a worker read. Details under "What this could not cover".

## When the hidden files were exposed
The suite first reached the host at **2026-11-26 14:30:06**. The files were under `work/prove/` only while `harness.acceptance` ran: the driver's run after each landing (window below = scribe card completed to evidence commit) and my two manual runs (window = estimated, 45 s before its history file was written). No ticket landed between 14:30 and 20:02. My other scoring (bake-off, later approval checks) used a separate no-network container.

| run | window |
|---|---|
| FXL-1B | 20:02:11 to 20:02:26 |
| FXL-2B | 20:36:55 to 20:37:14 |
| FXL-3B | 21:02:02 to 21:02:33 |
| FXL-4 | 21:13:07 to 21:13:13 |
| FXL-5 | 21:59:16 to 21:59:40 |
| FXL-4B | 22:09:15 to 22:09:45 |
| FXL-6 | 22:17:53 to 22:18:16 |
| FXL-7 | 22:47:46 to 22:48:00 |
| FXL-8 | 23:44:06 to 23:44:29 |
| manual FXL2B fix head | 20:23:54 to 20:24:39 |
| manual FXL3B fix head | 20:51:31 to 20:52:16 |

## What I searched, and how
1. **Every Hermes session database:** 34 `state.db` files (every profile, the round 2 bake-off profiles, and the default profile; `/opt/data/.hermes/profiles` is the same files as `/opt/data/profiles`, counted once). 15 hold sessions: **1489 sessions, 41691 messages**, of which **96 sessions and 3222 messages since 14:30**. Searched with **no date limit**. Columns: `content` (which includes tool results), `tool_calls`, `reasoning`, `reasoning_content`, `reasoning_details`, `api_content`, `codex_reasoning_items`, `codex_message_items`.
2. **Patterns (case-insensitive regular expressions):** `work/prove|harness-wt-|harness-score-` · `agent-harness/acceptance|acceptance-history|acceptance/fix-lens` · `\bacc-[\w*?\[\]{},-]*\.test\b|\bacc-\*`.
3. **Titles:** all 59 hidden titles as text (58 do not appear verbatim in any ticket or the design; the exception, "unsupported version", I left out as public). The ten distinctive ones you asked for:
   - `acc-analyse.test.js`: "a malformed message between two valid ones"
   - `acc-check.test.js`: "reference vector is valid with SOH and with pipe (CheckSum over SOH)"
   - `acc-decode.test.js`: "enum values that name JavaScript built-ins are unknown values"
   - `acc-dictionary.test.js`: "unknown tag, unknown value and unsupported version give null"
   - `acc-framing.test.js`: "a candidate without CheckSum is still returned, and the next message still found"
   - `acc-limits.test.js`: "message limit: 1,000 accepted, 1,001 refused, warning names both numbers"
   - `acc-page.test.js`: "the textarea cannot leak input through autofill, spellcheck or translation"
   - `acc-render.test.js`: "an unsupported version is labelled and its fields are shown raw, without made-up names"
   - `acc-timeline.test.js`: "a message without a usable 34 changes nothing, even a Logon with 141=Y"
   - `acc-analyse.test.js`: "over a limit nothing is decoded"
4. **Hidden code lines:** all 201 lines of 45 characters or more in the hidden files (none appears in a ticket, the design or the repository's own code and tests), compared with whitespace and escapes removed, over all 3240 messages since 14:30. **Control:** the same search run for 16 lines workers did write found all 16 (126 hits).
5. **Elsewhere:** the Kanban database (card bodies, results, comments, events); files changed since 14:30 under the profiles and `work/` (without `node_modules`, `.git`, `prove`), and separately 321 files under skills, memories, plans, hooks, cron, home and workspace folders; the whole history of the work repository (all refs), the current and retired run files.
6. **Actions inside the windows:** I listed every tool call any session made during the eleven windows. They are the scribe finishing its card and editing its own skill, one `kanban_show`/`kanban_attachments`, and, in FXL-8's window, a round 2 bake-off run writing its own `base.txt`. None reads or lists `work/prove`, `work/`, or a parent of them.

## Hits
| what | hits | judged |
|---|---|---|
| `title: bad tags` | 2 | ordinary wording ("rule 2 checks bad tags") |
| `title: event keys` | 29 | ordinary wording, mostly inside "TimelineEvent keys" |
| `title: header order` | 103 | public wording (technical design, FXL-2.md) |
| `title: logon with 141=y resets the expected number to 1` | 2 | a code comment; paraphrases the ticket's AC10 and design §7 (see below) |
| `title: result keys` | 20 | ordinary wording ("these result keys" in a harness document; "checks result keys") |
| `work/prove` | 4 | before the suite: older sample-repo tickets |

- **No hit at all** for the host acceptance folder or for `acc-*.test.js`.
- **None of the matched titles was used as the name of a test** in any message.
- **`work/prove` (4 hits):** 25 November, before this suite existed: sample-repo cards (PRC-2, RISK-3) saw a `harness-wt-` path in a test error, or listed `work/`. It does show that workers can and do see that folder.
- **The one distinctive title,** "Logon with 141=Y resets the expected number to 1", is a comment (`// ----- Step 1: ... -----`) that `bake-r2-deepseek-v4-pro` wrote into its own code at 23:20:38. The ticket's AC10 reads "A Logon with 141=Y resets the direction's expected number to 1 before its own check" and the design says the same. That session has no path or file-name hit and no hidden code line, and 23:20 is in no exposure window. I read it as paraphrase.
- **Kanban database:** 5 matches, only "header order" (4) and "event keys" (1).
- **Files:** 12 matches, only "header order" (the work repository's `src/framing.js` and `test/framing-f2.test.js`, an old implementer scratch file, a bake-off clone), "event keys" and the Logon comment (round 2 candidates' own scratch files). The skills and memory search: no match.

## What this could not cover
1. **Round 1 bake-off (the main gap).** Profiles `bake-qwen4-max`, `bake-qwen3-8-max`, `bake-qwen3-7-max`, `bake-deepseek-v4-pro`, `bake-glm-5-3` were deleted after BAKEOFF.md, with their session records. Their ten runs (20:16 to 22:51) were active during these windows: FXL-2B (`qwen3-8-max` #1), FXL-3B (`deepseek` #1), FXL-4 (`glm` #1), FXL-5 (`qwen3-8-max` #2), FXL-4B (`qwen3-7-max` #2), FXL-6 (`deepseek` #2), FXL-7 (`glm` #2), and my manual FXL-3B run (`qwen3-8-max` #1, **paused** for its duration). The table also puts `qwen4-max` #1 against the manual FXL-2B run, but only because that window's start is estimated: the run had ended (20:24:28) before I started the scoring, which finished at 20:24:39.
   - **What was checked while the records existed** (BAKEOFF.md), on **tool calls only**: no `work/prove`, `work/runs`, `work/fix-lens`, `work/old`, `work/scratch` path, no relative `../../`, no `acc-*.test.js`. The only `find /` was for the technical design. That check did **not** read tool results or reasoning, did not search titles or code lines, and its other path pattern would not have matched the host folder under `/home`.
   - **What survives, checked now:** the committed code of all ten runs and their final replies: no hidden code line, no distinctive title, no hidden path or file name.
2. **Other deleted throwaway profiles** (`bake-mdl-a` to `-d`, `bake-fbcheck`): single "reply ready" calls.
3. **Code a worker ran.** Gates and tests run worker-written code as the same user in the same container. A read made by such code leaves no session record, and there is no file access log. The committed history shows no such code; code run and not committed is not covered.
4. **Not verified:** whether Hermes ever removes or rewrites messages (for example on context compaction), and any record kept by a model provider.
5. **Not Hermes workers, so not searched:** the Claude spec pass, refuter and prover, which run on the host with read access to a checkout under `work/prove/` (a different folder from the scoring one).
6. A search for text cannot find hidden tests that were read and then only paraphrased. The nearest signal would be work that matches hidden expectations too closely; I did not assess that.

## For BAKEOFF and BAKEOFF-round2
Round 1's report said live workers could never see the hidden files in my scoring, which holds, but did not say that **round 1 candidates ran while the live pipeline's own scoring had hidden files on disk**. Round 2's candidates ran during one such window (FXL-8) and their records, searched here, show nothing. The round 2 report will say the same.

## Deleted and left in place
Deleted: my temporary audit scripts and inputs in the container's `/tmp` (`audit_*`), created in this job. Kept: the audit scripts and raw results on the host in `~/.local/state/agent-harness-bake/audit/`; the six `bake-r2-*` profiles (round 2 still needs them).

## Databases
| profile | sessions | since 14:30 | messages | oldest session | newest |
|---|---|---|---|---|---|
| (default) | 1214 | 0 | 33791 | 04-27 17:37 | 11-24 15:36 |
| bake-r2-codex | 3 | 3 | 99 | 11-26 23:04 | 11-26 23:50 |
| bake-r2-codex62 | 2 | 2 | 44 | 11-26 23:54 | 11-26 23:57 |
| bake-r2-deepseek-v4-1-flash | 3 | 3 | 81 | 11-26 23:54 | 11-27 00:00 |
| bake-r2-deepseek-v4-pro | 3 | 3 | 138 | 11-26 23:03 | 11-26 23:42 |
| bake-r2-qwen3-7-max | 3 | 3 | 115 | 11-26 23:03 | 11-26 23:39 |
| bake-r2-qwen4-max | 3 | 3 | 116 | 11-26 23:02 | 11-26 23:31 |
| cso | 6 | 0 | 14 | 05-14 18:09 | 11-24 15:42 |
| engineer | 1 | 0 | 2 | 11-24 15:42 | 11-24 15:42 |
| gatekeeper | 15 | 0 | 275 | 11-24 20:03 | 11-25 18:49 |
| implementer | 53 | 25 | 2759 | 11-24 21:32 | 11-26 23:28 |
| planner | 38 | 15 | 1102 | 11-24 21:29 | 11-26 23:28 |
| reviewer | 74 | 18 | 362 | 11-24 21:49 | 11-26 23:32 |
| scribe | 33 | 9 | 2079 | 11-24 20:03 | 11-26 23:39 |
| triage | 38 | 12 | 714 | 11-24 20:00 | 11-26 22:53 |

## Every hit
| time | profile | session | ticket (card) | where | matched |
|---|---|---|---|---|---|
| 11-25 17:59:18 | scribe | `local-c08bde9589` | PRC-2 · scribe | tool/terminal (content) | work/prove |
| 11-25 22:58:24 | implementer | `local-f5264b42af` | RISK-3 · implementer (fix 1) | tool/read_file (content) | work/prove |
| 11-25 22:58:47 | implementer | `local-f5264b42af` | RISK-3 · implementer (fix 1) | tool/read_file (content) | work/prove |
| 11-25 23:01:25 | scribe | `local-58818ccbf1` | RISK-3 · scribe | tool/terminal (content) | work/prove |
| 11-26 01:01:23 | planner | `local-483bd38a0e` | FXL-1 · planner | tool/read_file (content) | title: result keys |
| 11-26 01:01:23 | planner | `local-483bd38a0e` | FXL-1 · planner | tool/read_file (content) | title: result keys |
| 11-26 03:08:40 | triage | `local-eec8b78ee8` | FXL-2 · triage | tool/read_file (content) | title: result keys |
| 11-26 03:08:40 | triage | `local-eec8b78ee8` | FXL-2 · triage | tool/read_file (content) | title: result keys |
| 11-26 03:15:35 | planner | `local-4cf7a1bad9` | FXL-2 · planner | assistant (tool_calls) | title: header order |
| 11-26 03:15:35 | planner | `local-4cf7a1bad9` | FXL-2 · planner | assistant (reasoning) | title: header order |
| 11-26 03:15:35 | planner | `local-4cf7a1bad9` | FXL-2 · planner | assistant (reasoning_content) | title: header order |
| 11-26 03:16:26 | planner | `local-4cf7a1bad9` | FXL-2 · planner | assistant (tool_calls) | title: header order |
| 11-26 03:17:30 | planner | `local-4cf7a1bad9` | FXL-2 · planner | assistant (tool_calls) | title: header order |
| 11-26 03:18:18 | implementer | `local-039a63e2ec` | FXL-2 · implementer | tool/kanban_show (content) | title: header order |
| 11-26 03:20:19 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:21:25 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:22:39 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:24:19 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:25:24 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:29:12 | implementer | `local-039a63e2ec` | FXL-2 · implementer | assistant (tool_calls) | title: header order |
| 11-26 03:31:57 | implementer | `local-c8d46ca150` | FXL-2 · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 03:32:06 | implementer | `local-c8d46ca150` | FXL-2 · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 03:33:58 | implementer | `local-c8d46ca150` | FXL-2 · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 03:34:48 | implementer | `local-c8d46ca150` | FXL-2 · implementer (fix 1) | assistant (tool_calls) | title: header order |
| 11-26 03:39:09 | reviewer | `local-d838c8accf` | not linked to a card | user (content) | title: header order |
| 11-26 09:06:33 | reviewer | `local-a1afa70846` | not linked to a card | user (content) | title: header order |
| 11-26 09:11:01 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 09:11:01 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 09:12:10 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 09:12:10 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 09:23:26 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 09:23:26 | reviewer | `local-a1afa70846` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 09:25:58 | reviewer | `local-56b0493e47` | not linked to a card | user (content) | title: header order |
| 11-26 09:29:08 | reviewer | `local-56b0493e47` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 09:29:08 | reviewer | `local-56b0493e47` | not linked to a card | assistant (reasoning) | title: bad tags |
| 11-26 09:29:08 | reviewer | `local-56b0493e47` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 09:29:08 | reviewer | `local-56b0493e47` | not linked to a card | assistant (reasoning_content) | title: bad tags |
| 11-26 09:30:05 | scribe | `local-cb4a5be3be` | FXL-2 · scribe | tool/terminal (content) | title: header order |
| 11-26 09:30:43 | scribe | `local-cb4a5be3be` | FXL-2 · scribe | tool/read_file (content) | title: header order |
| 11-26 09:34:24 | planner | `local-099b9a70ec` | FXL-1b · planner | tool/terminal (content) | title: header order |
| 11-26 09:34:32 | planner | `local-099b9a70ec` | FXL-1b · planner | tool/read_file (content) | title: header order |
| 11-26 09:34:32 | planner | `local-099b9a70ec` | FXL-1b · planner | tool/read_file (content) | title: header order |
| 11-26 09:36:15 | implementer | `local-6a3ebea1bb` | FXL-1b · implementer | tool/read_file (content) | title: header order |
| 11-26 09:36:54 | implementer | `local-6a3ebea1bb` | FXL-1b · implementer | tool/read_file (content) | title: header order |
| 11-26 09:40:36 | implementer | `local-6a3ebea1bb` | FXL-1b · implementer | assistant (tool_calls) | title: header order |
| 11-26 09:40:40 | implementer | `local-6a3ebea1bb` | FXL-1b · implementer | tool/read_file (content) | title: header order |
| 11-26 09:41:48 | implementer | `local-6a3ebea1bb` | FXL-1b · implementer | assistant (tool_calls) | title: header order |
| 11-26 14:39:44 | planner | `local-d63bda43c9` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 14:39:50 | planner | `local-d63bda43c9` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 14:40:04 | planner | `local-d63bda43c9` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 14:42:53 | implementer | `local-3d86b3feef` | FXL-1B · implementer | tool/read_file (content) | title: header order |
| 11-26 14:43:01 | implementer | `local-3d86b3feef` | FXL-1B · implementer | tool/terminal (content) | title: header order |
| 11-26 14:43:07 | implementer | `local-3d86b3feef` | FXL-1B · implementer | tool/terminal (content) | title: header order |
| 11-26 14:45:08 | implementer | `local-3d86b3feef` | FXL-1B · implementer | assistant (tool_calls) | title: header order |
| 11-26 14:46:19 | implementer | `local-3d86b3feef` | FXL-1B · implementer | assistant (tool_calls) | title: header order |
| 11-26 14:52:09 | implementer | `local-3ba0580f32` | FXL-1B · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 15:22:09 | planner | `local-1017b9e564` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 15:22:16 | planner | `local-1017b9e564` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 15:22:21 | planner | `local-1017b9e564` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 15:24:20 | implementer | `local-bc5fd3813a` | FXL-1B · implementer | tool/terminal (content) | title: header order |
| 11-26 15:25:09 | implementer | `local-bc5fd3813a` | FXL-1B · implementer | tool/terminal (content) | title: header order |
| 11-26 15:27:28 | reviewer | `local-b9de9c4d74` | not linked to a card | user (content) | title: header order |
| 11-26 17:53:33 | reviewer | `local-9af3f16c93` | not linked to a card | user (content) | title: header order |
| 11-26 18:05:08 | implementer | `local-84400c3d97` | FXL-1B · implementer (fix 2) | tool/read_file (content) | title: header order |
| 11-26 18:13:26 | reviewer | `local-debe64306c` | not linked to a card | user (content) | title: header order |
| 11-26 18:21:11 | reviewer | `local-d887d08368` | not linked to a card | user (content) | title: header order |
| 11-26 18:37:26 | planner | `local-fa000217ae` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 18:37:42 | planner | `local-fa000217ae` | FXL-1B · planner | tool/terminal (content) | title: header order |
| 11-26 18:39:25 | implementer | `local-73ddf9eac0` | FXL-1B · implementer | tool/read_file (content) | title: header order |
| 11-26 18:39:50 | implementer | `local-73ddf9eac0` | FXL-1B · implementer | tool/read_file (content) | title: header order |
| 11-26 18:39:50 | implementer | `local-73ddf9eac0` | FXL-1B · implementer | tool/read_file (content) | title: header order |
| 11-26 18:40:48 | implementer | `local-73ddf9eac0` | FXL-1B · implementer | tool/terminal (content) | title: header order |
| 11-26 18:43:09 | reviewer | `local-fada8d3cfb` | not linked to a card | user (content) | title: header order |
| 11-26 19:02:38 | reviewer | `local-34602d1b60` | not linked to a card | user (content) | title: header order |
| 11-26 19:06:24 | reviewer | `local-34602d1b60` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 19:06:24 | reviewer | `local-34602d1b60` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 19:07:55 | reviewer | `local-34602d1b60` | not linked to a card | tool/session_search (content) | title: header order |
| 11-26 19:11:49 | implementer | `local-16cdb72701` | FXL-1B · implementer (fix 3) | tool/read_file (content) | title: header order |
| 11-26 19:12:00 | implementer | `local-16cdb72701` | FXL-1B · implementer (fix 3) | tool/read_file (content) | title: header order |
| 11-26 19:57:37 | reviewer | `local-2b696720a8` | not linked to a card | user (content) | title: header order |
| 11-26 20:05:30 | planner | `local-7789fc37b9` | FXL-2B · planner | tool/read_file (content) | title: header order |
| 11-26 20:05:30 | planner | `local-7789fc37b9` | FXL-2B · planner | tool/read_file (content) | title: header order |
| 11-26 20:07:38 | implementer | `local-23ccd50a82` | FXL-2B · implementer | tool/read_file (content) | title: header order |
| 11-26 20:10:31 | implementer | `local-404682f976` | FXL-2B · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 20:10:40 | implementer | `local-404682f976` | FXL-2B · implementer (fix 1) | tool/read_file (content) | title: header order |
| 11-26 20:10:58 | implementer | `local-404682f976` | FXL-2B · implementer (fix 1) | tool/terminal (content) | title: header order |
| 11-26 20:34:15 | reviewer | `local-ca94ba6dc7` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 20:34:15 | reviewer | `local-ca94ba6dc7` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 21:05:11 | planner | `local-8b23a7e821` | FXL-4 · planner | tool/read_file (content) | title: header order |
| 11-26 21:07:17 | implementer | `local-bded6ec462` | FXL-4 · implementer | tool/read_file (content) | title: header order |
| 11-26 21:10:40 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 21:10:40 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 21:10:40 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 21:10:40 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 21:10:52 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 21:10:52 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 21:10:52 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 21:10:52 | reviewer | `local-f676eb7933` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 21:19:25 | implementer | `local-a0814f5095` | FXL-5 · implementer | tool/read_file (content) | title: header order |
| 11-26 21:46:40 | triage | `local-269c4f4cd7` | FXL-5 · triage | assistant (tool_calls) | title: event keys |
| 11-26 21:47:31 | planner | `local-986226f6e3` | FXL-5 · planner | user (content) | title: event keys |
| 11-26 21:47:40 | planner | `local-986226f6e3` | FXL-5 · planner | tool/kanban_show (content) | title: event keys |
| 11-26 21:48:27 | planner | `local-986226f6e3` | FXL-5 · planner | assistant (tool_calls) | title: event keys |
| 11-26 21:51:04 | implementer | `local-b3b1125877` | FXL-5 · implementer | tool/read_file (content) | title: header order |
| 11-26 21:56:22 | reviewer | `local-543c313b27` | not linked to a card | assistant (reasoning) | title: event keys |
| 11-26 21:56:22 | reviewer | `local-543c313b27` | not linked to a card | assistant (reasoning_content) | title: event keys |
| 11-26 22:03:03 | implementer | `local-dd6a7edf90` | FXL-4B · implementer | tool/read_file (content) | title: header order |
| 11-26 22:14:07 | implementer | `local-6b23f9e3d1` | FXL-6 · implementer | tool/read_file (content) | title: header order |
| 11-26 22:16:36 | reviewer | `local-374ef62f32` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 22:16:36 | reviewer | `local-374ef62f32` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 22:21:24 | planner | `local-4137896883` | FXL-7 · planner | tool/read_file (content) | title: header order |
| 11-26 22:24:21 | implementer | `local-207f29b1c6` | FXL-7 · implementer | tool/read_file (content) | title: header order |
| 11-26 22:35:56 | implementer | `local-6c330ae80b` | FXL-7 · implementer | tool/read_file (content) | title: header order |
| 11-26 22:41:48 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 22:41:48 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 22:41:48 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 22:41:48 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 22:44:39 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 22:44:39 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning) | title: result keys |
| 11-26 22:44:39 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 22:44:39 | reviewer | `local-71784d0ee6` | not linked to a card | assistant (reasoning_content) | title: result keys |
| 11-26 23:04:52 | bake-r2-qwen4-max | `local-96cc09bd25` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:07:17 | bake-r2-qwen4-max | `local-96cc09bd25` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: event keys |
| 11-26 23:07:17 | bake-r2-qwen4-max | `local-96cc09bd25` | bake-off round 2, FXL-5 | assistant (reasoning) | title: event keys |
| 11-26 23:07:17 | bake-r2-qwen4-max | `local-96cc09bd25` | bake-off round 2, FXL-5 | assistant (reasoning_content) | title: event keys |
| 11-26 23:10:11 | bake-r2-qwen3-7-max | `local-808acd6f0b` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:15:42 | bake-r2-deepseek-v4-pro | `local-b48f800560` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:20:38 | bake-r2-deepseek-v4-pro | `local-b48f800560` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: logon with 141=y resets the expected number to 1 |
| 11-26 23:21:50 | bake-r2-deepseek-v4-pro | `local-b48f800560` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: logon with 141=y resets the expected number to 1 |
| 11-26 23:28:58 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:30:02 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: event keys |
| 11-26 23:31:12 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | tool/terminal (content) | title: event keys |
| 11-26 23:31:38 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: event keys |
| 11-26 23:31:45 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | tool/read_file (content) | title: event keys |
| 11-26 23:31:56 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | assistant (content) | title: event keys |
| 11-26 23:31:56 | bake-r2-codex | `local-9666dfde01` | bake-off round 2, FXL-5 | assistant (codex_message_items) | title: event keys |
| 11-26 23:32:24 | bake-r2-qwen4-max | `local-045d5d1bae` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:37:04 | bake-r2-qwen4-max | `local-045d5d1bae` | bake-off round 2, FXL-5 | tool/terminal (content) | title: header order |
| 11-26 23:38:28 | reviewer | `local-0fb6851511` | not linked to a card | assistant (reasoning) | title: header order |
| 11-26 23:38:28 | reviewer | `local-0fb6851511` | not linked to a card | assistant (reasoning_content) | title: header order |
| 11-26 23:39:27 | bake-r2-qwen3-7-max | `local-a290ffa287` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:43:08 | bake-r2-deepseek-v4-pro | `local-478d83fd76` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:44:23 | bake-r2-deepseek-v4-pro | `local-478d83fd76` | bake-off round 2, FXL-5 | assistant (reasoning) | title: event keys |
| 11-26 23:44:23 | bake-r2-deepseek-v4-pro | `local-478d83fd76` | bake-off round 2, FXL-5 | assistant (reasoning_content) | title: event keys |
| 11-26 23:47:46 | bake-r2-deepseek-v4-pro | `local-478d83fd76` | bake-off round 2, FXL-5 | assistant (reasoning) | title: event keys |
| 11-26 23:47:46 | bake-r2-deepseek-v4-pro | `local-478d83fd76` | bake-off round 2, FXL-5 | assistant (reasoning_content) | title: event keys |
| 11-26 23:50:54 | bake-r2-codex | `local-8d73c9a738` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:55:02 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | tool/terminal (content) | title: header order |
| 11-26 23:56:10 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | assistant (reasoning) | title: event keys |
| 11-26 23:56:10 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | assistant (reasoning_content) | title: event keys |
| 11-26 23:57:00 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: event keys |
| 11-26 23:57:07 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | tool/terminal (content) | title: event keys |
| 11-26 23:57:23 | bake-r2-deepseek-v4-1-flash | `local-3b740fcce8` | bake-off round 2, FXL-5 | assistant (content) | title: event keys |
| 11-26 23:57:40 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | tool/read_file (content) | title: header order |
| 11-26 23:58:53 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | assistant (tool_calls) | title: event keys |
| 11-26 23:59:25 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | tool/terminal (content) | title: event keys |
| 11-26 23:59:42 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | tool/terminal (content) | title: event keys |
| 11-26 23:59:57 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | assistant (content) | title: event keys |
| 11-26 23:59:57 | bake-r2-codex62 | `local-a18ee4600a` | bake-off round 2, FXL-5 | assistant (codex_message_items) | title: event keys |
| 11-27 00:00:11 | bake-r2-deepseek-v4-1-flash | `local-0ec52cee26` | bake-off round 2, FXL-5 | tool/terminal (content) | title: header order |
