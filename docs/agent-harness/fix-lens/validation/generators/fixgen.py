"""Independent FIX 4.2 / 4.4 wire encoder, validator and traffic simulator.

Written for the FIX Lens validation from the FIX 4.2 and FIX 4.4 specifications. It shares no
code with the tool under test. Python standard library only; all quantities and prices are
`decimal.Decimal`; all randomness comes from one seeded `random.Random`.

Wire rules used (FIX 4.2 / 4.4, "Message format"):
  * every field is `tag=value` followed by SOH (0x01);
  * BodyLength (9) is the number of bytes after the SOH that ends field 9, up to and including
    the SOH that precedes `10=`;
  * CheckSum (10) is the sum of every byte before `10=`, modulo 256, as three digits.
"""
from __future__ import annotations

import random
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP

SOH = "\x01"


# ----------------------------------------------------------------------------- encoding
def encode(begin, fields, body_length=None, checksum=None):
    """One wire message as a str (SOH-delimited). `fields` excludes tags 8, 9 and 10."""
    body = "".join(f"{t}={v}{SOH}" for t, v in fields)
    blen = len(body.encode("utf-8")) if body_length is None else body_length
    head = f"8={begin}{SOH}9={blen}{SOH}"
    total = sum((head + body).encode("utf-8")) % 256
    ck = f"{total:03d}" if checksum is None else checksum
    return f"{head}{body}10={ck}{SOH}"


def validate_wire(raw):
    """Independent wire check of one SOH-delimited message. Returns (ok, reason, fields)."""
    data = raw.encode("utf-8")
    if not data.endswith(b"\x01"):
        return False, "no trailing SOH", []
    parts = data[:-1].split(b"\x01")
    fields = []
    for p in parts:
        if b"=" not in p:
            return False, "field without =", fields
        t, v = p.split(b"=", 1)
        if not t.isdigit() or t.startswith(b"0"):
            return False, "bad tag", fields
        fields.append((int(t), v.decode("utf-8")))
    if len(fields) < 4 or [f[0] for f in fields[:3]] != [8, 9, 35]:
        return False, "header order", fields
    if fields[-1][0] != 10 or len(fields[-1][1]) != 3 or not fields[-1][1].isdigit():
        return False, "trailer", fields
    start = len(parts[0]) + 1 + len(parts[1]) + 1
    end = len(data) - (len(parts[-1]) + 1)
    if not fields[1][1].isdigit() or int(fields[1][1]) != end - start:
        return False, f"BodyLength says {fields[1][1]}, actual {end - start}", fields
    if sum(data[:end]) % 256 != int(fields[-1][1]):
        return False, "CheckSum mismatch", fields
    return True, "", fields


def as_form(text, form):
    """Rewrite an SOH log into another delimiter form. Only valid when no value holds the text."""
    return text if form == "soh" else text.replace(SOH, {"pipe": "|", "caret": "^A", "angle": "<SOH>"}[form])


def q4(d, mode=ROUND_HALF_UP):
    return d.quantize(Decimal("0.0001"), rounding=mode)


def plain(d):
    """Decimal as the shortest plain string: no exponent, no trailing zeros."""
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def shown(d):
    """A figure as FIX Lens is specified to show it (design section 13, 'Figures'): 4 decimal
    places at most, no trailing zeros. Both rounding modes are returned because the PRD names none."""
    return sorted({plain(q4(d, ROUND_HALF_UP)), plain(q4(d, ROUND_HALF_EVEN))})


# ----------------------------------------------------------------------------- simulator
EVENT = {  # intent -> the event name the PRD (AC-008, AC-009, TR-003) gives it
    "logon": "Logon", "logout": "Logout", "hb": "Heartbeat", "testreq": "TestRequest",
    "resendreq": "ResendRequest", "gapfill": "GapFill", "seqreset": "Reset",
    "reject": "SessionReject", "bmr": "BusinessReject", "new": "NewOrder",
    "cxlreq": "CancelRequest", "replreq": "ReplaceRequest", "cxlrej": "CancelReject",
    "ack": "Acknowledgement", "fill": "Fill", "cancelled": "Cancelled", "replaced": "Replaced",
    "bust": "TradeCancel", "correct": "TradeCorrect", "status": "OrderStatus",
}
SIDE_NAME = {"1": "buy", "2": "sell", "5": "sell"}


