#!/usr/bin/env python3
"""Write every dataset and its ground truth. Deterministic: fixed seeds, no clock, no network.

    python3 generators/build.py                 # datasets/ and ground-truth/ (small, stored)
    python3 generators/build.py --perf DIR      # the performance datasets, written to DIR (not stored)
"""
import argparse
import hashlib
import json
import os
import sys
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cases  # noqa: E402
from fixgen import SOH, Sim, plain, shown, validate_wire  # noqa: E402

SYMBOLS = [("ACME", D("0.01"), D(100)), ("ZETA", D("0.0001"), D("0.5")), ("OMNI", D("0.05"), D(1)),
           ("KRONE", D("0.001"), D(10))]
ACCOUNTS = ["ACC-ALPHA", "ACC-BETA", "ACC-GAMMA", None]
DASH = "–"


def rows(order_sides, execs):
    """Trading summary rows from (symbol, side) of each order and (symbol, side, qty, px) of each execution."""
    table = {}

    def side(sym, s):
        r = table.setdefault(sym, {"buy": [0, D(0), D(0)], "sell": [0, D(0), D(0)]})
        return r[s]

    for sym, s in order_sides:
        side(sym, s)[0] += 1
    for sym, s, q, p in execs:
        x = side(sym, s)
        x[1] += q
        x[2] += q * p
    out = {}
    for sym in sorted(table):
        b, s = table[sym]["buy"], table[sym]["sell"]
        net = b[1] - s[1]
        out[sym] = {"buyOrders": str(b[0]), "bought": shown(b[1]), "avgBuy": shown(b[2] / b[1]) if b[1] else [DASH],
                    "sellOrders": str(s[0]), "sold": shown(s[1]), "avgSell": shown(s[2] / s[1]) if s[1] else [DASH],
                    "net": [("+" if net > 0 else "") + v for v in shown(net)]}
    return out


def views(sim, truth):
    """What the Account and SenderCompID filters must show, from the generator's own records."""
    out = []
    ents = sim.entries
    for acct in sorted({o["account"] for o in sim.orders if o["account"]}):
        mine = [o for o in sim.orders if o["account"] == acct]
        numbers = sorted(ents[i]["number"] for o in mine for i in o["entries"])
        execs = [(x["sym"], "buy" if x["side"] == "1" else "sell", x["qty"], x["px"]) for o in mine for x in o["execs"] if x["alive"]]
        out.append({"filters": {"account": acct}, "shown": numbers, "orders": len(mine),
                    "trades": rows([(o["sym"], "buy" if o["side"] == "1" else "sell") for o in mine], execs)})
    for comp in sorted({e["sender"] for e in ents}):
        numbers = [e["number"] for e in ents if e["sender"] == comp]
        seen = set(numbers)
        news = [(o["sym"], "buy" if o["side"] == "1" else "sell") for o in sim.orders
                if ents[o["entries"][0]]["number"] in seen]
        execs = [(x["sym"], "buy" if x["side"] == "1" else "sell", x["qty"], x["px"]) for o in sim.orders
                 for x in o["execs"] if x["alive"] and ents[x["entry"]]["number"] in seen]
        gaps = sum(1 for g in truth["gaps"] if g["number"] in seen)
        out.append({"filters": {"senderCompId": comp}, "shown": numbers, "gaps": gaps, "trades": rows(news, execs)})
    return out


