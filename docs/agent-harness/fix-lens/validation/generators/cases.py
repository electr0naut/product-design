"""Hand-built cases with their ground truth. Each case is one small log and what a correct reading of it is.

`kind` says where the expectation comes from:
  "prd"  - the product's own PRD / technical design requires it (a failure is a product defect);
  "fix"  - the FIX 4.2/4.4 specification or plain business truth requires it, and the PRD/design is
           silent or says otherwise (a failure is a gap in the product's documents).
Expectations are written from the specification and the PRD text, never from the tool's output.
"""
from fixgen import SOH, encode

DASH = "–"
CASES = []


class S:
    """Minimal session helper for hand-built logs: MsgSeqNum per direction, a one-second clock."""

    def __init__(self, begin="FIX.4.4", date="20261127"):
        self.begin, self.date, self.seq, self.t = begin, date, {}, 0

    def time(self):
        s = 9 * 3600 + self.t
        self.t += 1
        return f"{self.date}-{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}.000"

    def m(self, frm, to, typ, body=(), seq=None, possdup=False, begin=None, sub=None, tsub=None, time=None,
          body_length=None, checksum=None):
        key = (frm, to, sub, tsub)
        if seq is None:
            seq = self.seq.get(key, 0) + 1
        if not possdup:
            self.seq[key] = seq
        head = [(35, typ), (49, frm), (56, to)]
        if sub:
            head.append((50, sub))
        if tsub:
            head.append((57, tsub))
        head.append((34, seq))
        if possdup:
            head.append((43, "Y"))
        head.append((52, time or self.time()))
        return encode(begin or self.begin, head + list(body), body_length, checksum)

    def er(self, frm, to, cl, oid, eid, et, st, sym="ACME", side=1, qty=100, lq=0, lp=0, cum=0, avg=0, ref=None,
           trans=None, orig=None, acct=None, **kw):
        begin = kw.get("begin") or self.begin
        body = [(37, oid)] + ([(11, cl)] if cl else []) + ([(41, orig)] if orig else []) + [(17, eid)]
        if begin == "FIX.4.2":
            body.append((20, 0 if trans is None else trans))
        if ref:
            body.append((19, ref))
        body += [(150, et), (39, st)] + ([(1, acct)] if acct else [])
        body += ([(55, sym)] if sym else []) + [(54, side), (38, qty), (32, lq), (31, lp), (151, 0), (14, cum), (6, avg)]
        return self.m(frm, to, "8", body, **kw)

    def nos(self, frm, to, cl, sym="ACME", side=1, qty=100, px=None, acct=None, **kw):
        body = [(11, cl)] + ([(1, acct)] if acct else []) + [(21, 1), (55, sym), (54, side), (38, qty)]
        body += [(40, 2), (44, px)] if px is not None else [(40, 1)]
        return self.m(frm, to, "D", body, **kw)


def row(buy_orders=0, bought="0", avg_buy=DASH, sell_orders=0, sold="0", avg_sell=DASH, net="0"):
    return {"buyOrders": str(buy_orders), "bought": bought, "avgBuy": avg_buy, "sellOrders": str(sell_orders),
            "sold": sold, "avgSell": avg_sell, "net": net}


def case(cid, feature, version, kind, basis, lines, expect, folder=None, view=None, eol="\n", text=None, note=None):
    CASES.append({"id": cid, "feature": feature, "version": version, "kind": kind, "basis": basis,
                  "text": text if text is not None else eol.join(lines) + eol, "expect": expect, "view": view,
                  "folder": folder or {"FIX.4.2": "FIX42", "FIX.4.4": "FIX44"}.get(version, "multi-session"),
                  "note": note})


def fpos(text, field, nth=0):
    """1-based position of the nth field that starts with `field` right after an SOH."""
    return pos(text, SOH + field, nth) + 1


def pos(text, needle, nth=0):
    """1-based character position of the nth occurrence of `needle` in `text`."""
    i = -1
    for _ in range(nth + 1):
        i = text.index(needle, i + 1)
    return i + 1


LOGON = [(98, 0), (108, 30)]

# =============================================================================== section 4
s = S()
lines = [s.m("A", "B", "A", LOGON, begin="FIX.4.3"), s.m("A", "B", "0", begin="FIXT.1.1"),
         s.m("A", "B", "0", begin="FIX.4.1"), s.m("A", "B", "0")]
case("S04-01", "Unsupported BeginString is reported per message", "FIX.4.4", "prd", "PRD Scope; design 5",
     lines, {"labels": {"1": "unsupported version FIX.4.3", "2": "unsupported version FIXT.1.1",
                        "3": "unsupported version FIX.4.1", "4": "Heartbeat"},
             "stats": {"messages": 4, "valid": 4, "malformed": 0}})

for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    lines = [s.m("A", "B", "D", [(11, "X1"), (21, 1), (55, "ACME"), (54, "Z"), (38, 100), (40, 2), (44, "10.5"),
                                 (5001, "venue-flag"), (20001, "x=y")])]
    case(f"S04-02-{v[-3:]}", "Unknown tag and unknown enum value are shown raw and labelled", v, "prd", "AC-004",
         lines, {"rows": [{"number": 1, "tag": "5001", "field": "Unknown tag 5001", "value": "venue-flag"},
                          {"number": 1, "tag": "20001", "field": "Unknown tag 20001", "value": "x=y"},
                          {"number": 1, "tag": "54", "field": "Side", "value": "Z", "meaning": "unknown value"},
                          {"number": 1, "tag": "40", "field": "OrdType", "value": "2", "meaning": "Limit"}]})

# ExecType / ExecTransType by version (PRD TR-003; FIX 4.2 ExecTransType 20; FIX 4.4 ExecType F, G, H, I)
s = S("FIX.4.2")
lines = [s.er("B", "A", "C1", "O1", "E1", "0", "0"),
         s.er("B", "A", "C1", "O1", "E2", "1", "1", lq=40, lp=10, cum=40, avg=10),
         s.er("B", "A", "C1", "O1", "E3", "2", "2", lq=60, lp=11, cum=100, avg="10.6"),
         s.er("B", "A", "C1", "O1", "E4", "2", "2", trans=3, cum=100, avg="10.6"),           # status
         s.er("B", "A", "C1", "O1", "E5", "1", "1", trans=1, ref="E3", lq=60, lp=11, cum=40, avg=10),  # bust
         s.er("B", "A", "C1", "O1", "E6", "1", "1", trans=2, ref="E2", lq=40, lp=9, cum=40, avg=9),    # correct
         s.er("B", "A", "C1", "O1", "E7", "F", "1", lq=5, lp=9, cum=45, avg=9),               # F is not FIX 4.2
         s.er("B", "A", "C1", "O1", "E8", "4", "4", cum=40, avg=9),
         s.er("B", "A", "C2", "O2", "E9", "8", "8"), s.er("B", "A", "C3", "O3", "E10", "C", "C")]
case("S04-03-4.2", "FIX 4.2 execution reports: ExecTransType before ExecType", "FIX.4.2", "prd", "TR-003; design 7.5",
     lines, {"events": ["1:Acknowledgement", "2:Fill", "3:Fill", "4:OrderStatus", "5:TradeCancel", "6:TradeCorrect",
                        "7:ExecutionReport (ExecType F)", "8:Cancelled", "9:ExecutionReport (ExecType 8)",
                        "10:ExecutionReport (ExecType C)"],
             "trades": {"ACME": row(bought="40", avg_buy="9", net="+40")}, "unmatched": 0})

