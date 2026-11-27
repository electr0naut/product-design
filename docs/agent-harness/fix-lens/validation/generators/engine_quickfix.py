#!/usr/bin/env python3
"""Engine-generated traffic: a real QuickFIX initiator and acceptor talking over loopback TCP.

Second, independent source of FIX messages (brief section 5, method 1). The engine, not this
script, writes BeginString, BodyLength, MsgSeqNum, SendingTime and CheckSum, runs the session
protocol (logon, heartbeats, resend requests, gap fills, logout) and validates every application
message against the QuickFIX FIX42.xml / FIX44.xml dictionary.

Usage (quickfix 1.16.0 from PyPI must be importable):
    python engine_quickfix.py --spec <dir with FIX42.xml and FIX44.xml> --work <empty dir> --out <dir>

Writes, per version, the acceptor's message log as the engine wrote it (QuickFIX file-log format,
"<timestamp> : <message>" with SOH) and a ground-truth JSON taken from the application callbacks.
"""
import argparse
import json
import os
import random
import socket
import sys
import threading
import time
from decimal import Decimal

import quickfix as fix

SEED = 20261127


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def field(msg, tag):
    return msg.getField(tag) if msg.isSetField(tag) else None


class Broker(fix.Application):
    """Acceptor: acknowledges, fills in two parts, cancels and replaces. Records what it executed."""

    def __init__(self, v42):
        super().__init__()
        self.v42 = v42
        self.n = 0
        self.orders = {}
        self.executions = []
        self.app_in = []
        self.app_out = []
        self.admin = []
        self.lock = threading.Lock()

    def onCreate(self, sid): pass
    def onLogon(self, sid): pass
    def onLogout(self, sid): pass
    def toAdmin(self, m, sid): self.admin.append(("out", m.toString()))
    def fromAdmin(self, m, sid): self.admin.append(("in", m.toString()))
    def toApp(self, m, sid): self.app_out.append(m.toString())

    def nid(self, p):
        self.n += 1
        return f"{p}{self.n:05d}"

    def report(self, sid, o, exec_type, status, last_qty="0", last_px="0", orig=None, cl=None, ref=None, trans="0"):
        m = fix.Message()
        m.getHeader().setField(fix.MsgType("8"))
        eid = self.nid("X")
        pairs = [(37, o["oid"]), (11, cl or o["cl"]), (17, eid)]
        if orig:
            pairs.append((41, orig))
        if self.v42:
            pairs.append((20, trans))
        if ref:
            pairs.append((19, ref))
        pairs += [(150, exec_type), (39, status), (55, o["sym"]), (54, o["side"]), (38, str(o["qty"])),
                  (32, last_qty), (31, last_px), (151, str(max(o["qty"] - o["cum"], Decimal(0)))),
                  (14, str(o["cum"])), (6, str(o["avg"]))]
        for t, v in pairs:
            m.setField(fix.StringField(t, str(v)))
        fix.Session.sendToTarget(m, sid)
        return eid

    def fill(self, sid, o, qty, px):
        notional = o["avg"] * o["cum"] + qty * px
        o["cum"] += qty
        o["avg"] = (notional / o["cum"]).quantize(Decimal("0.0001"))
        full = o["cum"] >= o["qty"]
        st = "2" if full else "1"
        eid = self.report(sid, o, st if self.v42 else "F", st, str(qty), str(px))
        x = {"execId": eid, "orderId": o["oid"], "symbol": o["sym"], "side": o["side"], "qty": str(qty),
             "px": str(px), "survives": True}
        self.executions.append(x)
        o["execs"].append(x)

    def fromApp(self, m, sid):
        with self.lock:
            self.app_in.append(m.toString())
            t = m.getHeader().getField(35)
            if t == "D":
                o = {"cl": field(m, 11), "oid": self.nid("ORD"), "sym": field(m, 55), "side": field(m, 54),
                     "qty": Decimal(field(m, 38)), "px": Decimal(field(m, 44) or "10"), "cum": Decimal(0),
                     "avg": Decimal(0), "execs": [], "chain": [field(m, 11)], "status": "0"}
                self.orders[o["cl"]] = o
                self.report(sid, o, "0", "0")
                plan = field(m, 58) or ""
                if "FILL" in plan:
                    half = (o["qty"] / 2).quantize(Decimal("1"))
                    self.fill(sid, o, half, o["px"])
                    self.fill(sid, o, o["qty"] - half, o["px"] + Decimal("0.05"))
                    o["status"] = "2"
                elif "PART" in plan:
                    self.fill(sid, o, (o["qty"] / 4).quantize(Decimal("1")), o["px"])
                    o["status"] = "1"
                if "BUST" in plan and o["execs"]:
                    x = o["execs"][-1]
                    x["survives"] = False
                    o["cum"] -= Decimal(x["qty"])
                    st = "1" if o["cum"] > 0 else "0"
                    self.report(sid, o, st if self.v42 else "H", st, x["qty"], x["px"], ref=x["execId"], trans="1")
                    o["status"] = st
            elif t in ("F", "G"):
                o = self.orders.get(field(m, 41))
                if o is None or o["status"] in ("2", "4"):
                    r = fix.Message()
                    r.getHeader().setField(fix.MsgType("9"))
                    for tag, v in [(37, o["oid"] if o else "NONE"), (11, field(m, 11)), (41, field(m, 41)),
                                   (39, o["status"] if o else "8"), (434, "1" if t == "F" else "2")]:
                        r.setField(fix.StringField(tag, v))
                    fix.Session.sendToTarget(r, sid)
                    return
                new = field(m, 11)
                old = o["cl"]
                o["chain"].append(new)
                self.orders[new] = o
                o["cl"] = new
                if t == "F":
                    o["status"] = "4"
                    self.report(sid, o, "4", "4", orig=old)
                else:
                    o["qty"] = Decimal(field(m, 38))
                    self.report(sid, o, "5", "5" if self.v42 else o["status"], orig=old)