def market(seed, sessions, orders, unique_ids=True, reset_some=True):
    sim = Sim(seed, unique_ids=unique_ids)
    for spec in sessions:
        sim.session(*spec)
    for i, s in enumerate(sim.sessions):
        sim.logon(s, reset=reset_some and i % 2 == 0)
    flows = [sim.life(sim.rng.choice(sim.sessions), SYMBOLS, ACCOUNTS) for _ in range(orders)]
    third = max(1, len(flows) // 3)
    sim.run(flows[:third])
    sim.lose_and_recover(sim.sessions[0], False, gapfill=True)
    sim.test_request(sim.sessions[-1], True)
    sim.run(flows[third:2 * third])
    if len(sim.sessions) > 1:
        s = sim.sessions[1]
        sim.logout(s)
        sim.logon(s, reset=True)          # a reset on one session while the others go on
    sim.lose_and_recover(sim.sessions[-1], True, gapfill=False)
    sim.run(flows[2 * third:])
    for s in sim.sessions:
        sim.logout(s)
    return sim


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dataset(name, folder, sim, description):
    for e in sim.entries:
        ok, why, _ = validate_wire(e["raw"])
        assert ok, (name, why)
    truth = sim.truth()
    text = sim.text()
    sha = write(os.path.join(ROOT, "datasets", folder, name + ".log"), text)
    truth.update({"dataset": f"datasets/{folder}/{name}.log", "sha256": sha, "description": description,
                  "bytes": len(text.encode("utf-8")), "views": views(sim, truth),
                  "intentionallyInvalid": [], "anomalies": [f"sequence gap at message {g['number']}" for g in truth["gaps"]]})
    with open(os.path.join(ROOT, "ground-truth", name + ".json"), "w") as f:
        json.dump(truth, f, indent=1, ensure_ascii=False)
    return truth


MULTI = [("FIX.4.4", "CLIENTA", "BROKERX"), ("FIX.4.2", "CLIENTB", "BROKERX"), ("FIX.4.4", "CLIENTA", "BROKERY"),
         ("FIX.4.2", "CLIENTC", "BROKERY"), ("FIX.4.4", "CLIENTD", "BROKERY", "DESK1", "GW2")]


def perf_market(seed, n_messages, n_sessions=5, pool=None):
    """A realistic mix cut to exactly n messages (logons first, order flows after)."""
    specs = [(("FIX.4.4" if i % 2 == 0 else "FIX.4.2"), f"CLIENT{i:02d}", f"BROKER{i % 3}") for i in range(n_sessions)]
    sim = Sim(seed)
    for spec in specs:
        sim.session(*spec)
    for s in sim.sessions:
        sim.logon(s, reset=True)
    live = []
    while len(sim.entries) < n_messages - 2:
        while len(live) < 3 * n_sessions:          # a steady number of orders in flight
            live.append(sim.life(sim.rng.choice(sim.sessions), SYMBOLS, ACCOUNTS))
        f = sim.rng.choice(live)
        try:
            next(f)
        except StopIteration:
            live.remove(f)
        if sim.rng.random() < 0.05 and len(sim.entries) < n_messages - 2:
            sim.heartbeat(sim.rng.choice(sim.sessions), sim.rng.random() < 0.5)
    while len(sim.entries) < n_messages:           # pad to the exact count with heartbeats
        sim.heartbeat(sim.sessions[0], True)
    return sim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perf")
    ap.add_argument("--perf-sizes", default="100,250,500,999,1000,1001,2500,5000,10000")
    ap.add_argument("--perf-sessions", type=int, default=5)
    a = ap.parse_args()
    if a.perf:
        os.makedirs(a.perf, exist_ok=True)
        index = []
        for n in [int(x) for x in a.perf_sizes.split(",")]:
            sim = perf_market(7000 + n, n, a.perf_sessions)
            text = sim.text()
            path = os.path.join(a.perf, f"mix-{n}.log")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            kinds = {}
            for e in sim.entries:
                kinds[e["type"]] = kinds.get(e["type"], 0) + 1
            index.append({"file": f"mix-{n}.log", "seed": 7000 + n, "messages": n, "bytes": len(text.encode()),
                          "sessions": len(sim.sessions), "orders": len({e["order"] for e in sim.entries if e["order"] is not None}),
                          "msgTypes": kinds, "sha256": hashlib.sha256(text.encode()).hexdigest()})
        with open(os.path.join(a.perf, "index.json"), "w") as f:
            json.dump(index, f, indent=1)
        print(f"wrote {len(index)} performance datasets to {a.perf}")
        return

    summary = []
    t = dataset("lifecycle-42", "FIX42", market(4201, [("FIX.4.2", "CLIENTB", "BROKERX")], 45),
                "One FIX 4.2 session, 45 orders with every lifecycle path, two lost messages, resends")
    summary.append(t)
    t = dataset("lifecycle-44", "FIX44", market(4401, [("FIX.4.4", "CLIENTA", "BROKERX")], 45),
                "One FIX 4.4 session, 45 orders with every lifecycle path, two lost messages, resends")
    summary.append(t)
    t = dataset("mixed-sessions", "multi-session", market(1101, MULTI, 110),
                "Five sessions (FIX 4.2 and 4.4, two brokers, SubIDs on one), 110 interleaved orders, a reset on one session")
    summary.append(t)
    sim = perf_market(7100, 100)
    t = dataset("mix-100", "performance", sim, "100-message mix; the larger performance sets are regenerated with --perf")
    summary.append(t)

    index = []
    for c in cases.CASES:
        path = f"datasets/{c['folder']}/{c['id']}.log"
        sha = write(os.path.join(ROOT, path), c["text"])
        index.append({k: c[k] for k in ("id", "feature", "version", "kind", "basis", "expect", "view", "note")}
                     | {"dataset": path, "sha256": sha, "bytes": len(c["text"].encode("utf-8")),
                        "intentionallyInvalid": c["folder"] == "malformed"})
    with open(os.path.join(ROOT, "ground-truth", "cases.json"), "w") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    with open(os.path.join(ROOT, "ground-truth", "manifest.json"), "w") as f:
        json.dump({"generator": "generators/build.py", "python": sys.version.split()[0],
                   "simulated": [{k: t[k] for k in ("dataset", "sha256", "seed", "description", "bytes", "messages", "valid",
                                                    "invalid", "directions", "orderCount", "rejections", "cancellations")}
                                 | {"gaps": len(t["gaps"]), "retransmissions": len(t["retransmissions"]),
                                    "resets": len(t["resets"]), "executions": len(t["executions"]),
                                    "groundTruth": "ground-truth/" + os.path.basename(t["dataset"])[:-4] + ".json"}
                                 for t in summary],
                   "cases": {"file": "ground-truth/cases.json", "count": len(index),
                             "intentionallyInvalid": [c["id"] for c in index if c["intentionallyInvalid"]]}}, f, indent=1)
    engine = []
    for v, folder in (("42", "FIX42"), ("44", "FIX44")):
        tp = os.path.join(ROOT, "ground-truth", f"engine-quickfix-{v}.truth.json")
        if not os.path.exists(tp):
            continue
        t = json.load(open(tp))
        side = {"1": "buy", "2": "sell"}
        t["trades"] = rows([(o["symbol"], side[o["side"]]) for o in t["orders"]],
                           [(x["symbol"], side[x["side"]], D(x["qty"]), D(x["px"])) for x in t["executions"] if x["survives"]])
        t["dataset"] = f"datasets/{folder}/engine-quickfix-{v}.log"
        t["sha256"] = hashlib.sha256(open(os.path.join(ROOT, t["dataset"]), "rb").read()).hexdigest()
        json.dump(t, open(tp, "w"), indent=1, ensure_ascii=False)
        engine.append({"dataset": t["dataset"], "sha256": t["sha256"], "groundTruth": f"ground-truth/engine-quickfix-{v}.truth.json",
                       "messages": t["messagesInLog"], "note": "written by a QuickFIX initiator/acceptor pair; not regenerated byte for byte (wall-clock timestamps)"})
    m = json.load(open(os.path.join(ROOT, "ground-truth", "manifest.json")))
    m["engine"] = engine
    json.dump(m, open(os.path.join(ROOT, "ground-truth", "manifest.json"), "w"), indent=1)
    for t in summary:
        print(t["dataset"], t["messages"], "messages,", t["orderCount"], "orders,", len(t["executions"]), "executions,",
              len(t["gaps"]), "gaps,", t["bytes"], "bytes")
    print(len(index), "hand-built cases")


if __name__ == "__main__":
    main()