s = S("FIX.4.4")
lines = [s.er("B", "A", "C1", "O1", "E1", "0", "0"),
         s.er("B", "A", "C1", "O1", "E2", "F", "1", lq=40, lp=10, cum=40, avg=10),
         s.er("B", "A", "C1", "O1", "E3", "F", "2", lq=60, lp=11, cum=100, avg="10.6"),
         s.er("B", "A", "C1", "O1", "E4", "I", "2", cum=100, avg="10.6"),
         s.er("B", "A", "C1", "O1", "E5", "H", "1", ref="E3", lq=60, lp=11, cum=40, avg=10),
         s.er("B", "A", "C1", "O1", "E6", "G", "1", ref="E2", lq=40, lp=9, cum=40, avg=9),
         s.er("B", "A", "C1", "O1", "E7", "4", "4", cum=40, avg=9),
         s.er("B", "A", "C2", "O2", "E8", "8", "8"), s.er("B", "A", "C3", "O3", "E9", "A", "A"),
         s.er("B", "A", "C3", "O3", "E10", "6", "6"), s.er("B", "A", "C3", "O3", "E11", "E", "E"),
         s.er("B", "A", "C3", "O3", "E12", "5", "0"), s.er("B", "A", "C3", "O3", "E13", "C", "C")]
case("S04-03-4.4", "FIX 4.4 execution reports: ExecType F, G, H, I", "FIX.4.4", "prd", "TR-003; design 7.5",
     lines, {"events": ["1:Acknowledgement", "2:Fill", "3:Fill", "4:OrderStatus", "5:TradeCancel", "6:TradeCorrect",
                        "7:Cancelled", "8:ExecutionReport (ExecType 8)", "9:ExecutionReport (ExecType A)",
                        "10:ExecutionReport (ExecType 6)", "11:ExecutionReport (ExecType E)", "12:Replaced",
                        "13:ExecutionReport (ExecType C)"],
             "trades": {"ACME": row(bought="40", avg_buy="9", net="+40")}, "unmatched": 0})

# FIX 4.4 traffic that still uses the FIX 4.2 values ExecType 1 / 2 for fills. Neither the Orchestra FIX 4.4 file
# nor QuickFIX's FIX44.xml lists 1 or 2 for ExecType, so by the dictionaries and by PRD TR-003 these are not
# fills: the tool must show them as "ExecutionReport (ExecType X)" with "unknown value" and count nothing.
s = S("FIX.4.4")
lines = [s.nos("A", "B", "C1", qty=100, px=10),
         s.er("B", "A", "C1", "O1", "E1", "1", "1", lq=40, lp=10, cum=40, avg=10),
         s.er("B", "A", "C1", "O1", "E2", "2", "2", lq=60, lp=10, cum=100, avg=10)]
case("S04-04", "FIX 4.4 reports with the FIX 4.2 values ExecType 1 or 2 are not fills and are labelled", "FIX.4.4", "prd",
     "TR-003 ('1 or 2 (FIX 4.2)'); AC-004, AC-009; Orchestra FIX 4.4 and QuickFIX FIX44.xml ExecType code sets",
     lines, {"trades": {"ACME": row(buy_orders=1)},
             "events": ["1:NewOrder", "2:ExecutionReport (ExecType 1)", "3:ExecutionReport (ExecType 2)"],
             "rows": [{"number": 2, "tag": "150", "value": "1", "meaning": "unknown value"}]},
     note="Risk, not verified with real logs: counterparties that still send 150=1/2 on FIX 4.4 get no fills counted.")

for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    lines = [s.m("A", "B", "D", [(11, "X1"), (21, 1), (55, "ACME"), (54, 1), (38, 100), (40, 2), (44, 10), (18, "1 6")])]
    case(f"S04-05-{v[-3:]}", "A multiple-value field (ExecInst 18=1 6) is not called an unknown value", v, "fix",
         "FIX 4.2/4.4 ExecInst (18) is a MultipleValueString; AC-004 'an enum value missing from the dictionary'",
         lines, {"rows": [{"number": 1, "tag": "18", "value": "1 6", "meaning_not": "unknown value"}]})

# =============================================================================== section 6
for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    lines = [s.m("A", "B", "A", LOGON), s.m("B", "A", "A", LOGON), s.m("A", "B", "0"), s.m("B", "A", "1", [(112, "T1")]),
             s.m("A", "B", "0", [(112, "T1")]), s.m("A", "B", "2", [(7, 2), (16, 0)]),
             s.m("B", "A", "4", [(123, "Y"), (36, 3)], seq=2, possdup=True),
             s.m("B", "A", "3", [(45, 4), (58, "bad")]), s.m("B", "A", "j", [(45, 4), (372, "D"), (380, 3)]),
             s.m("B", "A", "4", [(36, 20)]), s.m("B", "A", "0", seq=20),
             s.m("A", "B", "5"), s.m("B", "A", "5")]
    case(f"S06-01-{v[-3:]}", "Every session message type gets its event, in log order", v, "prd", "AC-007, AC-008",
         lines, {"events": ["1:Logon", "2:Logon", "3:Heartbeat", "4:TestRequest", "5:Heartbeat", "6:ResendRequest",
                            "7:GapFill", "8:SessionReject", "9:BusinessReject", "10:Reset", "11:Heartbeat",
                            "12:Logout", "13:Logout"],
                 "gaps": [], "stats": {"messages": 13, "valid": 13, "malformed": 0, "gaps": 0, "orders": 0},
                 "classes": {"8": "reject", "9": "reject", "1": "session"}})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("B", "A", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=6),
         s.m("B", "A", "0"), s.m("A", "B", "0"), s.m("B", "A", "0", seq=9), s.m("B", "A", "0")]
case("S06-02", "Sequence gaps are found per direction", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[4, 3, 6], [7, 3, 9]], "stats": {"gaps": 2}})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=5),
         s.m("A", "B", "0", seq=3, possdup=True), s.m("A", "B", "0", seq=4, possdup=True),
         s.m("A", "B", "0", seq=9, possdup=True), s.m("A", "B", "0", seq=6)]
case("S06-03", "PossDupFlag=Y neither advances nor resets the expected number", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[3, 3, 5]]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "4", [(123, "Y"), (36, 10)]),
         s.m("A", "B", "0", seq=10), s.m("A", "B", "0", seq=12)]
case("S06-04", "A GapFill sets the expected number to NewSeqNo", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[5, 11, 12]], "events": ["1:Logon", "2:Heartbeat", "3:GapFill", "4:Heartbeat", "5:SequenceGap", "5:Heartbeat"]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "4", [(36, 1)], seq=77),
         s.m("A", "B", "0", seq=1), s.m("A", "B", "0", seq=2)]
case("S06-05", "SequenceReset in reset mode: MsgSeqNum ignored, expected number becomes NewSeqNo", "FIX.4.4", "prd",
     "TR-003; design 7", lines, {"gaps": [], "events": ["1:Logon", "2:Heartbeat", "3:Reset", "4:Heartbeat", "5:Heartbeat"]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("B", "A", "A", LOGON), s.m("A", "B", "0"), s.m("B", "A", "0"), s.m("A", "B", "0"),
         s.m("A", "B", "A", LOGON + [(141, "Y")], seq=1), s.m("B", "A", "A", LOGON + [(141, "Y")], seq=1),
         s.m("A", "B", "0", seq=2), s.m("B", "A", "0", seq=2), s.m("A", "B", "0", seq=4)]
case("S06-06", "Logon with ResetSeqNumFlag=Y restarts both directions at 1", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[10, 3, 4]]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("C", "D", "A", LOGON), s.m("A", "B", "0"), s.m("C", "D", "0"),
         s.m("B", "A", "A", LOGON), s.m("D", "C", "A", LOGON), s.m("A", "B", "0"), s.m("C", "D", "0", seq=5),
         s.m("B", "A", "0"), s.m("D", "C", "0")]
