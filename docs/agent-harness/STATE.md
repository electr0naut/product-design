# Harness state

Written by the runner at 2026-11-27T14:06:00+0100. Host-only copy: `state.json`.
Kit: `6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953`

## What changed
- decision applied D-20261127-6: retired 5 hidden test(s) from the fix-lens history
- decision applied D-20261127-7: refreshed the fix-lens copies from 9448c0b99295: design sha256 4c2cb3fd5236, 17 hidden test files

## Tickets
- **SMK-1** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **SMK-2** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-9** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
  - **mutation run errored** (report-only, no result): stryker wrote no report (exit 1): Item.execute (file:///srv/lab/agent-harness/deps/fix-lens/node_modules/(at)stryker-mutator/core/dist/src/concurrent/pool.js:34:28) at async file:///srv/lab/agent-harness
- **FXL-10** (finished): gatekeeper (fix 1): done, implementer: done, implementer (fix 1): done, planner: done, reviewer (fix 1): done, scribe: done, triage: done
- **FXL-11** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-12** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-13** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done

## Blocks
- none

## Holds
- none

## Last hidden-suite result
{'ticket': 'FXL-13', 'enabled': True, 'passed': 121, 'total': 166, 'regressions': [], 'trusted_main': '8881fce6a69d5a4b504ea27ef03848aa0acb1e22'}

## Profiles
| profile | default | fallbacks |
|---|---|---|
| triage | qwen3.7-plus | deepseek-flash (deepseek) |
| planner | gpt-6.2-sol | qwen3.7-plus (alibaba-token-plan), deepseek-flash (deepseek) |
| implementer | gpt-6.2-sol | deepseek-v4.1-flash-1017 (alibaba-token-plan), qwen4-max (alibaba-token-plan), deepseek-flash (deepseek) |
| gatekeeper | deepseek-flash | qwen3.7-plus (alibaba-token-plan) |
| reviewer | deepseek-flash | qwen3.7-plus (alibaba-token-plan) |
| scribe | deepseek-flash | qwen3.7-plus (alibaba-token-plan) |

## Instructions without a report
- FXL-13-landed-review.md
