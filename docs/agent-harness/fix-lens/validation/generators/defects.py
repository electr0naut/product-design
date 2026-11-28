"""Which hand-built cases reproduce which defect. Used by build.py to write reproductions/."""
DEFECTS = [
    ("FL-01", "P0", "Two fills that share OrderID and ExecID on different sessions are counted as one", ["S07-08"]),
    ("FL-02", "P0", "Orders of different clients that reuse a ClOrdID are merged, and the Account filter shows the other client's flow", ["S07-06", "S07-07"]),
    ("FL-03", "P1", "Clicking an id opens another order when the value is a ClOrdID of one order and the OrderID of another", ["S07-11"]),
    ("FL-04", "P1", "A trade cancel that stands before its fill in the log is not applied", ["S07-05"]),
    ("FL-05", "P1", "After a session restarts at 1 without ResetSeqNumFlag, sequence gaps are no longer found", ["S06-11"]),
    ("FL-06", "P1", "Sessions told apart only by SubIDs share one sequence counter: missed gaps and false gaps", ["S06-15", "S06-16"]),
    ("FL-07", "P1", "A MsgSeqNum that was already used, without PossDupFlag, is shown as a normal message", ["S06-08"]),
    ("FL-08", "P2", "A resent or duplicated NewOrderSingle is counted as another order in the trading summary", ["S06-13-4.4", "S06-13-4.2", "S11-01"]),
    ("FL-09", "P2", "False sequence gaps after a PossDup message with the expected number, and after a SequenceReset to a lower number", ["S06-17", "S06-18"]),
    ("FL-10", "P2", "Values that are not FIX numbers are counted as quantities and prices", ["S10-15-01", "S10-15-02", "S10-15-03", "S10-15-12"]),
    ("FL-11", "P2", "The order banner takes the order's latest state from a resent older report", ["S07-12"]),
    ("FL-12", "P2", "A message without BeginString disappears without an error", ["S10-03"]),
    ("FL-13", "P2", "A wire-valid message with ISO-8859-1 text is reported as malformed", ["S10-24"]),
    ("FL-14", "P3", "A valid multiple-value field is labelled 'unknown value'", ["S04-05-4.4", "S04-05-4.2"]),
    ("FL-15", "P3", "An average price that ends exactly on a half is rounded down", ["S07-16"]),
    ("FL-16", "P3", "Figures finer than 4 decimal places or larger than 2^53 are shown as other values", ["S10-16", "S10-17"]),
]
