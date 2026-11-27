# FIX Lens, phase 2: candidate scope (draft, not approved)

**Status: a draft for Ubay to cut and order. Nothing here is approved, designed or ticketed.**
Ubay, 2026-11-27: "lets take from the prompt a phase 2 of the project, after this first deliverable". The
prompt is his validation brief (`validation/BRIEF-original.md`). Everything that brief asks of a FIX log
analysis tool and that FIX Lens v1.2 does not claim to do (the table at the end of `validation/BRIEF.md`) is
collected here as the candidate scope of phase 2.

## Where phase 1 ends
Phase 1 is the first deliverable: FIX Lens v1.2 (FIX 4.2 and 4.4, one pasted log of at most 1,000 messages,
decode, session timeline, order view, trading summary, filters), validated against the scoped brief, with the
defects that validation finds fixed, tested by Ubay with real logs and deployed. Phase 2 starts after that.

## Candidate scope, by theme
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

## The decisions that shape it (Ubay's)
1. **Does the tool stay a page that runs entirely in the browser?** Phase 1's promise is "nothing you paste is
   sent, stored or logged". Files of a million messages can still be read inside the page (in pieces, off the
   main thread, with results paged). Ten million and more probably cannot be made pleasant there; that would
   mean a companion that runs on the technician's own machine. Theme A needs this answer first.
2. **Which themes, in which order?** My suggestion: A first, because every "institutional" scenario of the
   brief needs real log sizes; then C and D, which are what a support technician asks of a session log; then E
   and F; G with whichever of C or D needs times first. **H (market data) is a product of its own** and I
   would make it phase 3.
3. **Who signs off the wider scope?** Phase 1's BRD was approved for a decode-and-explain tool. Cross-checking
   quantities and reconstructing order state moves it towards a reconciliation aid. That may need the same
   approval route as the BRD.

## What carries over from the validation
The validation of phase 1 leaves a generator, ground-truth manifests, a differential comparison with an
established FIX engine and property-based tests. Kept up, they are the acceptance suite phase 2 is built
against: each theme above starts by extending the ground truth, before any ticket is written.

## The route, as for phase 1
BRD refresh (if decision 3 says so), then PRD v2.0, then technical design v2.0, each approved by Ubay before
the next; then tickets through the harness, theme by theme.
