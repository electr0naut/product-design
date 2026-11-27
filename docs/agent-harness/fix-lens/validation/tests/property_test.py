#!/usr/bin/env python3
"""Property-based and differential tests (brief 14). Hypothesis drives the tool through tests/tool_server.mjs.

    FIX_LENS_DIR=<product> python tests/property_test.py [--quickfix-spec <dir with FIX42.xml, FIX44.xml>]

Needs `hypothesis`; the QuickFIX differential also needs the `quickfix` package and is recorded as BLOCKED without it.
Every expectation is computed here, from the FIX wire rules and PRD TR-002, not by the tool.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "generators"))
from hypothesis import HealthCheck, given, seed, settings, strategies as st  # noqa: E402

from build import ACCOUNTS, MULTI, SYMBOLS, market  # noqa: E402
from fixgen import SOH, encode, validate_wire  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--quickfix-spec")
ap.add_argument("--examples", type=int, default=300)
args = ap.parse_args()

server = subprocess.Popen(["node", os.path.join(HERE, "tool_server.mjs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8")
counter = 0
slowest = 0.0


def tool(text, render=False):
    global counter, slowest
    counter += 1
    server.stdin.write(json.dumps({"id": counter, "text": text, "render": render}) + "\n")
    server.stdin.flush()
    out = json.loads(server.stdout.readline())
    assert out["id"] == counter
    assert out.get("threw") is None, out["threw"]
    slowest = max(slowest, out["ms"])
    return out


results = []


def run(pid, feature, fn, version="FIX.4.2 + FIX.4.4"):
    try:
        info = fn()
        results.append({"id": pid, "feature": feature, "version": version, "status": "PASS", "actual": info or "property held"})
        print("PASS", pid, feature, "-", info or "")
    except AssertionError as e:
        results.append({"id": pid, "feature": feature, "version": version, "status": "FAIL", "actual": str(e)[:1500]})
        print("FAIL", pid, feature, "\n     ", str(e)[:1500])
    except Exception as e:  # a falsifying example reported by Hypothesis
        results.append({"id": pid, "feature": feature, "version": version, "status": "FAIL", "actual": repr(e)[:1500]})
        print("FAIL", pid, feature, "\n     ", repr(e)[:1500])


BEGIN = st.sampled_from(["FIX.4.2", "FIX.4.4"])
TAG = st.integers(min_value=1, max_value=99999).filter(lambda t: t not in (8, 9, 10))
PLAIN = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=24)
WIDE = st.text(alphabet=st.characters(blacklist_characters="\x01\n\r", blacklist_categories=("Cs",)), max_size=24)
SETTINGS = dict(max_examples=args.examples, deadline=None, suppress_health_check=list(HealthCheck), database=None)


def message(begin, mtype, fields):
    return encode(begin, [(35, mtype)] + fields)


# P1: any well-formed SOH message is accepted and its fields come back unchanged, in order
def p1():
    @seed(1)
    @settings(**SETTINGS)
    @given(BEGIN, st.sampled_from(["0", "D", "8", "AE", "U1"]), st.lists(st.tuples(TAG, WIDE), max_size=30))
    def prop(begin, mtype, fields):
        raw = message(begin, mtype, fields)
        assert validate_wire(raw)[0]
        out = tool(raw + "\n")
        assert out["errors"] == [], (raw, out["errors"])
        got = out["messages"][0]["fields"]
        want = [[8, begin], [9, raw.split(SOH)[1][2:]], [35, mtype]] + [[t, v] for t, v in fields] + [[10, raw[-4:-1]]]
        assert got == want, (raw, got)
    prop()
    return f"{args.examples} random messages, values over all of Unicode except SOH and line ends"


# P2: text delimiter forms follow TR-002: a delimiter inside a value is literal unless digits and '=' follow it
def p2():
    forms = {"pipe": "|", "caret": "^A", "angle": "<SOH>"}
    stats = {"valid": 0, "ambiguous": 0}

    @seed(2)
    @settings(**SETTINGS)
    @given(BEGIN, st.sampled_from(sorted(forms)), st.lists(st.tuples(TAG, st.one_of(
        st.text(alphabet="ab 1=|^A<SOH>.", max_size=14),
        st.sampled_from(["x|44=1", "x^A44=1", "x<SOH>44=1", "|1=", "^A7=", "<SOH>10=123", "a|b", "a^Ab", "a<SOH>b", "||", "^A^A", "end|"]))),
        min_size=1, max_size=8))
    def prop(begin, form, fields):
        d = forms[form]
        raw = message(begin, "D", fields)                 # bytes and CheckSum of the SOH wire form (TR-002 byte counts)
        text = raw.replace(SOH, d) + "\n"
        ambiguous = any(re.search(re.escape(d) + r"[0-9]+=", v) for _, v in fields)
        out = tool(text)
        if ambiguous:
            stats["ambiguous"] += 1
            assert len(out["errors"]) >= 1, ("expected a reported error for the case text cannot settle", text)
        else:
            stats["valid"] += 1
            assert out["errors"] == [], (text, out["errors"])
            got = [f for f in out["messages"][0]["fields"] if f[0] not in (8, 9, 10, 35)]
            assert got == [[t, v] for t, v in fields], (text, got)
    prop()
    return f"{stats['valid']} messages with literal delimiters read back exactly; {stats['ambiguous']} ambiguous ones reported as errors"


# P3: one changed character in the body is always caught, and the neighbours are untouched
def p3():
    @seed(3)
    @settings(**SETTINGS)
    @given(BEGIN, st.lists(st.tuples(TAG, PLAIN), min_size=1, max_size=12), st.data())
    def prop(begin, fields, data):
        good = message(begin, "0", [(49, "A"), (56, "B"), (34, 1)])
        raw = message(begin, "D", fields)
        lo = raw.index(SOH, raw.index(SOH) + 1) + 1          # first character after field 9
        hi = raw.rindex("10=")
        i = data.draw(st.integers(lo, hi - 1))
        if raw[i] == SOH:
            return
        c = data.draw(st.characters(min_codepoint=33, max_codepoint=126).filter(lambda ch: ch != raw[i]))
        bad = raw[:i] + c + raw[i + 1:]
        out = tool(good + "\n" + bad + "\n" + good + "\n")
        assert [m["number"] for m in out["messages"]] == [1, 3], (bad, out)
        assert [e["number"] for e in out["errors"]] == [2], (bad, out)
    prop()
    return f"{args.examples} single-character corruptions, each reported as message 2 with messages 1 and 3 intact"


# P4: arbitrary text never throws, and every candidate is either a message or an error
def p4():
    @seed(4)
    @settings(**SETTINGS)
    @given(st.lists(st.one_of(st.text(max_size=60), st.sampled_from(["8=FIX", "8=FIX.4.4", SOH, "|", "^A", "<SOH>", "10=123", "9=5", "35=D", "\n", "\r\n", "=", "10="])), max_size=40))
    def prop(parts):
        text = "".join(parts)
        out = tool(text)
        numbers = sorted([m["number"] for m in out["messages"]] + [e["number"] for e in out["errors"]])
        assert numbers == list(range(1, len(numbers) + 1)), (text, numbers)
    prop()
    return f"{args.examples} hostile texts; slowest answer so far {slowest:.1f} ms"


# P5: the result for two logs joined is the two results joined
def p5():
    rng = random.Random(5)
    sim = market(5005, MULTI[:2], 12)
    lines = [e["raw"] for e in sim.entries]
    for _ in range(40):
        k = rng.randint(1, len(lines) - 1)
        a, b = "\n".join(lines[:k]) + "\n", "\n".join(lines[k:]) + "\n"
        whole, ra, rb = tool(a + b), tool(a), tool(b)
        joined = [m["fields"] for m in ra["messages"]] + [m["fields"] for m in rb["messages"]]
        assert [m["fields"] for m in whole["messages"]] == joined
    return "40 split points of a 2-session log"


# P6: randomised valid order lifecycles against the generator's decimal ground truth
def p6():
    n = 0
    for sd in range(9000, 9040):
        sim = market(sd, MULTI if sd % 2 else MULTI[:1], 25)
        truth = sim.truth()
        out = tool(sim.text(), render=True)
        assert out["errors"] == [], sd
        assert out["events"] == truth["events"], f"seed {sd}: timeline differs"
        assert out["gaps"] == [[g["number"], g["expected"], g["received"]] for g in truth["gaps"]], f"seed {sd}: gaps"
        assert out["groups"] == [o["numbers"] for o in truth["orders"]], f"seed {sd}: order groups"
        for sym, want in truth["trades"].items():
            got = out["trades"].get(sym)
            assert got, f"seed {sd}: no row for {sym}"
            for k in ("buyOrders", "bought", "avgBuy", "sellOrders", "sold", "avgSell", "net"):
                assert got[k] in (want[k] if isinstance(want[k], list) else [want[k]]), f"seed {sd} {sym}.{k}: shown {got[k]}, expected {want[k]} (exact {want['exact']})"
        n += truth["messages"]
    return f"40 seeds, {n} messages, every timeline, gap, order group and trading figure equal to ground truth"


# P7: weighted average prices of random fills, against decimal arithmetic (rounding to 4 places)
def p7():
    from decimal import Decimal as D, ROUND_HALF_EVEN, ROUND_HALF_UP
    rng = random.Random(7)
    wrong, ties, n = [], 0, 3000
    for i in range(n):
        k = rng.randint(1, 4)
        fills = [(D(rng.randint(1, 5000)) / rng.choice([1, 10, 100]), D(rng.randint(1, 2000000)) / rng.choice([100, 1000, 10000])) for _ in range(k)]
        body = lambda j, q, p: [(35, "8"), (49, "B"), (56, "A"), (34, j + 1), (37, "O1"), (11, "C1"), (17, f"E{j}"), (150, "F"), (39, 1), (55, "ACME"), (54, 1), (32, format(q, "f")), (31, format(p, "f")), (151, 0), (14, 0), (6, 0)]
        text = "\n".join(encode("FIX.4.4", body(j, q, p)) for j, (q, p) in enumerate(fills)) + "\n"
        qty = sum(q for q, _ in fills)
        avg = sum(q * p for q, p in fills) / qty
        norm = lambda d: (format(d.normalize(), "f") if d != d.to_integral() else format(d.quantize(D(1)), "f"))
        ok = {norm(avg.quantize(D("0.0001"), rounding=m)) for m in (ROUND_HALF_UP, ROUND_HALF_EVEN)}
        ties += len(ok) > 1
        got = tool(text, render=True)["trades"]["ACME"]
        if got["avgBuy"] not in ok or got["bought"] not in {norm(qty.quantize(D("0.0001"), rounding=m)) for m in (ROUND_HALF_UP, ROUND_HALF_EVEN)}:
            wrong.append({"fills": [(str(q), str(p)) for q, p in fills], "exactAvg": str(avg), "expected": sorted(ok), "shownAvg": got["avgBuy"], "shownBought": got["bought"], "exactBought": str(qty)})
    assert not wrong, f"{len(wrong)} of {n} random fill sets shown with a wrong 4-place figure; first: {json.dumps(wrong[:3])}"
    return f"{n} random fill sets, all averages equal to the decimal value at 4 places ({ties} exact ties accepted either way)"


# D1: differential against the QuickFIX parser: same accept / reject verdict on valid and damaged messages
def d1():
    import quickfix as fix
    rng = random.Random(11)
    sim = market(1111, MULTI[:2], 30)
    raws = [e["raw"] for e in sim.entries]
    disagreements, n = [], 0
    kinds = {}
    for raw in raws:
        variants = {"valid": raw}
        f = raw.split(SOH)
        variants["BodyLength+1"] = raw.replace(f[1], f"9={int(f[1][2:]) + 1}", 1)
        variants["CheckSum+1"] = raw[:-4] + f"{(int(raw[-4:-1]) + 1) % 256:03d}" + SOH
        i = rng.randrange(len(f[0]) + len(f[1]) + 2, len(raw) - 8)
        if raw[i] != SOH:
            variants["one character changed"] = raw[:i] + ("Z" if raw[i] != "Z" else "Y") + raw[i + 1:]
        variants["no trailer"] = raw[:raw.rindex("10=")]
        variants["9 and 35 swapped"] = SOH.join([f[0], f[2], f[1]] + f[3:])
        for kind, text in variants.items():
            n += 1
            try:
                fix.Message(text, True)
                qf = True
            except Exception:
                qf = False
            out = tool(text + "\n")
            lens = len(out["messages"]) == 1 and not out["errors"]
            kinds.setdefault(kind, [0, 0])[0 if qf == lens else 1] += 1
            if qf != lens:
                disagreements.append({"kind": kind, "quickfix": qf, "fixlens": lens, "message": text.replace(SOH, "|")[:160]})
    results.append({"id": "D1-detail", "feature": "QuickFIX differential: verdicts by kind of damage (agree, disagree)", "version": "FIX.4.2 + FIX.4.4", "status": "INFO", "actual": kinds})
    assert not disagreements, f"{len(disagreements)} of {n} verdicts differ; by kind {kinds}; first: {json.dumps(disagreements[:2])}"
    return f"{n} messages (valid and damaged five ways): QuickFIX {fix.__name__} and FIX Lens agree on every accept / reject verdict"


run("PB-01", "Property: a well-formed SOH message is accepted and read back field for field", p1)
run("PB-02", "Property: text delimiter forms follow TR-002 (literal delimiter in a value; the ambiguous case is an error)", p2)
run("PB-03", "Property: one changed character is always reported, neighbours intact", p3)
run("PB-04", "Property: arbitrary hostile text never throws; message numbers are consecutive", p4)
run("PB-05", "Property: decoding two logs joined equals the two decodes joined", p5)
run("PB-06", "Randomised valid order lifecycles (40 seeds) against decimal ground truth", p6)
run("PB-07", "Weighted average price of random fills against decimal arithmetic", p7, "FIX.4.4")
try:
    import quickfix  # noqa: F401
    run("DF-01", "Differential: accept / reject verdicts equal QuickFIX's parser", d1)
except ImportError:
    results.append({"id": "DF-01", "feature": "Differential: accept / reject verdicts equal QuickFIX's parser", "version": "FIX.4.2 + FIX.4.4",
                    "status": "BLOCKED", "actual": "the quickfix package is not installed in this Python"})
    print("BLOCKED DF-01 quickfix not importable")
server.stdin.close()
os.makedirs(os.path.join(ROOT, "reports", "partial"), exist_ok=True)
json.dump(results, open(os.path.join(ROOT, "reports", "partial", "property.json"), "w"), indent=1)
print(f"slowest single answer: {slowest:.1f} ms")
