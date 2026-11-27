#!/usr/bin/env python3
"""Exploratory and compatibility tests on external material (brief 3, 13). Not definitive: no full ground truth.

    FIX_LENS_DIR=<product> python3 -I tests/external_test.py --sources <dir prepared by sources/fetch.sh>

1. Public sample logs: every message is checked by this file's own wire validator (through generators/fixgen.py)
   and the verdict is compared with the tool's, message by message.
2. QuickFIX acceptance-test definitions (server side, FIX 4.2 and 4.4): each definition is turned into the
   two-way log it describes (BodyLength and CheckSum computed here where the definition leaves them to the
   test runner). The engine's own expected reaction, written in the definition, is compared with the tool's
   timeline: a ResendRequest from the engine means it saw a gap; a Logout "MsgSeqNum too low" means it saw
   a sequence number that had already been used.
The downloaded files are untrusted: they are read as text only (run with -I).
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "generators"))
from fixgen import SOH, validate_wire  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--sources", required=True)
a = ap.parse_args()
server = subprocess.Popen(["node", os.path.join(HERE, "tool_server.mjs")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8")
n = 0


def tool(text):
    global n
    n += 1
    server.stdin.write(json.dumps({"id": n, "text": text, "render": True}) + "\n")
    server.stdin.flush()
    out = json.loads(server.stdout.readline())
    assert out.get("threw") is None, out["threw"]
    return out


results = []
LOGS = [("log-analyzer/repo/sample_fix44.log", "|"), ("fix-log-analyzer/repo/sample_log.log", "|"),
        ("study-guide/repo/fix_log1.txt", SOH), ("fiximulator/repo/logs/FIX.4.2-FIXIMULATOR-BANZAI.messages.log", SOH)]
for rel, delim in LOGS:
    p = os.path.join(a.sources, rel)
    if not os.path.exists(p):
        results.append({"id": "EX-" + rel.split("/")[0], "feature": f"Public sample log {rel}", "status": "BLOCKED", "actual": "file not present"})
        continue
    text = open(p, encoding="utf-8", errors="replace", newline="").read()
    mine = []
    for line in text.splitlines():
        i = line.find("8=FIX")
        if i < 0:
            continue
        raw = line[i:].rstrip("\r\n").replace(delim, SOH) if delim != SOH else line[i:].rstrip("\r\n")
        mine.append(validate_wire(raw))
    out = tool(text)
    bad_numbers = {e["number"] for e in out["errors"]}
    verdicts = [(k + 1) not in bad_numbers for k in range(len(mine))]
    agree = len(mine) == out["stats"].get("messages") and all(v == m[0] for v, m in zip(verdicts, mine))
    results.append({"id": "EX-" + rel.split("/")[0], "feature": f"Public sample log {rel}: accept / reject verdict per message equals an independent wire check",
                    "version": "as found", "dataset": rel + " (external, not stored)", "status": "PASS" if agree else "FAIL",
                    "expected": {"messages": len(mine), "wireValid": sum(1 for m in mine if m[0])},
                    "actual": {"stats": out["stats"], "rules": sorted({e["rule"] for e in out["errors"]}),
                               "independentReasons": sorted({m[1] for m in mine if not m[0]})[:5]}})
    print(results[-1]["status"], results[-1]["id"], results[-1]["expected"], results[-1]["actual"])

# ---- QuickFIX acceptance definitions
summary = {"definitions": 0, "messages": 0, "resend_agree": 0, "resend_disagree": [], "too_low_defs": [], "too_low_flagged": 0,
           "verdict_agree": 0, "verdict_disagree": []}
for v in ("fix42", "fix44"):
    for path in sorted(glob.glob(os.path.join(a.sources, "quickfix/repo/test/definitions/server", v, "*.def"))):
        name = v + "/" + os.path.basename(path)
        lines, meta, clock = [], [], 0
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.rstrip("\r\n")
            if not (line[:1] in "IE" and line[1:6] == "8=FIX"):
                continue
            clock += 1
            body = line[1:].replace("<TIME>", f"20261127-10:00:{clock % 60:02d}").replace("00000000-00:00:00.000", f"20261127-10:00:{clock % 60:02d}.000")
            fields = body.rstrip(SOH).split(SOH)
            explicit_len = len(fields) > 1 and fields[1].startswith("9=")
            explicit_sum = fields[-1].startswith("10=") and line[0] == "I"
            if fields[-1].startswith("10="):
                trailer, fields = fields[-1], fields[:-1]
            else:
                trailer = None
            if not explicit_len or line[0] == "E":
                rest = [f for f in fields[1:] if not (f.startswith("9=") and f is fields[1])] if explicit_len else fields[1:]
                payload = "".join(f + SOH for f in rest)
                fields = [fields[0], f"9={len(payload.encode('utf-8'))}"] + rest
            head = "".join(f + SOH for f in fields)
            raw = head + (trailer if explicit_sum else f"10={sum(head.encode('utf-8')) % 256:03d}") + SOH
            lines.append(raw)
            meta.append({"side": line[0], "type": dict(f.split("=", 1) for f in fields if "=" in f).get("35"),
                         "text": dict(f.split("=", 1) for f in fields if "=" in f).get("58", "")})
        if not lines:
            continue
        summary["definitions"] += 1
        summary["messages"] += len(lines)
        out = tool("\n".join(lines) + "\n")
        bad = {e["number"] for e in out["errors"]}
        for k, raw in enumerate(lines):
            ok = validate_wire(raw)[0]
            if ok == ((k + 1) not in bad):
                summary["verdict_agree"] += 1
            else:
                summary["verdict_disagree"].append({"definition": name, "message": k + 1, "independent": ok, "raw": raw.replace(SOH, "|")[:140]})
        # gaps the tool reports on messages sent by the test driver (I lines)
        tool_gap = any(meta[g[0] - 1]["side"] == "I" for g in out["gaps"])
        engine_resend = any(m["side"] == "E" and m["type"] == "2" for m in meta)
        if tool_gap == engine_resend:
            summary["resend_agree"] += 1
        else:
            summary["resend_disagree"].append({"definition": name, "engineAsksResend": engine_resend, "toolReportsGap": tool_gap})
        if any(m["side"] == "E" and "MsgSeqNum too low" in m["text"] for m in meta):
            flagged = len(out["gaps"]) > 0
            summary["too_low_defs"].append({"definition": name, "toolShowsAnything": flagged})
            summary["too_low_flagged"] += flagged
print(json.dumps({k: (v if not isinstance(v, list) else v[:12]) for k, v in summary.items()}, indent=1))
results.append({"id": "EX-quickfix-defs-01", "feature": "QuickFIX acceptance definitions (FIX 4.2, 4.4): accept / reject verdict per message equals an independent wire check",
                "version": "FIX.4.2 + FIX.4.4", "dataset": "quickfix test/definitions/server/fix42, fix44 (external, not stored)",
                "status": "PASS" if not summary["verdict_disagree"] else "FAIL",
                "expected": f"{summary['messages']} messages of {summary['definitions']} definitions, same verdicts",
                "actual": {"agree": summary["verdict_agree"], "disagree": summary["verdict_disagree"][:5]}})
results.append({"id": "EX-quickfix-defs-02", "feature": "QuickFIX acceptance definitions: the tool reports a gap exactly where the engine is expected to send a ResendRequest",
                "version": "FIX.4.2 + FIX.4.4", "dataset": "quickfix test/definitions/server/fix42, fix44 (external, not stored)",
                "status": "INFO", "expected": "exploratory: disagreements are listed for a human to judge",
                "actual": {"agree": summary["resend_agree"], "disagree": summary["resend_disagree"]}})
results.append({"id": "EX-quickfix-defs-03", "feature": "QuickFIX acceptance definitions where the engine ends the session for 'MsgSeqNum too low': does the tool show anything",
                "version": "FIX.4.2 + FIX.4.4", "dataset": "quickfix test/definitions/server/fix42, fix44 (external, not stored)",
                "status": "INFO", "expected": "exploratory evidence for defect FL-07",
                "actual": {"definitions": summary["too_low_defs"], "flaggedByTool": summary["too_low_flagged"]}})
server.stdin.close()
os.makedirs(os.path.join(ROOT, "reports", "partial"), exist_ok=True)
json.dump(results, open(os.path.join(ROOT, "reports", "partial", "external.json"), "w"), indent=1)
