# Harness state

Written by the runner at 2026-11-28T01:06:39+0100. Host-only copy: `state.json`.
Kit: `9f1a4a1c122a802f5d25734dbca5318ab305c415`

## What changed
- decision applied D-20261127-23: ticket.md written for FXL-23; card text replaced on: triage, planner, implementer, gatekeeper, reviewer, scribe; triage waits on 'accept FXL-22' again [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]
- decision applied D-20261127-24: unblocked t_e6592dfb (FXL-22 · triage) [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]
- decision applied D-20261127-25: unblocked t_b6621679 (FXL-23 · triage) [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]
- decision applied D-20261127-26: ticket.md written for FXL-24; card text replaced on: triage, planner, implementer, gatekeeper, reviewer, scribe; triage waits on 'accept FXL-23' again [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]
- decision applied D-20261127-27: ticket.md written for FXL-25; card text replaced on: triage, planner, implementer, gatekeeper, reviewer, scribe [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]
- decision applied D-20261127-28: ticket.md written for FXL-26; card text replaced on: triage, planner, implementer, gatekeeper, reviewer, scribe [commit 501b01f95a68, 2026-11-28T00:03:58+00:00, signature: by a listed key]

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
