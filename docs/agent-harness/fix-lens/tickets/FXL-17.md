+++
key = "FXL-17"
title = "The Account filter keeps a message outside all orders that carries the Account, whatever its type"
rank = 17
blocked_by = []
labels = []
+++
`applyFilters` in `src/filters.js` leaves out every Heartbeat (35=0) when an Account is chosen, also a Heartbeat
that carries that Account. Technical design section 14 (v1.2) has no such exception: the `account` filter keeps
the messages of every order that has a message with that Account, **plus any message outside all orders that
carries that Account itself**. The message type plays no part.

The exception came from a sentence of FXL-13 ("A Heartbeat never passes it"), which meant a Heartbeat without
the Account and was worded badly. This ticket corrects it. Remove the exception; change nothing else.

`test/filters.test.js` is expected to change in this ticket: the test
`test_apply_filters_heartbeat_with_matching_account_is_excluded` describes the old behaviour and is replaced.

The source rules of technical design section 8.4 apply to every file under `src/`: no assignment to `.id`,
`.name`, `.title`, `.src`, `.value`, `.style` or `.cssText`, no `setAttribute`, no `import(`.
`test/static-checks.test.js` enforces this since FXL-9.

Acceptance criteria
- AC0: For this log: NewOrder 11=C1, 1=ACC1; ExecutionReport 11=C1, 37=O1 (no Account); Heartbeat with 1=ACC1;
  Heartbeat with no Account; choosing `ACC1` keeps messages 1, 2 and 3, and not 4.
- AC1: The type does not matter: for a log of a TestRequest (35=1) with 1=ACC1, a Logon (35=A) with 1=ACC1 and a
  Heartbeat with 1=ACC2, choosing `ACC1` keeps messages 1 and 2.
- AC2: A message outside all orders that has no Account, or another Account, does not pass, whatever its type.
- AC3: Filters still combine: in the log of AC0, with every message sent by `BRK` except message 1, choosing
  `ACC1` and SenderCompID `BRK` keeps messages 2 and 3.
- AC4: With no Account chosen, a Heartbeat passes or fails by the other filters alone, as before.
- AC5: Every other test of `test/filters.test.js` passes with its expectations unchanged.