case("S06-07", "Sessions with overlapping sequence numbers are tracked apart", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[8, 3, 5]]}, folder="multi-session")

# A sequence number that was already used, without PossDupFlag, is a serious session error in FIX
# (FIX 4.2/4.4 session protocol: "MsgSeqNum too low" ends the session). The design ignores it.
s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0"),
         s.nos("A", "B", "X1", seq=2), s.m("A", "B", "0", seq=4)]
case("S06-08", "A duplicate MsgSeqNum without PossDupFlag is pointed out", "FIX.4.4", "fix",
     "FIX session protocol, MsgSeqNum lower than expected without PossDupFlag; design 11 says 'Ignored'", lines,
     {"flagged": [4]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=4), s.m("A", "B", "0", seq=3),
         s.m("A", "B", "0", seq=5)]
case("S06-09", "Out-of-order messages: the gap is reported once, the late message adds none", "FIX.4.4", "prd",
     "TR-003; design 11", lines, {"gaps": [[3, 3, 4]]})

s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("B", "A", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "5"), s.m("B", "A", "5"),
         s.m("A", "B", "A", LOGON), s.m("B", "A", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=8)]
case("S06-10", "Reconnection that continues the sequence numbers", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[9, 6, 8]]})

# Reconnection where both sides start again at 1 without ResetSeqNumFlag (QuickFIX ResetOnLogout /
# ResetOnDisconnect, or a scheduled daily reset): the second run of the session is 1, 2, 5.
s = S()
lines = [s.m("A", "B", "A", LOGON)] + [s.m("A", "B", "0") for _ in range(6)] + [s.m("A", "B", "5")]
s.seq.clear()
lines += [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=5)]
case("S06-11", "A gap after the session restarts at 1 without ResetSeqNumFlag is still found", "FIX.4.4", "fix",
     "FIX session protocol: sequence numbers restart at 1 on a new session; TR-003 resets only on 141=Y", lines,
     {"gaps_include": [[11, 3, 5]]})

for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    fill = dict(lq=100, lp=10, cum=100, avg=10)
    et = "2" if v == "FIX.4.2" else "F"
    lines = [s.nos("A", "B", "X1", px=10), s.er("B", "A", "X1", "O1", "E1", et, "2", **fill),
             s.nos("A", "B", "X1", px=10, seq=1, possdup=True),
             s.er("B", "A", "X1", "O1", "E1", et, "2", seq=1, possdup=True, **fill)]
    case(f"S06-12-{v[-3:]}", "A resent execution report (PossDupFlag=Y) is not a second execution", v, "prd", "AC-041",
         lines, {"trades_fields": {"ACME": {"bought": "100", "avgBuy": "10", "net": "+100"}}})
    case(f"S06-13-{v[-3:]}", "A resent NewOrderSingle (PossDupFlag=Y) is not a second order", v, "fix",
         "Brief 6: a retransmission is not a new business event; AC-040 counts NewOrderSingle messages", lines,
         {"trades_fields": {"ACME": {"buyOrders": "1"}}, "stats": {"orders": 1}})

s = S()
lines = [s.m("B", "A", "A", LOGON), s.m("B", "A", "0", seq=3),
         s.er("B", "A", "X1", "O1", "E1", "F", "2", lq=100, lp=10, cum=100, avg=10, seq=2, possdup=True)]
case("S06-14", "A PossDup report whose original is not in the log is still counted once", "FIX.4.4", "prd", "AC-041",
     lines, {"gaps": [[2, 2, 3]], "trades_fields": {"ACME": {"bought": "100"}}})

# Two sessions with the same CompIDs, told apart by SubIDs (FIX session identity may include SubID and
# LocationID). Desk D1 runs 1,2,3; desk D2 runs 1,2,4: D2 has a gap at its third message.
s = S()
lines = [s.m("A", "B", "A", LOGON, sub="D1"), s.m("A", "B", "A", LOGON, sub="D2"), s.m("A", "B", "0", sub="D1"),
         s.m("A", "B", "0", sub="D2"), s.m("A", "B", "0", sub="D1"), s.m("A", "B", "0", sub="D2", seq=4)]
case("S06-15", "Sessions that differ only by SenderSubID keep separate sequence numbers", "FIX.4.4", "fix",
     "Brief 11; FIX session identity; TR-003 keys a direction on 49/56 only", lines, {"gaps": [[6, 3, 4]]},
     folder="multi-session")
s = S()
lines = [s.m("A", "B", "A", LOGON, sub="D1"), s.m("A", "B", "0", sub="D1"),
         s.m("A", "B", "0", sub="D2", seq=50), s.m("A", "B", "0", sub="D2"), s.m("A", "B", "0", sub="D1"),
         s.m("A", "B", "0", sub="D1")]
case("S06-16", "No false gap when a second SubID session of the same CompIDs runs at higher numbers", "FIX.4.4", "fix",
     "Brief 11; FIX session identity; TR-003 keys a direction on 49/56 only", lines, {"gaps": []},
     folder="multi-session")

# A PossDup message that carries exactly the expected number has not been received before: FIX processes it
# normally and it takes that number (QuickFIX acceptance definition 2e_PossDupNotReceived).
s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=3, possdup=True), s.m("A", "B", "5", seq=4)]
case("S06-17", "A PossDup message with the expected number fills that number: no gap after it", "FIX.4.4", "fix",
     "FIX session protocol (PossDupFlag: process if MsgSeqNum not yet received); QuickFIX 2e_PossDupNotReceived.def; "
     "TR-003 'Messages with PossDupFlag=Y don't advance'", lines, {"gaps": []})
# A SequenceReset may only move the expected number forward (QuickFIX acceptance definition 11c_NewSeqNoLess).
s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "4", [(36, 1)]), s.m("A", "B", "0", seq=4)]
case("S06-18", "A SequenceReset to a lower number is not followed by a false gap", "FIX.4.4", "fix",
     "FIX SequenceReset: NewSeqNo may only increase the expected number; QuickFIX 11c_NewSeqNoLess.def; TR-003",
     lines, {"gaps": []})

