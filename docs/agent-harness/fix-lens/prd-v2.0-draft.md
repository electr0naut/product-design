# FIX Lens PRD v2.0 (phase 2): DRAFT, not approved

**Status:** draft by the reviewing session, 2026-11-28, for Ubay Gonzalez to read and correct. Nothing in it is
approved, designed or ticketed. The approved PRD is `prd.md` (v1.4) and it is unchanged. When this draft is
approved, its stories are merged into `prd.md` as v2.0 and the technical design follows.

**Basis:** `phase-2-scope.md` (phase 2 is themes C, D and E, agreed by Ubay on 2026-11-27), the nine findings of
the validation that v1.4 left open (FL-06 to FL-12, FL-14, FL-16 in `validation/reports/defects.md`), and the
two checks Ubay moved to phase 2 (privacy and markup).

**The frame does not change:** FIX 4.2 and 4.4, one pasted log of at most 10,000 messages and 10,485,760
bytes, a page that runs entirely in the browser and sends, stores and logs nothing.

**Phase 1 is not closed yet.** The scope outline ends phase 1 with Ubay's test on real logs and a deployment.
Neither has happened. This draft can be read and approved before that, but no phase 2 ticket should be loaded
until phase 1 is closed or Ubay says otherwise.

## Decisions for Ubay before this can be approved

| # | Question | Recommendation | Why |
|---|---|---|---|
| 1 | Are SubID and LocationID always part of what makes a session? | No: decide per log (AC-075), with a control to override | Some counterparties run one session per desk SubID; others put a trader id in SubID on one session. A fixed rule invents gaps in one case or hides them in the other (FL-06) |
| 2 | Heartbeat timeouts need arithmetic on SendingTime (52). In phase 2? | Yes, on SendingTime only, within one sender | One clock per sender, read from the messages. Several clocks, time zones and latency stay in phase 3 (theme G) |
| 3 | How much field validation? | Required fields, data types and code sets from the Orchestra files already used; repeating groups read as groups. No conditional rules ("required when OrdType is Limit") | The conditional rules are prose in the specification, not data; each would be a hand-written rule. They can be added later one by one |
| 4 | Does a validation finding make a message "malformed"? | No. Malformed stays what TR-002 says (framing). Validation findings are a third state: valid, with findings | Otherwise a message a venue sends every day with one odd field would drop out of the order view and the trading summary |
| 5 | Quantities and prices as exact decimals? | Yes (FL-16) | Sums in binary floating point show values that are not in the log |
| 6 | Order of delivery | E first (dictionary), then C, then D | D's checks use E's number rule and C's sessions |

## What changes for the technician

- **Sessions (theme C).** The page lists the sessions in the log, tells them apart correctly, and explains
  what happened to each: sequence numbers that are too low, resends matched to what came back, heartbeats that
  stopped, disconnects and restarts.
- **Orders (theme D).** Every order has a state the page works out and checks against what the reports say:
  quantities that do not add up are pointed out, a resent report no longer changes the state, and a resent
  order is not counted twice.
- **Fields (theme E).** A message that frames correctly but breaks the specification says where: a required
  field is missing, a value has the wrong form, a code is not in the code set, a repeating group has the wrong
  count. Repeating groups are shown as groups.

## Out of scope for v2.0

- Everything in phases 3 and 4: files and logs above the limit, JSON, TCP and PCAP input, FIX 5.0 and venue
  dictionaries, time zones and latency, market data.
- Conditional field rules of the specification (decision 3).
- Repair or resending of anything: the page only reads.
- Matching one execution seen on several feeds across different executing parties' ids (a drop copy that
  renumbers ExecIDs). v2.0 tells apart what the ids allow (AC-082) and says when it cannot.

## Theme E: field-level validation

### US-011: Tell me where a message breaks the specification

**As a** client onboarding technician
**I want to** see which fields of a message break the FIX specification of its version
**So that** I can tell a counterparty exactly what to correct during certification

