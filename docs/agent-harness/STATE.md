# Harness state

Written by the runner at 2026-11-28T01:04:32+0100. Host-only copy: `state.json`.
Kit: `9f1a4a1c122a802f5d25734dbca5318ab305c415`

## What changed
- decision applied D-20261127-22: ticket.md written for FXL-22; card text replaced on: triage, planner, implementer, gatekeeper, reviewer, scribe [commit 6ac65b0160a5, 2026-11-28T00:03:17+00:00, signature: by a listed key]

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
- **FXL-22** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: blocked
- **FXL-23** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: blocked
- **FXL-24** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-25** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo
- **FXL-26** (open): gatekeeper: todo, implementer: todo, planner: todo, reviewer: todo, scribe: todo, triage: todo

## Blocks
- FXL-22 · triage (`t_e6592dfb`), head `None`: AC10 states 'findOrder also learns to find the order of one message' but doesn't specify the behavior. What is the input (a message object? a message number?)? What is the output (the order/group? the order id?)? What is the new function signature?
- FXL-23 · triage (`t_b6621679`), head `None`: AC9 is truncated in the handoff ('The usual order still works as today: a fi… [truncated, 368 chars omitted]'). Cannot verify observability (Rule 1). Please provide the complete text of AC9.

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