# =============================================================================== section 7
for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    f1, f2 = ("1", "2") if v == "FIX.4.2" else ("F", "F")
    lines = [s.nos("CLI", "BRK", "C1", qty=100, px=10, acct="ACC1"),
             s.er("BRK", "CLI", "C1", "O1", "E1", "0", "0"),
             s.er("BRK", "CLI", "C1", "O1", "E2", f1, "1", lq=30, lp=10, cum=30, avg=10),
             s.m("CLI", "BRK", "G", [(11, "C2"), (41, "C1"), (21, 1), (55, "ACME"), (54, 1), (38, 200), (40, 2), (44, "10.5")]),
             s.er("BRK", "CLI", "C2", "O1", "E3", "E", "E", orig="C1", qty=100, cum=30, avg=10),
             s.er("BRK", "CLI", "C2", "O1", "E4", "5", "5" if v == "FIX.4.2" else "1", orig="C1", qty=200, cum=30, avg=10),
             s.m("CLI", "BRK", "G", [(11, "C3"), (41, "C2"), (21, 1), (55, "ACME"), (54, 1), (38, 20), (40, 2), (44, "10.5")]),
             s.m("BRK", "CLI", "9", [(37, "O1"), (11, "C3"), (41, "C2"), (39, 1), (434, 2), (102, 0)]),
             s.er("BRK", "CLI", "C2", "O1", "E5", f1, "1", lq=70, lp="10.5", qty=200, cum=100, avg="10.35"),
             s.m("CLI", "BRK", "F", [(11, "C4"), (41, "C2"), (55, "ACME"), (54, 1), (38, 200)]),
             s.er("BRK", "CLI", "C4", "O1", "E6", "6", "6", orig="C2", qty=200, cum=100, avg="10.35"),
             s.er("BRK", "CLI", "C4", "O1", "E7", f1, "6", orig="C2", lq=10, lp="10.5", qty=200, cum=110, avg="10.3636"),
             s.er("BRK", "CLI", "C4", "O1", "E8", "4", "4", orig="C2", qty=200, cum=110, avg="10.3636"),
             s.nos("CLI", "BRK", "C9", sym="ZETA", side=2, qty=5, acct="ACC2"),
             s.er("BRK", "CLI", "C9", "NONE", "E9", "8", "8", sym="ZETA", side=2, qty=5),
             s.m("CLI", "BRK", "F", [(11, "C10"), (41, "C7"), (55, "ZETA"), (54, 2), (38, 5)]),
             s.m("BRK", "CLI", "9", [(37, "NONE"), (11, "C10"), (41, "C7"), (39, 8), (434, 1), (102, 1)])]
    case(f"S07-01-{v[-3:]}", "A cancel/replace chain with fills is one order; figures are exact", v, "prd",
         "AC-009, AC-035, AC-036, AC-039..AC-047; design 12 (OrderID NONE)", lines,
         {"events": ["1:NewOrder", "2:Acknowledgement", "3:Fill", "4:ReplaceRequest", "5:ExecutionReport (ExecType E)",
                     "6:Replaced", "7:ReplaceRequest", "8:CancelReject", "9:Fill", "10:CancelRequest",
                     "11:ExecutionReport (ExecType 6)", "12:Fill", "13:Cancelled", "14:NewOrder",
                     "15:ExecutionReport (ExecType 8)", "16:CancelRequest", "17:CancelReject"],
          "groups": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], [14, 15], [16, 17]],
          "trades": {"ACME": row(buy_orders=1, bought="110", avg_buy="10.3636", net="+110"),
                     "ZETA": row(sell_orders=1)},
          "stats": {"orders": 3}})
    case(f"S07-02-{v[-3:]}", "Selecting an order shows its messages, terms and last state", v, "prd",
         "AC-036, AC-038, AC-049; design 8.2", lines,
         {"shown": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
          "banner": ["C1 · C2 · C3 · C4 · O1", "100 ACME @ 10", "110 filled @ 10.3636"],
          "trades": {"ACME": row(buy_orders=1, bought="110", avg_buy="10.3636", net="+110")},
          "stats_text": ["13 of 17 messages", "0 sequence gaps", "1 order"]},
         view={"orderId": "C3", "filters": {}})
    case(f"S07-03-{v[-3:]}", "The Account filter keeps every message of the account's orders", v, "prd",
         "AC-050, AC-051, AC-053", lines,
         {"shown": [14, 15], "trades": {"ZETA": row(sell_orders=1)},
          "filter_options": {"Account": ["All", "ACC1", "ACC2"], "SenderCompID": ["All", "BRK", "CLI"],
                             "SenderSubID": ["All"], "TargetCompID": ["All", "BRK", "CLI"], "TargetSubID": ["All"]}},
         view={"orderId": None, "filters": {"account": "ACC2"}})

# Trade cancels and corrections (AC-042 .. AC-044)
for v in ("FIX.4.2", "FIX.4.4"):
    s = S(v)
    F, H, G = ("2", "2", "2") if v == "FIX.4.2" else ("F", "H", "G")
    lines = [s.nos("A", "B", "C1", qty=300, px=10),
             s.er("B", "A", "C1", "O1", "E1", F, "1", lq=100, lp=10, cum=100, avg=10),
             s.er("B", "A", "C1", "O1", "E2", F, "1", lq=100, lp=11, cum=200, avg="10.5"),
             s.er("B", "A", "C1", "O1", "E3", F, "2", lq=100, lp=12, cum=300, avg=11),
             s.er("B", "A", "C1", "O1", "E4", G, "2", trans=2, ref="E1", lq=50, lp=9, cum=250, avg="11.0"),   # correct E1
             s.er("B", "A", "C1", "O1", "E5", G, "2", trans=2, ref="E4", lq=60, lp=8, cum=260, avg="10.6923"),  # correct again via E4
             s.er("B", "A", "C1", "O1", "E6", H, "1", trans=1, ref="E2", lq=100, lp=11, cum=160, avg="10.5"),   # bust E2
             s.er("B", "A", "C1", "O1", "E7", H, "1", trans=1, ref="E5", lq=60, lp=8, cum=100, avg=12),         # bust E1 via E5
             s.er("B", "A", "C1", "O1", "E8", H, "1", trans=1, ref="NOPE", lq=10, lp=1, cum=100, avg=12),       # unmatched bust
             s.er("B", "A", "C1", "O1", "E9", G, "1", trans=2, ref="GONE", lq=25, lp=20, cum=125, avg="13.6"),  # unmatched correct
             s.er("B", "A", "C1", "O1", "E6", H, "1", trans=1, ref="E2", lq=100, lp=11, cum=160, avg="10.5", seq=6, possdup=True)]
    case(f"S07-04-{v[-3:]}", "Trade cancels and corrections, by original or corrected ExecID, and unmatched ones", v,
         "prd", "AC-042, AC-043, AC-044; design 13", lines,
         {"events": ["1:NewOrder", "2:Fill", "3:Fill", "4:Fill", "5:TradeCorrect", "6:TradeCorrect", "7:TradeCancel",
                     "8:TradeCancel", "9:TradeCancel", "10:TradeCorrect", "11:TradeCancel"],
          "trades": {"ACME": row(buy_orders=1, bought="125", avg_buy="13.6", net="+125")}, "unmatched": 2})

# A trade cancel that stands before its fill in the log (two logs merged, or sorted by another clock)
s = S()
lines = [s.nos("A", "B", "C1", qty=100, px=10),
         s.er("B", "A", "C1", "O1", "E2", "H", "0", ref="E1", lq=100, lp=10, seq=2),
         s.er("B", "A", "C1", "O1", "E1", "F", "2", lq=100, lp=10, cum=100, avg=10, seq=1)]
case("S07-05", "A trade cancel listed before the fill it names still removes that fill", "FIX.4.4", "prd",
     "AC-041 'as they stand at the end of the log', AC-042, AC-044 'not in the log'; brief 7 (reports before earlier events)",
     lines, {"trades": {"ACME": row(buy_orders=1)}, "unmatched": 0})

# Order identifiers are scoped to a session in FIX: ClOrdID is unique per sender, OrderID / ExecID per venue.
s = S()
lines = [s.nos("CLI1", "BRK", "1", sym="AAA", side=1, qty=100, acct="ACC1"),
         s.nos("CLI2", "BRK", "1", sym="BBB", side=2, qty=50, acct="ACC2"),
         s.er("BRK", "CLI1", "1", "O-1", "E1", "F", "2", sym="AAA", side=1, lq=100, lp=5, cum=100, avg=5),
         s.er("BRK", "CLI2", "1", "O-2", "E2", "F", "2", sym="BBB", side=2, qty=50, lq=50, lp=7, cum=50, avg=7)]