- AC-063: Each valid message (TR-002) is checked against the message definition of its BeginString and
  MsgType in the Orchestra dictionary. The checks produce findings; a message with findings is still valid
  and still takes part in every other result.
- AC-064: A finding is one of:
    - a required field of the message type is absent (required as marked in the dictionary, header and
      trailer included);
    - a field has no value;
    - a value does not have the form of its data type (AC-066);
    - a value of a field with a code set is not in it (a multiple-value field is checked value by value,
      AC-067);
    - a tag appears twice outside a repeating group;
    - a tag is not defined for this message type in this version. Tags 5000 to 9999 and above 20000 are
      user-defined and are never findings.
- AC-065: A message card lists its findings at the top, each with the tag, the field name and the rule, and
  the field row is marked. The summary strip shows the number of messages with findings, and the log can be
  filtered to them.
- AC-066: The forms of the data types:
    - int, Length, SeqNum, NumInGroup: digits, with an optional leading minus for int only;
    - Qty, Price, PriceOffset, Amt, float: digits with an optional decimal point and an optional leading
      minus; no exponent, no `0x`, no spaces, no thousands separator, no leading `+` (FL-10);
    - char: one character; Boolean: `Y` or `N`;
    - UTCTimestamp: `YYYYMMDD-HH:MM:SS` or with `.sss`; UTCDateOnly and LocalMktDate: `YYYYMMDD`;
      UTCTimeOnly: `HH:MM:SS` or with `.sss`; each a real date or time (a leap second `60` is allowed);
    - String, data and every other type: any value that is not empty.
- AC-067: A field of type MultipleValueString (for example ExecInst 18) is read as values separated by one
  space. Each value is decoded with its own meaning and checked on its own (FL-14).
- AC-068: A quantity or price that fails AC-066 is not counted in the trading summary or the order state, and
  the trading summary says how many fills were left out for that reason (FL-10).

### US-012: Show repeating groups as groups

**As a** FIX support technician
**I want to** see the entries of a repeating group one under another
**So that** I can read parties, legs and allocations without counting tags

- AC-069: A field whose data type is NumInGroup opens a repeating group, as defined in the dictionary for
  that message type. A new entry starts at each appearance of the group's first field. A group inside an
  entry is read the same way.
- AC-070: In the message card the group is shown under its count field, entry by entry, numbered, with nested
  groups indented. Fields outside groups keep the order they have in the message.
- AC-071: Findings for groups: the count is not the number of entries found; an entry does not start with the
  group's first field; a group field appears outside its group.
- AC-072: A group that the dictionary does not define for the message (an unknown or user-defined count
  field) is shown flat, as today, without a finding.

### US-013: Do not lose a line that looks like FIX

- AC-073: A line that has a `35=` field and ends in a `10=nnn` field, but has no place where a message can
  start (TR-002), is reported as a malformed message "no BeginString" and counted (FL-12).

## Theme C: session analysis in depth

### US-014: The sessions in the log

**As a** FIX support technician
**I want to** see which sessions the log contains and follow each on its own
**So that** numbers of one session are never read as another's

- AC-074: A session is identified by BeginString, SenderCompID (49) and TargetCompID (56) taken as a pair in
  either direction, and, when the log uses them to separate sessions, SenderSubID (50), TargetSubID (57),
  SenderLocationID (142) and TargetLocationID (143).
