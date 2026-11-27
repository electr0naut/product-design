# Harness state

Written by the runner at 2026-11-28T00:16:04+0100. Host-only copy: `state.json`.
Kit: `ccbaea983b26d0df710e6cafd1e4968dcd6a0d50`

## What changed
- decision applied D-20261127-19: loaded 5 ticket(s) from 2a7550244286. FXL-22: triage t_e6592dfb, gate t_7abd7fb5, triage waits on nothing. FXL-23: triage t_b6621679, gate t_42672b13, triage waits on accept FXL-22. FXL-24: triage t_96a6ccf1, gate t_64085dc0, triage waits on accept FXL-23. FXL-25: triage t_cb1e1642, gate t_aabb57a4, triage waits on accept FXL-24. FXL-26: triage t_60da39c7, gate t_24680da2, triage waits on accept FXL-21, accept FXL-22, accept FXL-25 [commit 44f86c2be028, 2026-11-27T23:13:25+00:00, signature: by a listed key]

## Tickets
- **SMK-1** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **SMK-2** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-9** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-10** (finished): gatekeeper (fix 1): done, implementer: done, implementer (fix 1): done, planner: done, reviewer (fix 1): done, scribe: done, triage: done
- **FXL-11** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-12** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-13** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-17** (finished): gatekeeper (fix 1): done, implementer: done, implementer (fix 1): done, planner: done, reviewer (fix 1): done, scribe: done, triage: done
- **FXL-14** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-15** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-16** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-18** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-19** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-20** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-21** (finished): gatekeeper: done, implementer: done, planner: done, reviewer: done, scribe: done, triage: done
- **FXL-22** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: running
- **FXL-23** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-24** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-25** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-26** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo

## Blocks
- none

## Holds
- none

## Last hidden-suite result
{'ticket': 'FXL-21', 'enabled': True, 'passed': 214, 'total': 214, 'regressions': [], 'trusted_main': 'e23113c3cd40e591be96ca451f587aea0465ea16'}

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
- none