case("S07-06", "The same ClOrdID used by two clients is two orders", "multi", "fix",
     "Brief 6, 7, 11; FIX: ClOrdID is unique per order sender; AC-035 joins on the value alone", lines,
     {"groups": [[1, 3], [2, 4]], "stats": {"orders": 2}}, folder="multi-session")
case("S07-07", "The Account filter does not show another client's order that reuses a ClOrdID", "multi", "fix",
     "Brief 11; US-009 'one client's flow in a shared log'; AC-051 follows AC-035", lines,
     {"shown": [1, 3], "trades": {"AAA": row(buy_orders=1, bought="100", avg_buy="5", net="+100")}},
     folder="multi-session", view={"orderId": None, "filters": {"account": "ACC1"}})

s = S()
lines = [s.nos("CLI", "VENUEA", "A1", qty=100), s.nos("CLI", "VENUEB", "B1", qty=200),
         s.er("VENUEA", "CLI", "A1", "1", "1", "F", "2", lq=100, lp=10, cum=100, avg=10),
         s.er("VENUEB", "CLI", "B1", "1", "1", "F", "2", qty=200, lq=200, lp=11, cum=200, avg=11)]
case("S07-08", "Two venues that both use OrderID 1 / ExecID 1: both fills count, and the orders stay apart", "multi",
     "fix", "Brief 6, 11; FIX: OrderID and ExecID are unique per executing party; AC-041 keys on 37+17 alone", lines,
     {"trades": {"ACME": row(buy_orders=2, bought="300", avg_buy="10.6667", net="+300")},
      "groups": [[1, 3], [2, 4]]}, folder="multi-session")

s = S()
lines = [s.nos("CLI", "BRK", "A1", qty=100), s.nos("CLI", "BRK", "B1", qty=200),
         s.er("BRK", "CLI", "A1", "O1", "E1", "F", "2", lq=100, lp=10, cum=100, avg=10),
         s.er("BRK", "CLI", "B1", "O2", "E1", "F", "2", qty=200, lq=200, lp=11, cum=200, avg=11)]
case("S07-09", "The same ExecID on two different orders is two executions", "FIX.4.4", "prd", "AC-041 (OrderID and ExecID)",
     lines, {"trades": {"ACME": row(buy_orders=2, bought="300", avg_buy="10.6667", net="+300")}})

# The same execution seen twice: once on the order session, once on a drop copy with other CompIDs.
s = S()
fill = dict(lq=100, lp=10, cum=100, avg=10)
lines = [s.nos("CLI", "BRK", "A1", qty=100), s.er("BRK", "CLI", "A1", "O1", "E1", "F", "2", **fill),
         s.er("BRK", "DROP", "A1", "O1", "E1", "F", "2", **fill)]
case("S07-10", "An execution seen again on a drop copy is counted once", "multi", "prd", "AC-041", lines,
     {"trades": {"ACME": row(buy_orders=1, bought="100", avg_buy="10", net="+100")}}, folder="multi-session")

# An id that is a ClOrdID of one order and the OrderID of another (numeric ids on both sides are common).
s = S()
lines = [s.nos("CLI1", "BRK", "1001", sym="AAA", side=1, qty=100),
         s.nos("CLI2", "BRK", "ZZ9", sym="BBB", side=2, qty=50),
         s.er("BRK", "CLI1", "1001", "7", "E1", "0", "0", sym="AAA"),
         s.er("BRK", "CLI2", "ZZ9", "1001", "E2", "F", "2", sym="BBB", side=2, qty=50, lq=50, lp=7, cum=50, avg=7)]
case("S07-11", "Clicking OrderID 1001 opens the order that has that OrderID", "multi", "prd",
     "AC-034, AC-036 'shows only that order's messages'; design 12 findOrder takes the id alone", lines,
     {"click": {"card": 4, "tag": "37", "shown": [2, 4], "banner": ["ZZ9"]}}, folder="multi-session")

# The state in the order banner when the last report in the log is a resend of an older one.
s = S()
lines = [s.nos("A", "B", "C1", qty=100, px=10),
         s.er("B", "A", "C1", "O1", "E1", "F", "1", lq=40, lp=10, cum=40, avg=10),
         s.er("B", "A", "C1", "O1", "E2", "F", "2", lq=60, lp=10, cum=100, avg=10),
         s.er("B", "A", "C1", "O1", "E1", "F", "1", lq=40, lp=10, cum=40, avg=10, seq=1, possdup=True)]
case("S07-12", "The order's latest state is not taken from a resent older report", "FIX.4.4", "fix",
     "Brief 6, 7 (duplicate and late reports); AC-036 takes the last ExecutionReport in the log", lines,
     {"banner": ["100 filled @ 10"], "trades": {"ACME": row(buy_orders=1, bought="100", avg_buy="10", net="+100")}},
     view={"orderId": "C1", "filters": {}})

# Late / early reports: a fill that stands before its NewOrderSingle is still part of the order and counted.
s = S()
lines = [s.er("B", "A", "C1", "O1", "E1", "F", "2", lq=100, lp=10, cum=100, avg=10), s.nos("A", "B", "C1", qty=100, px=10)]
case("S07-13", "A fill listed before its NewOrderSingle is grouped with it and counted", "FIX.4.4", "prd",
     "AC-035, AC-041", lines, {"groups": [[1, 2]], "trades": {"ACME": row(buy_orders=1, bought="100", avg_buy="10", net="+100")}})

# Sides, and fills that carry no quantity (AC-041, AC-047). CumQty is never used as a fill.
s = S()
lines = [s.nos("A", "B", "C1", side=5, qty=100), s.nos("A", "B", "C2", side=3, qty=100), s.nos("A", "B", "C3", side=8, qty=100),
         s.nos("A", "B", "C4", side=6, qty=100), s.nos("A", "B", "C5", side=4, qty=100),
         s.er("B", "A", "C1", "O1", "E1", "F", "2", side=5, lq=100, lp=10, cum=100, avg=10),
         s.er("B", "A", "C2", "O2", "E2", "F", "1", side=3, lq=0, lp=0, cum=70, avg=10),
         s.er("B", "A", "C3", "O3", "E3", "F", "2", side=8, lq=100, lp=10, cum=100, avg=10),
         s.er("B", "A", "C4", "O4", "E4", "F", "2", side=6, lq=30, lp=11, cum=100, avg=10),
         s.er("B", "A", "C5", "O5", "E5", "F", "2", side=4, lq=20, lp=12, cum=100, avg=10),
         s.er("B", "A", "C6", "O6", "E6", "F", "2", sym=None, lq=100, lp=10, cum=100, avg=10)]
case("S07-14", "Buy and sell sides, fills without LastQty, messages without Symbol", "FIX.4.4", "prd", "AC-041, AC-047",
     lines, {"trades": {"ACME": row(buy_orders=1, sell_orders=3, sold="150", avg_sell="10.4667", net="-150")}})

# Decimal arithmetic: figures whose exact decimal value is known.
s = S()
lines = [s.nos("A", "B", "C1", sym="FXA", qty=3), s.nos("A", "B", "C2", sym="FXB", qty=3),
         s.nos("A", "B", "C3", sym="FXC", side=2, qty=3)]
n = 0
for sym, side, fills in (("FXA", 1, [("0.1", "1.1"), ("0.2", "1.2"), ("0.7", "1.3")]),
                         ("FXB", 1, [("1", "10.0001"), ("1", "10.0002"), ("2", "10.0004")]),
                         ("FXC", 2, [("0.0001", "100"), ("0.0002", "100"), ("3", "0.3333")])):
    for q, p in fills:
        n += 1
        lines.append(s.er("B", "A", f"C{'ABC'.index(sym[-1]) + 1}", f"O{sym}", f"E{n}", "F", "1", sym=sym, side=side, lq=q, lp=p))
