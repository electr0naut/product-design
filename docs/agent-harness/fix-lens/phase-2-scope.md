# FIX Lens after v1.2: phases 2, 3 and 4 (scope outline, not yet a PRD)

**Status: the phasing is agreed by Ubay (2026-11-27: "agreed on the phasing of the project"): phase 2 is
themes C, D and E; phase 3 is A, B and G; phase 4 is F and H. Nothing here is designed or ticketed; each phase
still needs its PRD and technical design approved.**
Ubay, 2026-11-27: "lets take from the prompt a phase 2 of the project, after this first deliverable", and then,
on the eight themes below: "lets keep A, B, F, G, H for phases 3 and 4". So **phase 2 is themes C, D and E.**
The prompt is his validation brief (`validation/BRIEF-original.md`): everything it asks of a FIX log analysis
tool that FIX Lens v1.2 does not claim to do (the table at the end of `validation/BRIEF.md`) is collected here.

## Where phase 1 ends
Phase 1 is the first deliverable: FIX Lens v1.2 (FIX 4.2 and 4.4, one pasted log of at most 1,000 messages,
decode, session timeline, order view, trading summary, filters), validated against the scoped brief, with the
defects that validation finds fixed, tested by Ubay with real logs and deployed. Phase 2 starts after that.

## The themes
| # | Theme | What it adds | From the brief | Size (rough, in tickets) |
|---|---|---|---|---|
| A | **Large logs and files** | Read log files, not only a paste: 10,000 to millions of messages, rotated and compressed files, several files as one log, orders that span files. Results that stay usable at that size (search, paging). | 9, 11, 12, 14 | 8 to 12 |
| B | **More input forms** | JSON-wrapped messages, TCP payloads and PCAP captures, length-delimited DATA fields with delimiter bytes in them. | 9, 10 | 4 to 6 |
| C | **Session analysis in depth** | Session identity beyond the CompID pair (SubIDs, qualifiers). Heartbeat intervals and timeouts. Resend requests matched to what was resent or gap-filled. Duplicate and too-low sequence numbers. Disconnects and reconnects. Resets across trading days. | 6, 11 | 6 to 8 |
| D | **Order and execution reconstruction** | A full order state for every order (pending, rejected, expired, IOC and FOK outcomes). Quantity cross-checks: CumQty, LeavesQty and AvgPx against the fills, with the valid exceptions. Order status requests. Order identity scoped to its session. The same execution seen on several feeds (drop copy) told apart from separate executions. | 7, 11, 13 | 8 to 10 |
| E | **Field-level validation** | Required fields per message type and version, field formats and ranges, enumerations, repeating groups read as groups (counts, order, nesting). | 4, 8, 10 | 6 to 8 |
| F | **More protocol versions and dictionaries** | FIX 5.0 SP2 over FIXT 1.1 (transport and application versions kept apart). A venue's own dictionary: custom message types, tags and values. | 4, 11 | 6 to 8 |
| G | **Time and latency** | Event time, SendingTime, TransactTime and the log's own timestamps kept apart; time zones and precision; latency figures that never mix clocks without saying so; midnight and trading-day boundaries. | 9, 11, 13 | 4 to 6 |
| H | **Market data** | Requests, snapshots, incremental refreshes and rejects; subscriptions; book state rebuilt and checked; missed updates and recovery. | 8, 11 | 10 or more |

The sizes are guesses from phase 1, where ten tickets took about four hours of pipeline time and a day of
review; they are for ordering, not for planning.

## Phase 2: themes C, D and E (Ubay's decision)
| Theme | In phase 2 |
|---|---|
| **C. Session analysis in depth** | session identity beyond the CompID pair; heartbeat intervals and timeouts; resend requests matched to what was resent or gap-filled; duplicate and too-low sequence numbers; disconnects and reconnects; resets across trading days |
| **D. Order and execution reconstruction** | a full state for every order; quantity cross-checks (CumQty, LeavesQty, AvgPx against the fills); order status requests; order identity scoped to its session; the same execution on several feeds told apart from separate executions |
| **E. Field-level validation** | required fields per message type and version; field formats and ranges; enumerations; repeating groups read as groups |