class Client(fix.Application):
    def __init__(self):
        super().__init__()
        self.logged_on = threading.Event()
        self.sid = None
        self.reports = 0

    def onCreate(self, sid): self.sid = sid
    def onLogon(self, sid): self.logged_on.set()
    def onLogout(self, sid): self.logged_on.clear()
    def toAdmin(self, m, sid): pass
    def fromAdmin(self, m, sid): pass
    def toApp(self, m, sid): pass
    def fromApp(self, m, sid): self.reports += 1


def settings(path, role, begin, spec, port, work, reset):
    dd = os.path.join(spec, "FIX42.xml" if begin == "FIX.4.2" else "FIX44.xml")
    v = begin[-3:].replace(".", "")
    me, peer = (f"BRK{v}", f"CLI{v}") if role == "acceptor" else (f"CLI{v}", f"BRK{v}")
    lines = ["[DEFAULT]", f"ConnectionType={role}", f"FileStorePath={work}/store-{role}",
             f"FileLogPath={work}/log-{role}", "StartTime=00:00:00", "EndTime=00:00:00",
             "UseDataDictionary=Y", f"DataDictionary={dd}", "ValidateUserDefinedFields=N",
             "HeartBtInt=1", "ReconnectInterval=1", f"ResetOnLogon={'Y' if reset else 'N'}",
             "[SESSION]", f"BeginString={begin}", f"SenderCompID={me}", f"TargetCompID={peer}"]
    lines += [f"SocketAcceptPort={port}"] if role == "acceptor" else [f"SocketConnectHost=127.0.0.1", f"SocketConnectPort={port}"]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return fix.SessionSettings(path)


def order(client, cl, sym, side, qty, px, plan):
    m = fix.Message()
    m.getHeader().setField(fix.MsgType("D"))
    for t, v in [(11, cl), (21, "1"), (55, sym), (54, side), (38, qty), (40, "2"), (44, px), (58, plan),
                 (60, time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())), (1, "ACC-" + sym)]:
        m.setField(fix.StringField(t, str(v)))
    fix.Session.sendToTarget(m, client.sid)


def amend(client, mtype, cl, orig, sym, side, qty, px):
    m = fix.Message()
    m.getHeader().setField(fix.MsgType(mtype))
    pairs = [(11, cl), (41, orig), (55, sym), (54, side), (38, qty), (60, time.strftime("%Y%m%d-%H:%M:%S", time.gmtime()))]
    if mtype == "G":
        pairs += [(21, "1"), (40, "2"), (44, px)]
    for t, v in pairs:
        m.setField(fix.StringField(t, str(v)))
    fix.Session.sendToTarget(m, client.sid)