case("S07-15", "Fractional quantities and prices: sums and weighted averages are exact to 4 places", "FIX.4.4", "prd",
     "AC-045, AC-046; design 13 'Figures'", lines,
     {"trades": {"FXA": row(buy_orders=1, bought="1", avg_buy="1.26", net="+1"),
                 "FXB": row(buy_orders=1, bought="4", avg_buy="10.0003", net="+4"),
                 "FXC": row(sell_orders=1, sold="3.0003", avg_sell="0.3433", net="-3.0003")}})

# An average that is exactly representable to 4 places only in decimal: (1 x 1.0001 + 1 x 1.0004) / 2 = 1.00025;
# and one that is not a tie at all: three fills whose mean is 0.00015 exactly -> ties are flagged in the manifest.
s = S()
lines = [s.nos("A", "B", "C1", sym="TIE", qty=2)]
lines += [s.er("B", "A", "C1", "O1", "E1", "F", "1", sym="TIE", lq=1, lp="1.005"),
          s.er("B", "A", "C1", "O1", "E2", "F", "2", sym="TIE", lq=1, lp="1.0001")]
case("S07-16", "Average price (1 x 1.005 + 1 x 1.0001) / 2 = 1.00255 exactly is shown as 1.0026", "FIX.4.4", "prd",
     "AC-045; the PRD names no rounding mode, but half-up and half-even both give 1.0026", lines,
     {"trades_fields": {"TIE": {"avgBuy": ["1.0026"]}}})

# =============================================================================== section 8
s = S()
lines = [s.er("B", "A", "C1", "O1", "E1", "F", "2", lq=100, lp=10, cum=100, avg=10),
         s.m("B", "A", "8", [(37, "O2"), (11, "C2"), (453, 2), (448, "BRK1"), (447, "D"), (452, 1), (448, "TRD9"),
                             (447, "D"), (452, 12), (17, "E2"), (150, "F"), (39, 2), (55, "ACME"), (54, 1), (32, 5),
                             (31, 10), (151, 0), (14, 5), (6, 10), (136, 2), (137, "1.5"), (138, "USD"), (139, 4),
                             (137, "0.5"), (138, "USD"), (139, 7)])]
case("S08-01", "Repeated tags are listed in order, none dropped, none an error", "FIX.4.4", "prd", "PRD Scope; design 6",
     lines, {"tag_sequence": {"2": [8, 9, 35, 49, 56, 34, 52, 37, 11, 453, 448, 447, 452, 448, 447, 452, 17, 150, 39,
                                   55, 54, 32, 31, 151, 14, 6, 136, 137, 138, 139, 137, 138, 139, 10]},
             "rows": [{"number": 2, "tag": "448", "value": "TRD9"}, {"number": 2, "tag": "139", "value": "7"}],
             "stats": {"malformed": 0, "valid": 2}})
s = S("FIX.4.2")
lines = [s.m("A", "B", "E", [(66, "L1"), (394, 1), (68, 2), (73, 2), (11, "LA"), (67, 1), (55, "ACME"), (54, 1), (38, 100),
                             (40, 1), (11, "LB"), (67, 2), (55, "ZETA"), (54, 2), (38, 50), (40, 1)])]
case("S08-02", "A FIX 4.2 NewOrderList keeps both orders' fields, in order", "FIX.4.2", "prd", "PRD Scope; design 6",
     lines, {"tag_sequence": {"1": [8, 9, 35, 49, 56, 34, 52, 66, 394, 68, 73, 11, 67, 55, 54, 38, 40, 11, 67, 55, 54,
                                   38, 40, 10]}, "stats": {"malformed": 0}})

# =============================================================================== section 9 (single-message format cases)
s = S()
a, b, c = s.m("A", "B", "A", LOGON), s.m("A", "B", "0"), s.m("A", "B", "0", seq=5)
case("S09-01", "Empty input", "FIX.4.4", "prd", "design 8.2", [], {"stats": {"messages": 0, "valid": 0, "malformed": 0},
     "empty_text": "No FIX messages found in the pasted text."}, text="")
case("S09-02", "Only empty lines and non-FIX lines", "FIX.4.4", "prd", "TR-002", [],
     {"stats": {"messages": 0}}, text="\n\n   \nINFO starting gateway on port 9876\n\n")
case("S09-03", "Timeline order follows the log, not SendingTime", "FIX.4.4", "prd", "AC-007",
     [s.m("A", "B", "0", seq=7, time="20261127-23:59:59.000"), s.m("A", "B", "0", seq=8, time="20261127-00:00:01.000"),
      s.m("A", "B", "5", seq=9, time="20261126-12:00:00.000")],
     {"events": ["1:Heartbeat", "2:Heartbeat", "3:Logout"], "gaps": []})
half = b.index("52=") + 8          # the cut falls inside the SendingTime value
text = a + "\n" + b[:half]
case("S09-04", "Truncated input: the cut message is an error, the one before it is kept", "FIX.4.4", "prd",
     "AC-012, AC-014; TR-002", [], {"stats": {"messages": 2, "valid": 1, "malformed": 1},
                                    "errors": [{"number": 2, "rule": "missing_checksum",
                                                "position": [len(text), len(text) + 1]}]},
     text=text)
text = a + "\n" + b[:half] + "\n" + b[half:] + "\n" + c + "\n"
case("S09-05", "A message wrapped over two lines is reported, not silently dropped; its neighbours are kept",
     "FIX.4.4", "prd", "design 3 'a message never crosses a line end'; AC-012, AC-014", [],
     {"stats": {"messages": 3, "valid": 2, "malformed": 1}, "error_numbers": [2]}, text=text)

# =============================================================================== section 10 (malformed)
def bad(cid, feature, kind, basis, text, expect, version="FIX.4.4", note=None):
    case(cid, feature, version, kind, basis, [], expect, folder="malformed", text=text, note=note)


s = S()
good1, good2 = s.m("A", "B", "A", LOGON), None
body = [(11, "X1"), (21, 1), (55, "ACME"), (54, 1), (38, 100), (40, 1)]
m_ok = s.m("A", "B", "D", body)
good2 = s.m("A", "B", "0")


def wrap(mid):
    return good1 + "\n" + mid + "\n" + good2 + "\n"


NEIGH = {"valid_numbers": [1, 3], "events_include": ["1:Logon", "3:Heartbeat"]}
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
true_len = int(m_ok.split(SOH)[1][2:])
m_len = s2.m("A", "B", "D", body, body_length=true_len + 4)
t = wrap(m_len)
bad("S10-01", "Wrong BodyLength", "prd", "TR-002; AC-012, AC-015", t,
    {"errors": [{"number": 2, "rule": "body_length", "position": fpos(t, "9=", 1),
                 "text": f"Message 2: BodyLength (9) says {true_len + 4}, actual {true_len} at position {fpos(t, '9=', 1)}"}],
     **NEIGH, "stats": {"messages": 3, "valid": 2, "malformed": 1}, "trades": {}})
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
m_ck = s2.m("A", "B", "D", body, checksum=f"{(int(m_ok[-4:-1]) + 1) % 256:03d}")
t = wrap(m_ck)
bad("S10-02", "Wrong CheckSum", "prd", "TR-002; AC-012", t,
    {"errors": [{"number": 2, "rule": "checksum", "position": fpos(t, "10=", 1)}], **NEIGH, "trades": {}})