It stays inside phase 1's frame: FIX 4.2 and 4.4, one pasted log within the present limits, a page that runs
entirely in the browser.

**One dependency to settle in the PRD:** heartbeat timeouts (C) need arithmetic on SendingTime. That is one
clock, read from the messages, and I would put that much in phase 2. Everything about several clocks, time
zones and latency stays with theme G.

**The sign-off route (decided by Ubay, 2026-11-27):** "we generate a new BRD with the phases without going
through the previous reviewers and it is autoapproved. I just need the BRD updated with the changes". The BRD
(Confluence page 589885, version 4) now carries the four phases, the Risk Committee decisions they change and
the risks they add. No new round with the role reviewers or the Risk Committee is needed for phase 2.

**Added to the validation in phase 2 (Ubay, 2026-11-27: "Phase 2"):** the privacy check (nothing pasted leaves
the page) and the markup check (log content cannot inject markup). They are not part of the validation of
phase 1.

## Phases 3 and 4: themes A, B, F, G and H (agreed by Ubay)
- **Phase 3: A and B, with G.** Large logs and files, the other input forms, and time and latency. A is the
  change of architecture, and B and G both lean on it: PCAP and log-prefixed files bring their own
  timestamps.
- **Phase 4: F and H.** FIX 5.0 SP2 with venue dictionaries, and market data, which is close to a product of
  its own.

**The decision that opens phase 3 (Ubay's): does the tool stay a page that runs entirely in the browser?**
Phase 1's promise is "nothing you paste is sent, stored or logged". Files of a million messages can still be
read inside the page (in pieces, off the main thread, with results paged). Ten million and more probably
cannot be made pleasant there; that would mean a companion that runs on the technician's own machine.

## The maximum for now: 10,000 messages (Ubay, 2026-11-27)
"A meaning huge files. 10000 is the max for now." So theme A is about files well beyond that, and the tool's
limit is to go from 1,000 to 10,000 messages. That is a change to the approved PRD (AC-016 to AC-018, TR-005)
and to the design, so it needs Ubay's approval of the wording before any ticket.

Measured on 2026-11-27 with the limit lifted in a scratch copy of v1.2, in a real browser (headless Chromium,
a mix of orders and fills, pipe-delimited):

| messages | bytes | logic only | Decode to painted | one filter change |
|---:|---:|---:|---:|---:|
| 1,000 | 154,025 | 52 ms | 1.2 s | 0.3 s |
| 5,000 | 782,116 | 223 ms | 5.6 s | 1.5 s |
| 10,000 | 1,575,034 | 450 ms | 11.1 s | 3.4 s |

- **The logic is ready for 10,000:** it scales in a straight line and takes under half a second.
- **The page is not:** it draws every message card at once (about 1.1 ms per message, and over a million page
  elements at 10,000 messages), so Decode takes 11 seconds and every filter change over 3.
- **The byte limit has to move too:** 10,000 messages of this kind are 1.6 MB, over today's 1,048,576.

So raising the limit is a change to how the page draws (cards a page at a time), not to the analysis. Rough
size: three or four tickets. Proposed as v1.3, before or after Ubay's real-log test, as he chooses.

## What carries over from the validation
The validation of phase 1 leaves a generator, ground-truth manifests, a differential comparison with an
established FIX engine and property-based tests. Kept up, they are the acceptance suite phase 2 is built
against: each theme starts by extending the ground truth, before any ticket is written.

## The route, as for phase 1
For each phase: the PRD, then the technical design, each approved by Ubay before the next; then tickets
through the harness. The BRD already covers the four phases (refresh of 2026-11-27); it is refreshed again only
if the answer to the phase 3 question changes its basis. Phase 2's PRD would be v2.0.