- AC-075: Whether SubID and LocationID separate sessions is decided per CompID pair: they do when two Logons
  (35=A) of that pair carry different values of them. The page says which rule it used for each pair, and a
  control lets the technician choose the other. (Decision 1. The examples of FL-06 have no Logon; the design
  must settle what a log without Logons does, and I recommend "separate when the sequence numbers only make
  sense separately", with the reasoning shown.)
- AC-076: A sessions panel lists each session with its ids, the number of messages each way, the first and
  last SendingTime, and its counts of gaps, resends, rejects and restarts. Selecting a session filters the
  log to it, like the present filters.
- AC-077: Every sequence result is computed per session and direction.

### US-015: Sequence numbers, completely

- AC-078: A message whose MsgSeqNum (34) is lower than the expected number and that has no PossDupFlag (43)=Y
  is a **SequenceTooLow** event, "expected N, received M". The expected number does not change (FL-07).
- AC-079: A message with PossDupFlag=Y whose number is the expected one is processed and takes the number. A
  PossDup message with a lower number is a **Resent** event and changes nothing (FL-09).
- AC-080: A SequenceReset (35=4) whose NewSeqNo (36) is not above the expected number does not move it, and
  its event says so (FL-09). A GapFill whose own MsgSeqNum is above the expected number is itself a gap.
- AC-081: A ResendRequest (35=2) is matched to its answer: the messages with PossDupFlag=Y and the GapFills
  that follow from the other side, by number, over BeginSeqNo (7) to EndSeqNo (16), where EndSeqNo `0` (and
  `999999` in FIX 4.2) means "to the latest". The event shows the range asked, which numbers were resent,
  which were gap-filled, and which were never answered in the log.
- AC-082: A resent message (PossDupFlag=Y, with a number already seen on its session) is not a new business
  event: it is not counted as an order (FL-08), not counted as a fill, and does not change an order's state
  (FL-11). The same holds for the second copy of a message in a log merged from both sides of a connection,
  when the two copies are identical. The card of such a message says which message it
  repeats.

### US-016: Heartbeats, disconnects and restarts

- AC-083: The heartbeat interval of a session is HeartBtInt (108) of its Logon. For each sender, a silence
  between two consecutive messages longer than the interval plus 20 percent, measured on SendingTime (52), is
  a **HeartbeatLate** event with both times. Without a Logon in the log, or without SendingTime, no such
  event is produced and the sessions panel says why.
- AC-084: A TestRequest (35=1) is matched to the Heartbeat (35=0) that carries its TestReqID (112). A
  TestRequest never answered in the log is marked.
- AC-085: A session ends cleanly when both sides send Logout (35=5). A Logon on a session whose last message
  was not a Logout is a **RestartWithoutLogout** event. A Logout with Text (58) shows the text in the event.
- AC-086: A restart is a Logon after the first on a session. The event says whether the numbers continued or
  went back to 1, and whether ResetSeqNumFlag (141)=Y was set. A restart at 1 on a later date than the last
  message before it (by SendingTime) is labelled a daily reset.
- AC-087: A SessionReject (35=3) is linked to the message it rejects, by RefSeqNum (45), with RefTagID (371)
  and SessionRejectReason (373) decoded. A BusinessReject (35=j) is linked the same way.

## Theme D: order and execution reconstruction

### US-017: The state of every order

**As a** FIX support technician
**I want to** see the state the reports give an order and the state the fills add up to
**So that** I can see at once when a counterparty's numbers do not agree with themselves

- AC-088: An order's identity is scoped to its session (US-014) as well as to its parties (AC-035), so two
  desks of one client that reuse a ClOrdID have separate orders.
- AC-089: Each order has a state from its latest ExecutionReport that is not a repeat (AC-082) and not an
  OrderStatus answer to a request: OrdStatus (39) decoded, including PendingNew, PendingCancel,
  PendingReplace, Rejected (with OrdRejReason 103 and Text), Expired, DoneForDay, Stopped and Suspended. The
  banner says "as of message N".
- AC-090: An order with TimeInForce (59) `3` (IOC) or `4` (FOK) says how it ended: filled in full, filled in
  part and the rest cancelled, or cancelled without a fill. A FOK order with a partial fill is a finding.
- AC-091: An order list shows every order of the log with its ids, session, terms, state, filled quantity
  and average price, and its number of findings. It is paged like the rest (US-010) and follows the filters.
- AC-092: An OrderStatusRequest (35=H) is a timeline event and is matched to the ExecutionReport that answers
  it (ExecType `I` in 4.4, ExecTransType `3` in 4.2, by OrdStatusReqID 790 when present, otherwise by the
  order's ids).

### US-018: Cross-check the quantities

- AC-093: For each ExecutionReport of an order, in order, after trade cancels and corrections:
    - CumQty (14) equals the sum of LastShares/LastQty (32) of the order's fills so far;
    - LeavesQty (151), when present, equals OrderQty (38) minus CumQty, or `0` when OrdStatus is Cancelled,
      Rejected, Expired or DoneForDay;
    - AvgPx (6) equals the quantity-weighted average of LastPx (31) of the fills so far, within the last
      decimal place the report shows;
    - CumQty never goes down except by a trade cancel or correction;
    - OrdStatus agrees with the quantities: Filled only when LeavesQty is `0` and CumQty equals OrderQty,
      PartiallyFilled only when CumQty is above zero.
- AC-094: A check that fails is a finding on that report: what the report says, what the fills give, and the
  messages the figure was computed from. Checks that cannot be made say why: the order's first messages are
  not in the log (the first report already has CumQty above zero), or OrderQty changed by a replace.
- AC-095: An order whose fills begin before the log does is treated as starting from its first report's
  CumQty and AvgPx; the differences from there on are checked.
- AC-096: The same execution on two feeds: reports with the same ExecID (17) from the same executing party to
  different targets (for example the client session and a drop copy) are one execution, counted once, and the
  card says where else it appears. Reports with the same ExecID from different executing parties are
  different executions (as in v1.4).
- AC-097: Quantities, prices and their sums are exact decimals, not binary floating point. Figures are shown
  with the decimals they have, up to 8, and a value beyond that is rounded half away from zero and marked as
  rounded (FL-16).

## Checks added to the validation in phase 2

- AC-098 (privacy): with the browser's network recording on, pasting and decoding any log makes no request
  after the page and its own files have loaded, and writes nothing to cookies, localStorage, sessionStorage,
  IndexedDB or the cache. Checked in a real browser as part of the acceptance suite.
- AC-099 (markup): no pasted text can become markup, an attribute, a class name, a URL or script. Checked with
  a corpus of hostile values in every field that is displayed, in a real browser, under a Content Security
  Policy that forbids inline script and style.

## Technical requirements that change

- **TR-001:** the dictionary carries, per version: required fields per message type, data types, and group
  definitions (count field, first field, members, nesting). The page's size and load time stay within TR-005.
- **TR-003:** rewritten around sessions (US-014 to US-016).
- **TR-005:** every result of v2.0 on a log of 10,000 messages within the present time limits; validation
  and the cross-checks must not add more than half a second to Decode on the reference machine.
- **TR-006:** AC-098 and AC-099.

## Delivery, roughly

Before any ticket, as agreed in the scope outline: the ground truth is extended theme by theme (generator,
manifests, the comparison with an established FIX engine), and the hidden acceptance tests are written from it.

| Step | Stories | Tickets (guess) |
|---|---|---|
| 1. Dictionary and validation | US-011, US-013 | 5 to 6 |
| 2. Groups | US-012 | 2 to 3 |
| 3. Sessions and sequence numbers | US-014, US-015 | 5 to 6 |
| 4. Heartbeats and restarts | US-016 | 3 |
| 5. Order state and cross-checks | US-017, US-018 | 6 to 8 |
| 6. Privacy and markup checks | AC-098, AC-099 | 1 to 2 |

About 22 to 28 tickets. At the measured 14 to 30 minutes and about 60 cents of review per ticket, that is nine
to fourteen hours of pipeline time; the ground truth and hidden tests are the larger part of the work.

## Risks

- **The session rule guesses wrong (AC-075).** Mitigation: the rule used is shown and can be overridden.
- **Validation noise.** Real venues break the specification in small ways every day; a page full of findings
  hides the one that matters. Mitigation: findings never change validity (decision 4), and they can be
  filtered and counted by rule. The real-log test of phase 1 should be repeated on v2.0 for this.
- **The dictionary grows.** Required fields and groups for two versions add to the page's size. To measure in
  the design.
- **Cross-checks on partial logs.** Most pasted logs start mid-session. Mitigation: AC-094 and AC-095 say
  what was not checked instead of inventing a finding.