t = wrap(m_ok.replace("8=FIX.4.4" + SOH, ""))
bad("S10-03", "Missing BeginString: the message is reported as malformed", "fix",
    "Brief 10; TR-002 'first three fields are not 8, 9 and 35' but 'a message starts at 8=FIX'", t,
    {"stats": {"messages": 3, "malformed": 1}, "trades": {}})
f = m_ok.split(SOH)
t = wrap(SOH.join([f[0], f[2], f[1]] + f[3:]))
bad("S10-04", "BodyLength and MsgType swapped", "prd", "TR-002; design 3.8", t,
    {"errors": [{"number": 2, "rule": "header_order", "position": pos(t, "35=D")}], **NEIGH, "trades": {}})
t = wrap(SOH.join([f[0], f[1]] + f[3:]))
bad("S10-05", "MsgType missing", "prd", "TR-002", t, {"errors": [{"number": 2, "rule": "header_order"}], **NEIGH, "trades": {}})
t = wrap(SOH.join([f[0]] + f[2:]))
bad("S10-06", "BodyLength missing", "prd", "TR-002", t, {"errors": [{"number": 2, "rule": "header_order"}], **NEIGH, "trades": {}})
cut = m_ok[:m_ok.index("10=")]
t = wrap(cut)
bad("S10-07", "Missing trailer", "prd", "TR-002; AC-015", t,
    {"errors": [{"number": 2, "rule": "missing_checksum", "position": [len(good1) + 1 + len(cut), len(good1) + 1 + len(cut) + 1]}], **NEIGH, "trades": {}})
t = wrap(m_ok.replace("55=ACME", "55ACME"))
bad("S10-08", "A field without '='", "prd", "TR-002", t,
    {"errors": [{"number": 2, "rule": "field_without_equals", "position": pos(t, "55ACME")}], **NEIGH, "trades": {}})
for i, tag in enumerate(["abc", "0", "-5", "007", "1.5", "", "1234567890"]):
    t = wrap(m_ok.replace("55=ACME", f"{tag}=ACME"))
    bad(f"S10-09-{i + 1}", f"A tag that is not a positive integer: '{tag}'", "prd", "TR-002; design 3.8.2", t,
        {"errors": [{"number": 2, "rule": "bad_tag", "position": pos(t, f"{SOH}{tag}=ACME") + 1}], **NEIGH, "trades": {}})
t = wrap(m_ok.replace(SOH, ";"))
bad("S10-10", "An unsupported delimiter (;) is reported, not misread", "prd", "TR-002; design 11", t,
    {"errors": [{"number": 2, "rule": "header_order"}], **NEIGH, "trades": {}})
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
m_eq = s2.m("A", "B", "D", body + [(58, "a=b=c|d^A<SOH>e"), (5001, "=")])
t = wrap(m_eq)
bad("S10-11", "Equals signs and other delimiter forms inside a value of an SOH message are kept", "prd", "TR-002", t,
    {"stats": {"messages": 3, "valid": 3, "malformed": 0},
     "rows": [{"number": 2, "tag": "58", "value": "a=b=c|d^A<SOH>e"}, {"number": 2, "tag": "5001", "value": "="}]})
for form, sep in (("pipe", "|"), ("caret", "^A"), ("angle", "<SOH>")):
    val = "left|right || end|".replace("|", sep)
    s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
    mm = s2.m("A", "B", "D", body + [(58, val), (5001, f"a{sep}b")]).replace(SOH, sep)
    t = wrap(mm)
    bad(f"S10-12-{form}", f"The delimiter inside a value, {form} form", "prd", "TR-002 'A delimiter inside a value'", t,
        {"stats": {"messages": 3, "valid": 3, "malformed": 0},
         "rows": [{"number": 2, "tag": "58", "value": val}, {"number": 2, "tag": "5001", "value": f"a{sep}b"}]})
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
mm = s2.m("A", "B", "D", body + [(58, "see|44=1 for price")]).replace(SOH, "|")
t = wrap(mm)
bad("S10-13", "The one case text cannot settle (value holds delimiter + digits + '='): a CheckSum error", "prd",
    "TR-002 'The one case that text cannot settle'", t, {"errors": [{"number": 2, "rule": "checksum"}], **NEIGH, "trades": {}})
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
t = wrap(s2.m("A", "B", "ZZ", body + [(55, "DUP2"), (54, "9"), (9999, "x")]))
bad("S10-14", "Invalid MsgType, unknown tag, invalid enum, duplicate fields: decoded, no event, first value counts",
    "prd", "AC-004; design 6, 11", t,
    {"stats": {"messages": 3, "valid": 3, "malformed": 0}, "events": ["1:Logon", "3:Heartbeat"],
     "labels_any": {"2": ["ZZ", "unknown"]}, "rows": [{"number": 2, "tag": "55", "value": "DUP2"}], "trades": {}})
for i, (q, why) in enumerate([("0x10", "hexadecimal"), ("1e3", "exponent"), (" 100 ", "spaces"), ("0b11", "binary"),
                              ("+100", "plus sign"), ("abc", "text"), ("", "empty"), ("-100", "negative"),
                              ("NaN", "NaN"), ("Infinity", "Infinity"), ("1,000", "thousands separator")]):
    s2 = S()
    t = s2.er("B", "A", "C1", "O1", "E1", "F", "2", lq=q, lp=10, cum=100, avg=10) + "\n"
    bad(f"S10-15-{i + 1:02d}", f"LastQty '{q}' ({why}) is not a FIX quantity and is not counted as traded", "fix",
        "FIX Qty/float datatype: digits with an optional decimal point; design 13 'a finite number above zero'", t,
        {"trades": {}})
s2 = S()
t = s2.er("B", "A", "C1", "O1", "E1", "F", "2", lq=100, lp="0x10", cum=100, avg=10) + "\n"
bad("S10-15-12", "LastPx '0x10' is not a FIX price and gives no average", "fix", "FIX Price/float datatype", t,
    {"trades_fields": {"ACME": {"bought": "100", "avgBuy": DASH}}})
s2 = S()
t = "\n".join([s2.nos("A", "B", "C1", qty="99999999999999999999"),
               s2.er("B", "A", "C1", "O1", "E1", "F", "1", lq="9007199254740993", lp="0.0001"),
               s2.er("B", "A", "C1", "O1", "E2", "F", "1", lq="2", lp="0.0001")]) + "\n"
bad("S10-16", "Very large quantities are summed exactly", "fix", "Brief 7, 10 (decimal arithmetic, extremely large values)", t,
    {"trades_fields": {"ACME": {"bought": "9007199254740995", "net": "+9007199254740995"}}})
s2 = S()
t = "\n".join([s2.er("B", "A", "C1", "O1", "E1", "F", "1", sym="BTC", lq="0.00004", lp="64000"),
               s2.er("B", "A", "C1", "O1", "E2", "F", "1", sym="BTC", lq="0.00004", lp="64000"),
               s2.er("B", "A", "C1", "O1", "E3", "F", "1", sym="EURUSD", lq="1000000", lp="1.08345")]) + "\n"
bad("S10-17", "Quantities and prices finer than 4 decimal places are not shown as other values", "fix",
    "Brief 7 (decimal arithmetic); design 13 'Figures' rounds every figure to 4 places", t,
    {"trades_fields": {"BTC": {"bought": "0.00008"}, "EURUSD": {"avgBuy": "1.08345"}}},
    note="By design 13 the tool shows 0.0001 and 1.0835 (or 1.0834).")
