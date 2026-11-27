# Harness state

Written by the runner at 2026-11-27T12:59:26+0100. Host-only copy: `state.json`.
Kit: `7c190a2d696add2fb63f4d409a03e34498e018eb`

## What changed
- decision applied D-20261127-4: approved test/timeline.test.js at 80116ec44644 for FXL-10
- decision applied D-20261127-5: unblocked t_587dd3d4 (FXL-10 · gatekeeper (fix 1))

## Tickets
- **SMK-1** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **SMK-2** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-9** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-10** (open): gatekeeper (fix 1): done, implementer: done, implementer (fix 1): done, planner: done, reviewer (fix 1): done, scribe: running, triage: done
- **FXL-11** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-12** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-13** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo

## Blocks
- none

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
