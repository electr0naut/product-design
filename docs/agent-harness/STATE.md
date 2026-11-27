# Harness state

Written by the runner at 2026-11-27T12:50:27+0100. Host-only copy: `state.json`.
Kit: `7c190a2d696add2fb63f4d409a03e34498e018eb`

## What changed
- block: FXL-10 · gatekeeper (fix 1)

## Tickets
- **SMK-1** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **SMK-2** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-9** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-10** (open): gatekeeper (fix 1): blocked, implementer: done, implementer (fix 1): done, planner: done, reviewer (fix 1): todo, scribe: todo, triage: done
- **FXL-11** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-12** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-13** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo

## Blocks
- FXL-10 · gatekeeper (fix 1) (`t_587dd3d4`), head `80116ec44644d7b6f335f8a99271296b8da16800`: FXL-10: the fix pass edited or deleted tests that exist on base (test/timeline.test.js); a person must decide

## Holds
- none

## Last hidden-suite result
{'ticket': 'FXL-9', 'enabled': True, 'passed': 77, 'total': 166, 'regressions': [], 'trusted_main': '60b1211023d1f00874e6231d5c98c94501613581'}

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
- D22-review.md