junk = "\x00\x02\x7f�  8= FIX 35=D garbage \x01\x01\x01 10=abc |||^A^A<SOH> =\x01=1\x01"
t = good1 + "\n" + junk + "\n" + m_ok + junk + "\n" + junk + good2 + "\n"
bad("S10-18", "Binary garbage before, between and after valid messages on the same lines", "prd", "AC-014; TR-002", t,
    {"stats": {"messages": 3, "valid": 3, "malformed": 0}, "events": ["1:Logon", "2:NewOrder", "3:Heartbeat"]})
t = good1 + "\n" + m_ok[:m_ok.index("34=")] + m_ck + m_ok + "\n" + good2 + "\n"
bad("S10-19", "A cut message, a corrupt message and a valid message on one line: the valid ones survive", "prd",
    "AC-014; design 3.2", t, {"stats": {"messages": 5, "valid": 3, "malformed": 2}, "valid_numbers": [1, 4, 5],
                              "events": ["1:Logon", "4:NewOrder", "5:Heartbeat"]})
for i, ck in enumerate(["7", "1234", "ab1", ""]):
    t = wrap(m_ok[:m_ok.index("10=")] + f"10={ck}" + SOH)
    bad(f"S10-20-{i + 1}", f"CheckSum that is not three digits: '{ck}'", "prd", "design 3.8.4", t,
        {"errors": [{"number": 2, "rule": "checksum_format"}], **NEIGH, "trades": {}})
t = wrap(m_ok.replace(f"9={true_len}", "9=12x"))
bad("S10-21", "BodyLength that is not a number", "prd", "design 3.8.5", t,
    {"errors": [{"number": 2, "rule": "body_length", "position": fpos(t, "9=", 1)}], **NEIGH, "trades": {}})
s2 = S(); s2.seq[("A", "B", None, None)] = 1; s2.t = 1
long_value = "L" * 150000
t = wrap(s2.m("A", "B", "D", body + [(58, long_value)]))
bad("S10-22", "A 150,000-character value", "prd", "TR-005; AC-014", t,
    {"stats": {"messages": 3, "valid": 3, "malformed": 0}, "events": ["1:Logon", "2:NewOrder", "3:Heartbeat"]})
# Unusual but valid: leading zeros in BodyLength and MsgSeqNum (seen in the public sample log), empty value
s2 = S()
raw = s2.m("A", "B", "0", [(58, "")])
blen = raw.split(SOH)[1][2:]
padded = raw.replace(f"9={blen}{SOH}", f"9={int(blen):04d}{SOH}")
ck = sum(padded[:padded.index("10=")].encode()) % 256
padded = padded[:padded.index("10=")] + f"10={ck:03d}{SOH}"
bad("S10-23", "Unusual but valid: BodyLength with leading zeros and an empty value are accepted", "prd",
    "TR-002; design 6 ('58=' is shown as empty)", padded + "\n", {"stats": {"messages": 1, "valid": 1, "malformed": 0}})

# A wire-valid message whose Text holds ISO-8859-1 bytes (one byte per character). After a paste the tool sees
# characters, counts them as UTF-8 (two bytes each) and can no longer match BodyLength or CheckSum.
head = [(35, "0"), (49, "A"), (56, "B"), (34, 1), (52, "20261127-09:00:00.000"), (58, "Soci\u00e9t\u00e9 G\u00e9n\u00e9rale order")]
payload = "".join(f"{t}={v}{SOH}" for t, v in head)
first = f"8=FIX.4.4{SOH}9={len(payload.encode('latin-1'))}{SOH}"
latin = first + payload + f"10={sum((first + payload).encode('latin-1')) % 256:03d}{SOH}"
bad("S10-24", "A wire-valid message with ISO-8859-1 text (one byte per character) is not called malformed", "fix",
    "FIX messages are bytes, and BodyLength/CheckSum count bytes; design 3.7 counts the UTF-8 bytes of the pasted characters",
    latin + "\n", {"stats": {"messages": 1, "valid": 1, "malformed": 0}})

# =============================================================================== section 11
# A log merged from both sides of one connection: every message appears twice.
s = S()
orig = [s.m("CLI", "BRK", "A", LOGON), s.m("BRK", "CLI", "A", LOGON), s.nos("CLI", "BRK", "C1", qty=100, px=10),
        s.er("BRK", "CLI", "C1", "O1", "E1", "0", "0"), s.er("BRK", "CLI", "C1", "O1", "E2", "F", "2", lq=100, lp=10, cum=100, avg=10)]
lines = [x for m_ in orig for x in (m_, m_)]
case("S11-01", "A log merged from both sides of a connection does not double orders or fills", "multi", "fix",
     "Brief 11; AC-040 counts NewOrderSingle messages, AC-041 dedupes fills only", lines,
     {"trades": {"ACME": row(buy_orders=1, bought="100", avg_buy="10", net="+100")}, "stats": {"orders": 1}, "gaps": []},
     folder="multi-session")
# Incomplete log: starts mid-session, and a correction names an execution that is not in the log.
s = S()
s.seq[("BRK", "CLI", None, None)] = 4711
lines = [s.er("BRK", "CLI", "C1", "O1", "E9", "G", "2", ref="E1", lq=80, lp=10, cum=80, avg=10),
         s.er("BRK", "CLI", "C2", "O2", "E10", "H", "0", ref="E3", lq=10, lp=10), s.m("BRK", "CLI", "0")]
case("S11-02", "An incomplete log: no gap for the first message; an unmatched correction counts, an unmatched cancel does not",
     "FIX.4.4", "prd", "AC-044; design 7", lines,
     {"gaps": [], "trades": {"ACME": row(bought="80", avg_buy="10", net="+80")}, "unmatched": 2,
      "notes_include": ["2 trade cancels or corrections refer to an execution that is not in this log."]},
     folder="multi-session")
# A sequence reset on one session while another goes on.
s = S()
lines = [s.m("A", "B", "A", LOGON), s.m("C", "B", "A", LOGON), s.m("A", "B", "0"), s.m("C", "B", "0"),
         s.m("A", "B", "A", LOGON + [(141, "Y")], seq=1), s.m("C", "B", "0"), s.m("A", "B", "0", seq=2),
         s.m("C", "B", "0", seq=5)]
case("S11-03", "A reset on one session leaves the other session's numbers alone", "FIX.4.4", "prd", "TR-003", lines,
     {"gaps": [[8, 4, 5]]}, folder="multi-session")
# FIX 4.2 and FIX 4.4 sessions in one log
s = S()
lines = [s.nos("C42", "BRK", "A1", qty=100, begin="FIX.4.2"), s.nos("C44", "BRK", "B1", qty=100),
         s.er("BRK", "C42", "A1", "OA", "E1", "2", "2", lq=100, lp=10, cum=100, avg=10, begin="FIX.4.2"),
         s.er("BRK", "C44", "B1", "OB", "E2", "F", "2", lq=100, lp=12, cum=100, avg=12),
         s.er("BRK", "C42", "A1", "OA", "E3", "2", "2", trans=1, ref="E1", lq=100, lp=10, begin="FIX.4.2")]
case("S11-04", "FIX 4.2 and FIX 4.4 sessions in one log are each read by their own rules", "multi", "prd",
     "TR-001 (dictionary per message), TR-003", lines,
     {"events": ["1:NewOrder", "2:NewOrder", "3:Fill", "4:Fill", "5:TradeCancel"],
      "trades": {"ACME": row(buy_orders=2, bought="100", avg_buy="12", net="+100")},
      "rows": [{"number": 3, "tag": "32", "field": "LastShares"}, {"number": 4, "tag": "32", "field": "LastQty"}]},
     folder="multi-session")