def run(begin, spec, work, out):
    rng = random.Random(SEED + (42 if begin == "FIX.4.2" else 44))
    port = free_port()
    v42 = begin == "FIX.4.2"
    os.makedirs(work, exist_ok=True)
    broker, client = Broker(v42), Client()
    sa = settings(os.path.join(work, "acceptor.cfg"), "acceptor", begin, spec, port, work, False)
    si = settings(os.path.join(work, "initiator.cfg"), "initiator", begin, spec, port, work, False)
    acceptor = fix.SocketAcceptor(broker, fix.FileStoreFactory(sa), sa, fix.FileLogFactory(sa))
    initiator = fix.SocketInitiator(client, fix.FileStoreFactory(si), si, fix.FileLogFactory(si))
    acceptor.start()
    initiator.start()
    if not client.logged_on.wait(15):
        raise SystemExit("BLOCKED: the initiator did not log on within 15 s")
    sent = []
    syms = ["ACME", "ZETA", "OMNI"]
    for i in range(1, 13):
        sym, side = rng.choice(syms), rng.choice(["1", "2"])
        qty, px = rng.randint(1, 20) * 100, Decimal(rng.randint(1000, 9000)) / 100
        plan = rng.choice(["FILL", "FILL", "PART", "REST", "FILL BUST", "PART"])
        cl = f"C{begin[-1]}-{i}"
        order(client, cl, sym, side, qty, px, plan)
        sent.append({"cl": cl, "sym": sym, "side": side, "qty": qty, "px": str(px), "plan": plan})
        time.sleep(0.05)
        if plan == "REST":
            amend(client, "G", cl + "r", cl, sym, side, qty + 100, px)
            time.sleep(0.05)
            amend(client, "F", cl + "c", cl + "r", sym, side, qty + 100, px)
        elif plan == "PART" and rng.random() < 0.5:
            amend(client, "F", cl + "c", cl, sym, side, qty, px)
        elif plan == "FILL" and rng.random() < 0.3:
            amend(client, "F", cl + "c", cl, sym, side, qty, px)       # too late: CancelReject
        time.sleep(0.05)
    time.sleep(2.5)                                                     # a few heartbeats
    # A sequence gap made by the engine itself: the initiator skips three numbers, so the acceptor
    # asks for a resend and the initiator answers with a SequenceReset-GapFill.
    session = fix.Session.lookupSession(client.sid)
    session.logout()
    time.sleep(1.5)
    before = session.getExpectedSenderNum()
    session.setNextSenderMsgSeqNum(before + 3)
    session.logon()
    if not client.logged_on.wait(15):
        raise SystemExit("BLOCKED: the initiator did not log on again")
    time.sleep(1.5)
    order(client, f"C{begin[-1]}-13", "ACME", "1", 300, Decimal("12.34"), "FILL")
    sent.append({"cl": f"C{begin[-1]}-13", "sym": "ACME", "side": "1", "qty": 300, "px": "12.34", "plan": "FILL"})
    time.sleep(1.5)
    initiator.stop()
    acceptor.stop()
    time.sleep(0.5)

    v = begin[-3:].replace(".", "")
    logname = f"{begin}-BRK{v}-CLI{v}.messages.current.log"
    raw = open(os.path.join(work, "log-acceptor", logname), "rb").read()
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, f"engine-quickfix-{v}.log"), "wb") as f:
        f.write(raw)
    seen = {}
    for o in broker.orders.values():
        seen[id(o)] = o
    truth = {
        "engine": "quickfix 1.16.0 (PyPI), SocketInitiator + SocketAcceptor over 127.0.0.1",
        "begin": begin, "seed": SEED, "messagesInLog": raw.count(b"8=FIX"),
        "appMessagesFromClient": len(broker.app_in), "appMessagesFromBroker": len(broker.app_out),
        "adminMessagesAtBroker": len(broker.admin),
        "skippedSequenceNumbers": {"direction": f"CLI{v}>BRK{v}", "expected": before, "received": before + 3},
        "orders": [{"clOrdIds": o["chain"], "orderId": o["oid"], "symbol": o["sym"], "side": o["side"],
                    "finalOrdStatus": o["status"], "cum": str(o["cum"])} for o in seen.values()],
        "executions": broker.executions,
        "newOrdersSent": sent,
    }
    with open(os.path.join(out, f"engine-quickfix-{v}.truth.json"), "w") as f:
        json.dump(truth, f, indent=1)
    print(begin, "log bytes", len(raw), "messages", truth["messagesInLog"], "executions", len(broker.executions))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--begin", default="both")
    a = ap.parse_args()
    for b in (["FIX.4.2", "FIX.4.4"] if a.begin == "both" else [a.begin]):
        run(b, a.spec, os.path.join(a.work, b), a.out)
