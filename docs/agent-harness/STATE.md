# Harness state

Written by the runner at 2026-11-27T19:57:21+0100. Host-only copy: `state.json`.
Kit: `b483e6d3816cbfe0379fd6314af0cd96b8ad1a88`

## What changed
- decision applied D-20261127-17: loaded 3 ticket(s) from b50786bfd690. FXL-19: triage t_3d9ab922, gate t_d90b366e, triage waits on nothing. FXL-20: triage t_e31f1f06, gate t_e9db36b3, triage waits on accept FXL-19. FXL-21: triage t_edf3e2d5, gate t_02e46066, triage waits on accept FXL-19, accept FXL-20 [commit ace4e2c716ed, 2026-11-27T18:55:23+00:00, signature: by a listed key]

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
- **FXL-19** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: running
- **FXL-20** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-21** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo

## Blocks
- none

## Holds
- none

## Last hidden-suite result
{'ticket': 'FXL-18', 'enabled': True, 'passed': 173, 'total': 173, 'regressions': [], 'trusted_main': '6f2f554ac55de1311a62aa29c256ab6138ab5b50'}

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
