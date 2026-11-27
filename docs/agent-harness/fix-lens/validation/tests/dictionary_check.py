#!/usr/bin/env python3
"""Cross-check the product's dictionaries against two independent sources.

    python3 -I tests/dictionary_check.py --product <fix-lens dir> --orchestra <dir> --quickfix <dir> --out reports/partial/dictionary.json

1. The Orchestra FIX 4.2 / 4.4 files at the commit the product pins (PRD TR-001), parsed here with
   xml.etree, independently of the product's build script: every field name, type and code must be equal.
2. QuickFIX's FIX42.xml / FIX44.xml, a separately maintained dictionary: tag -> field name and tag -> set of
   enumerated values. Differences are listed for a human to judge; they are not automatically defects.
The XML files are untrusted downloads: they are only parsed, never executed (run with python3 -I).
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser()
ap.add_argument("--product", required=True)
ap.add_argument("--orchestra", required=True)
ap.add_argument("--quickfix", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
NS = "{http://fixprotocol.io/2020/orchestra/repository}"
report = {"results": []}


def product(v):
    src = open(os.path.join(a.product, "src", "dictionary", f"fix{v}.js"), encoding="utf-8").read().strip()
    assert src.startswith("export default ") and src.endswith(";")
    return json.loads(src[len("export default "):-1])


def orchestra(v):
    root = ET.parse(os.path.join(a.orchestra, f"OrchestraFIX{v}.xml")).getroot()
    codesets = {}
    for cs in root.iter(NS + "codeSet"):
        codesets[cs.get("name")] = {c.get("value"): c.get("name") for c in cs.iter(NS + "code")}
    fields = {}
    for f in root.iter(NS + "field"):
        if f.get("id") is None:
            continue
        e = {"name": f.get("name"), "type": f.get("type")}
        if f.get("type") in codesets:
            e["enumValues"] = codesets[f.get("type")]
        fields[f.get("id")] = e
    return fields


def quickfix(v):
    root = ET.parse(os.path.join(a.quickfix, f"FIX{v}.xml")).getroot()
    out = {}
    for f in root.find("fields"):
        out[f.get("number")] = {"name": f.get("name"), "type": f.get("type"),
                                "values": sorted(x.get("enum") for x in f.findall("value"))}
    return out


for v in ("42", "44"):
    p, o, q = product(v)["fields"], orchestra(v), quickfix(v)
    diffs = []
    for tag in sorted(set(p) | set(o), key=int):
        if p.get(tag) != o.get(tag):
            diffs.append({"tag": tag, "product": p.get(tag), "orchestra": o.get(tag)})
    report["results"].append({"id": f"DICT-{v}-01", "feature": f"Dictionary equals the pinned Orchestra FIX {v[0]}.{v[1]} file (independent parse)",
                              "fields": len(p), "enumFields": sum(1 for x in p.values() if "enumValues" in x),
                              "status": "PASS" if not diffs else "FAIL", "differences": diffs[:20], "differenceCount": len(diffs)})
    names, missing, extra, enums = [], [], [], []
    for tag in sorted(set(p) | set(q), key=int):
        if tag not in p:
            missing.append({"tag": tag, "quickfix": q[tag]["name"]})
        elif tag not in q:
            extra.append({"tag": tag, "product": p[tag]["name"]})
        else:
            if p[tag]["name"] != q[tag]["name"]:
                names.append({"tag": tag, "product": p[tag]["name"], "quickfix": q[tag]["name"]})
            pv, qv = sorted(p[tag].get("enumValues", {})), q[tag]["values"]
            if pv != qv:
                enums.append({"tag": tag, "name": p[tag]["name"], "onlyProduct": sorted(set(pv) - set(qv)),
                              "onlyQuickfix": sorted(set(qv) - set(pv))})
    report["results"].append({"id": f"DICT-{v}-02", "feature": f"Dictionary compared with QuickFIX FIX{v}.xml (informative)",
                              "status": "INFO", "tagsOnlyInQuickfix": missing, "tagsOnlyInProduct": extra,
                              "nameDifferences": names, "enumDifferences": enums})
    print(f"FIX {v}: {len(p)} fields; vs Orchestra: {len(diffs)} differences; vs QuickFIX: {len(missing)} tags missing, "
          f"{len(extra)} extra, {len(names)} names differ, {len(enums)} enum sets differ")
os.makedirs(os.path.dirname(a.out), exist_ok=True)
json.dump(report, open(a.out, "w"), indent=1)