class Sim:
    """A small market of clients and brokers. Every emitted message is recorded with what it means."""

    def __init__(self, seed, date="20261127", unique_ids=True):
        self.rng = random.Random(seed)
        self.seed = seed
        self.date = date
        self.ms = 9 * 3600 * 1000
        self.entries = []          # dicts: raw, intent, session, dir, seq, possdup, order (index), ...
        self.seq = {}              # (begin, sender, target, sendersub, targetsub) -> last MsgSeqNum used
        self.lost = {}             # direction -> first lost MsgSeqNum not yet noticed
        self.sessions = []
        self.orders = []
        self.unique_ids = unique_ids
        self.counters = {}
        self.gaps = []
        self.retransmissions = []
        self.resets = []

    # ---- plumbing
    def now(self):
        self.ms += self.rng.randint(1, 900)
        s, ms = divmod(self.ms, 1000)
        return f"{self.date}-{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}.{ms:03d}"

    def session(self, begin, client, broker, client_sub=None, broker_sub=None):
        s = {"id": len(self.sessions), "begin": begin, "client": client, "broker": broker,
             "client_sub": client_sub, "broker_sub": broker_sub}
        self.sessions.append(s)
        return s

    def nextid(self, key, prefix):
        self.counters[key] = self.counters.get(key, 0) + 1
        return f"{prefix}{self.counters[key]}"

    def emit(self, sess, from_client, mtype, body, intent, *, possdup=False, seq=None, lost=False,
             order=None, extra=None):
        """Send one message. `lost` consumes a sequence number but keeps the message out of the log."""
        a, b = (sess["client"], sess["broker"]) if from_client else (sess["broker"], sess["client"])
        sa, sb = (sess["client_sub"], sess["broker_sub"]) if from_client else (sess["broker_sub"], sess["client_sub"])
        d = (sess["id"], from_client)
        if seq is None:
            seq = self.seq.get(d, 0) + 1
            self.seq[d] = seq
        head = [(35, mtype), (49, a), (56, b)]
        if sa:
            head.append((50, sa))
        if sb:
            head.append((57, sb))
        head.append((34, seq))
        if possdup:
            head.append((43, "Y"))
        t = self.now()
        head.append((52, t))
        if possdup:
            head.append((122, t))
        if lost:
            self.lost.setdefault(d, seq)
            return None
        raw = encode(sess["begin"], head + list(body))
        e = {"raw": raw, "intent": intent, "session": sess["id"], "sender": a, "target": b, "seq": seq,
             "possdup": possdup, "order": order, "type": mtype, "begin": sess["begin"], "gap": None}
        if extra:
            e.update(extra)
        if not possdup and d in self.lost and seq > self.lost[d]:
            e["gap"] = [self.lost.pop(d), seq]
        self.entries.append(e)
        return e

    # ---- session-level choreography
    def logon(self, sess, reset=False):
        body = [(98, 0), (108, 30)] + ([(141, "Y")] if reset else [])
        if reset:
            self.seq[(sess["id"], True)] = 0
            self.seq[(sess["id"], False)] = 0
            self.lost.pop((sess["id"], True), None)
            self.lost.pop((sess["id"], False), None)
            self.resets.append({"session": sess["id"], "at_entry": len(self.entries)})
        self.emit(sess, True, "A", body, "logon")
        self.emit(sess, False, "A", body, "logon")

    def logout(self, sess):
        self.emit(sess, True, "5", [], "logout")
        self.emit(sess, False, "5", [], "logout")

    def heartbeat(self, sess, from_client):
        self.emit(sess, from_client, "0", [], "hb")

    def test_request(self, sess, from_client):
        rid = self.nextid("tr", "TEST")
        self.emit(sess, from_client, "1", [(112, rid)], "testreq")
        self.emit(sess, not from_client, "0", [(112, rid)], "hb")

    def lose_and_recover(self, sess, from_client, gapfill):
        """One message of this direction never reaches the log; the peer asks for it again."""
        d = (sess["id"], from_client)
        self.emit(sess, from_client, "0", [], "hb", lost=True)
        lost_seq = self.seq[d]
        self.emit(sess, from_client, "0", [], "hb")           # arrives: the gap shows here
        self.emit(sess, not from_client, "2", [(7, lost_seq), (16, 0)], "resendreq")
        if gapfill:   # admin messages are not resent: SequenceReset-GapFill, PossDupFlag=Y
            self.emit(sess, from_client, "4", [(123, "Y"), (36, self.seq[d] + 1)], "gapfill",
                      possdup=True, seq=lost_seq)
            self.retransmissions.append({"entry": len(self.entries) - 1, "kind": "gapfill"})

    # ---- orders
    def new_order(self, sess, sym, side, qty, px, account):
        c = sess["client"]
        o = {"index": len(self.orders), "session": sess["id"], "sess": sess, "sym": sym, "side": side,
             "qty": qty, "px": px, "account": account, "chain": [], "oid": None, "cum": Decimal(0),
             "execs": [], "status": None, "entries": [], "open": True, "pending": None,
             "rejections": 0, "cancelled": False}
        o["cl"] = self.clid(sess)
        o["chain"].append(o["cl"])
        self.orders.append(o)
        return o

    def clid(self, sess):
        if self.unique_ids:
            return self.nextid(("cl", sess["client"], sess["id"]), f"{sess['client']}.{sess['id']}.")
        return self.nextid(("cl", sess["id"]), "")

    def oid(self, sess):
        if self.unique_ids:
            return self.nextid(("oid", sess["broker"]), f"{sess['broker']}-O")
        return self.nextid(("oid", sess["id"]), "")

    def eid(self, sess):
        if self.unique_ids:
            return self.nextid(("eid", sess["broker"]), f"{sess['broker']}-E")
        return self.nextid(("eid", sess["id"]), "")

    def avg(self, o):
        alive = [x for x in o["execs"] if x["alive"]]
        tot = sum((x["qty"] for x in alive), Decimal(0))
        return (sum((x["qty"] * x["px"] for x in alive), Decimal(0)) / tot) if tot else Decimal(0)

    def client_msg(self, o, mtype, intent, cl, orig=None, qty=None, px=None):
        body = [(11, cl)]
        if orig:
            body.append((41, orig))
        if o["account"] and (mtype == "D" or self.rng.random() < 0.5):
            body.append((1, o["account"]))
        if mtype == "D":
            body.append((21, 1))
        body += [(55, o["sym"]), (54, o["side"]), (60, self.now())]
        if mtype != "F":
            body.append((38, plain(o["qty"] if qty is None else qty)))
            p = o["px"] if px is None else px
            body += [(40, 2), (44, plain(p))] if p is not None else [(40, 1)]
        else:
            body.append((38, plain(o["qty"])))
        e = self.emit(o["sess"], True, mtype, body, intent, order=o["index"])
        o["entries"].append(len(self.entries) - 1)
        return e

    def report(self, o, intent, exec_type, status, *, cl=None, orig=None, last_qty=None, last_px=None,
               ref=None, trans=None, exec_id=None, possdup=False, seq=None, with_account=None):
        """An ExecutionReport in the form of the session's version."""
        v42 = o["sess"]["begin"] == "FIX.4.2"
        eid = exec_id or self.eid(o["sess"])
        body = [(37, o["oid"] or "NONE"), (11, cl or o["cl"])]
        if orig:
            body.append((41, orig))
        body.append((17, eid))
        if v42:
            body.append((20, trans if trans is not None else 0))
        if ref:
            body.append((19, ref))
        body += [(150, exec_type), (39, status)]
        if with_account if with_account is not None else (o["account"] and self.rng.random() < 0.3):
            body.append((1, o["account"]))
        body += [(55, o["sym"]), (54, o["side"]), (38, plain(o["qty"]))]
        if o["px"] is not None:
            body.append((44, plain(o["px"])))
        body += [(32, plain(last_qty) if last_qty is not None else 0),
                 (31, plain(last_px) if last_px is not None else 0),
                 (151, plain(max(o["qty"] - o["cum"], Decimal(0))) if o["open"] else 0),
                 (14, plain(o["cum"])), (6, plain(q4(self.avg(o)))), (60, self.now())]
        name = EVENT.get(intent) or f"ExecutionReport (ExecType {exec_type})"
        e = self.emit(o["sess"], False, "8", body, intent, order=o["index"], possdup=possdup, seq=seq,
                      extra={"exec_id": eid, "event": name, "body": body})
        o["entries"].append(len(self.entries) - 1)
        o["last_report"] = {"status": str(status), "cum": plain(o["cum"]), "avg": plain(q4(self.avg(o)))}
        return e

    def fill(self, o, qty, px, status=None):
        v42 = o["sess"]["begin"] == "FIX.4.2"
        o["cum"] += qty
        full = o["cum"] >= o["qty"]
        x = {"qty": qty, "px": px, "alive": True, "order": o["index"], "sym": o["sym"], "side": o["side"]}
        o["execs"].append(x)
        true_status = "2" if full else "1"
        o["status"] = true_status
        if full:
            o["open"] = False
        et = true_status if v42 else "F"
        # `status` overrides the reported OrdStatus only (a fill while a cancel or replace is pending)
        e = self.report(o, "fill", et, status or true_status, last_qty=qty, last_px=px)
        x["id"] = e["exec_id"]
        x["ids"] = [e["exec_id"]]
        x["entry"] = len(self.entries) - 1
        return e

    def state_after_change(self, o):
        if o["status"] in ("4", "C", "3", "8"):      # cancelled, expired, done for day: stays closed
            return o["status"]
        return "0" if o["cum"] == 0 else ("2" if o["cum"] >= o["qty"] else "1")

    def bust(self, o, x):
        v42 = o["sess"]["begin"] == "FIX.4.2"
        x["alive"] = False
        o["cum"] -= x["qty"]
        o["status"] = self.state_after_change(o)
        o["open"] = o["status"] in ("0", "1")
        # FIX 4.2: ExecTransType=1 (Cancel); ExecType restates the order, and may well be 1 or 2.
        et = self.rng.choice(["1", "2", o["status"]]) if v42 else "H"
        e = self.report(o, "bust", et, o["status"], last_qty=x["qty"], last_px=x["px"], ref=x["ids"][-1],
                        trans=1 if v42 else None)
        x["ids"].append(e["exec_id"])
        return e

    def correct(self, o, x, qty, px):
        v42 = o["sess"]["begin"] == "FIX.4.2"
        o["cum"] += qty - x["qty"]
        x["qty"], x["px"] = qty, px
        o["status"] = self.state_after_change(o)
        o["open"] = o["status"] in ("0", "1")
        et = self.rng.choice(["1", "2"]) if v42 else "G"
        ref = self.rng.choice(x["ids"])      # the original ExecID or an earlier correction's (AC-043)
        e = self.report(o, "correct", et, o["status"], last_qty=qty, last_px=px, ref=ref,
                        trans=2 if v42 else None)
        x["ids"].append(e["exec_id"])
        return e

    # ---- one order's life, as a generator: it yields between messages so that flows interleave
    def life(self, sess, symbols, accounts):
        rng = self.rng
        sym, tick, lot = rng.choice(symbols)
        side = rng.choice(["1", "1", "2", "2", "5"])
        qty = Decimal(rng.randint(1, 40)) * lot
        base = Decimal(rng.randint(500, 90000)) * tick
        px = base if rng.random() < 0.8 else None
        o = self.new_order(sess, sym, side, qty, px, rng.choice(accounts))

        def price():
            return (px if px is not None else base) + Decimal(rng.randint(-20, 20)) * tick

        self.client_msg(o, "D", "new", o["cl"])
        yield
        if rng.random() < 0.08:
            o["status"], o["open"] = "8", False
            o["rejections"] += 1
            self.report(o, "er_other", "8", "8")
            return
        o["oid"] = self.oid(sess)
        if rng.random() < 0.3:
            self.report(o, "er_other", "A", "A")
            yield
        o["status"] = "0"
        self.report(o, "ack", "0", "0")
        yield
        for _ in range(rng.randint(0, 6)):
            if not o["open"]:
                # a filled order can still be busted or corrected
                alive = [x for x in o["execs"] if x["alive"]]
                if alive and rng.random() < 0.25:
                    self.bust(o, rng.choice(alive))
                    yield
                continue
            leaves = o["qty"] - o["cum"]
            act = rng.choice(["fill", "fill", "fill", "replace", "cancel", "bust", "correct", "status",
                              "dup", "pendingfill"])
            alive = [x for x in o["execs"] if x["alive"]]
            if act == "fill" and leaves > lot:
                q = Decimal(rng.randint(1, max(1, int(leaves / lot) - 1))) * lot
                self.fill(o, q, price())
                yield
            elif act in ("replace", "pendingfill"):
                new_cl = self.clid(sess)
                new_qty = o["cum"] + Decimal(rng.randint(1, 40)) * lot
                new_px = price() if px is not None else None
                self.client_msg(o, "G", "replreq", new_cl, orig=o["cl"], qty=new_qty, px=new_px)
                o["chain"].append(new_cl)
                yield
                self.report(o, "er_other", "E", "E", cl=new_cl, orig=o["cl"])
                yield
                if act == "pendingfill" and o["qty"] - o["cum"] > lot:
                    self.fill(o, lot, price(), status="E")     # a fill while the replace is pending
                    new_qty = max(new_qty, o["cum"] + lot)
                    yield
                if rng.random() < 0.25:
                    o["rejections"] += 1
                    body = [(37, o["oid"]), (11, new_cl), (41, o["cl"]), (39, o["status"]), (434, 2), (102, 0)]
                    self.emit(sess, False, "9", body, "cxlrej", order=o["index"])
                    o["entries"].append(len(self.entries) - 1)
                else:
                    old = o["cl"]
                    o["cl"], o["qty"] = new_cl, new_qty
                    if new_px is not None:
                        o["px"] = new_px
                    o["status"] = self.state_after_change(o)
                    st = "5" if sess["begin"] == "FIX.4.2" else o["status"]
                    self.report(o, "replaced", "5", st, cl=new_cl, orig=old)
                yield
            elif act == "cancel":
                new_cl = self.clid(sess)
                self.client_msg(o, "F", "cxlreq", new_cl, orig=o["cl"])
                o["chain"].append(new_cl)
                yield
                self.report(o, "er_other", "6", "6", cl=new_cl, orig=o["cl"])
                yield
                if rng.random() < 0.3 and o["qty"] - o["cum"] > lot:
                    self.fill(o, lot, price(), status="6")     # a fill while the cancel is pending
                    yield
                if rng.random() < 0.3:
                    o["rejections"] += 1
                    body = [(37, o["oid"]), (11, new_cl), (41, o["cl"]), (39, o["status"]), (434, 1), (102, 0)]
                    self.emit(sess, False, "9", body, "cxlrej", order=o["index"])
                    o["entries"].append(len(self.entries) - 1)
                    yield
                else:
                    old = o["cl"]
                    o["cl"], o["status"], o["open"], o["cancelled"] = new_cl, "4", False, True
                    self.report(o, "cancelled", "4", "4", cl=new_cl, orig=old)
                    yield
            elif act == "bust" and alive:
                self.bust(o, rng.choice(alive))
                yield
            elif act == "correct" and alive:
                x = rng.choice(alive)
                room = o["qty"] - (o["cum"] - x["qty"])
                q = Decimal(rng.randint(1, max(1, int(room / lot)))) * lot
                self.correct(o, x, q, price())
                yield
            elif act == "status":
                v42 = sess["begin"] == "FIX.4.2"
                self.report(o, "status", o["status"] if v42 else "I", o["status"], trans=3 if v42 else None)
                yield
            elif act == "dup" and o["entries"]:
                # the last execution report of this order is sent again, PossDupFlag=Y, same MsgSeqNum
                last = self.entries[o["entries"][-1]]
                if last["type"] == "8" and not last["possdup"]:
                    body = last["body"]
                    e = self.emit(sess, False, "8", body, last["intent"], possdup=True, seq=last["seq"],
                                  order=o["index"], extra={"exec_id": last["exec_id"], "event": last["event"],
                                                           "body": body})
                    o["entries"].append(len(self.entries) - 1)
                    self.retransmissions.append({"entry": len(self.entries) - 1, "kind": "possdup report"})
                    yield
        if o["open"]:
            end = rng.choice(["fill", "fill", "open", "expire", "dfd"])
            if end == "fill":
                self.fill(o, o["qty"] - o["cum"], price())
            elif end == "expire":
                o["status"], o["open"] = "C", False
                self.report(o, "er_other", "C", "C")
            elif end == "dfd":
                o["status"], o["open"] = "3", False
                self.report(o, "er_other", "3", "3")
            yield

    def run(self, flows):
        """Interleave the order flows at random until all are done."""
        live = list(flows)
        while live:
            f = self.rng.choice(live)
            try:
                next(f)
            except StopIteration:
                live.remove(f)
            if self.rng.random() < 0.04:
                s = self.rng.choice(self.sessions)
                self.heartbeat(s, self.rng.random() < 0.5)

    # ---- ground truth
    def truth(self):
        ents = self.entries
        for i, e in enumerate(ents):
            e["number"] = i + 1
        events, gaps = [], []
        for e in ents:
            if e["gap"]:
                gaps.append({"number": e["number"], "expected": e["gap"][0], "received": e["gap"][1],
                             "sender": e["sender"], "target": e["target"]})
                events.append(f"{e['number']}:SequenceGap")
            name = e.get("event") or EVENT.get(e["intent"])
            if name:
                events.append(f"{e['number']}:{name}")
        symbols, executions = {}, []
        for o in self.orders:
            row = symbols.setdefault(o["sym"], {"buy": {"orders": 0, "qty": Decimal(0), "notional": Decimal(0)},
                                                "sell": {"orders": 0, "qty": Decimal(0), "notional": Decimal(0)}})
            side = SIDE_NAME[o["side"]]
            row[side]["orders"] += 1
            for x in o["execs"]:
                executions.append({"order": o["index"], "exec_ids": x["ids"], "symbol": x["sym"], "side": side,
                                   "qty": plain(x["qty"]), "px": plain(x["px"]), "survives": x["alive"],
                                   "number": ents[x["entry"]]["number"]})
                if x["alive"]:
                    row[side]["qty"] += x["qty"]
                    row[side]["notional"] += x["qty"] * x["px"]
        trades = {}
        for sym, row in sorted(symbols.items()):
            b, s = row["buy"], row["sell"]
            net = b["qty"] - s["qty"]
            trades[sym] = {
                "buyOrders": str(b["orders"]), "bought": shown(b["qty"]),
                "avgBuy": shown(b["notional"] / b["qty"]) if b["qty"] else ["–"],
                "sellOrders": str(s["orders"]), "sold": shown(s["qty"]),
                "avgSell": shown(s["notional"] / s["qty"]) if s["qty"] else ["–"],
                "net": [("+" if net > 0 else "") + v for v in shown(net)],
                "exact": {"bought": plain(b["qty"]), "sold": plain(s["qty"]),
                          "buyNotional": plain(b["notional"]), "sellNotional": plain(s["notional"])},
            }
        orders = []
        for o in self.orders:
            orders.append({
                "order": o["index"], "session": o["session"], "account": o["account"], "symbol": o["sym"],
                "side": SIDE_NAME[o["side"]], "clOrdIds": o["chain"], "orderId": o["oid"],
                "numbers": [ents[i]["number"] for i in o["entries"]],
                "finalOrdStatus": o["status"], "filledQty": plain(o["cum"]), "avgPx": plain(q4(self.avg(o))),
                "lastReport": o.get("last_report"), "rejections": o["rejections"], "cancelled": o["cancelled"],
            })
        sessions = []
        for s in self.sessions:
            for from_client in (True, False):
                a, b = (s["client"], s["broker"]) if from_client else (s["broker"], s["client"])
                sa, sb = (s["client_sub"], s["broker_sub"]) if from_client else (s["broker_sub"], s["client_sub"])
                n = sum(1 for e in ents if e["session"] == s["id"] and e["sender"] == a)
                sessions.append({"session": s["id"], "begin": s["begin"], "sender": a, "target": b,
                                 "senderSub": sa, "targetSub": sb, "messages": n})
        return {
            "seed": self.seed, "messages": len(ents), "valid": len(ents), "invalid": 0,
            "sessions": sessions, "directions": len(sessions),
            "gaps": gaps, "events": events,
            "retransmissions": [{"number": ents[r["entry"]]["number"], "kind": r["kind"]} for r in self.retransmissions],
            "resets": [{"session": r["session"], "number": r["at_entry"] + 1} for r in self.resets],
            "orderCount": len(self.orders), "orders": orders, "executions": executions, "trades": trades,
            "rejections": sum(o["rejections"] for o in self.orders),
            "cancellations": sum(1 for o in self.orders if o["cancelled"]),
        }

    def text(self, eol="\n"):
        return eol.join(e["raw"] for e in self.entries) + eol
