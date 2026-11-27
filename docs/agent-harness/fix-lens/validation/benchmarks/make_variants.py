#!/usr/bin/env python3
"""Variants of the 1,000-message mix for the benchmarks: more sessions, malformed messages, the byte limit.

    python3 benchmarks/make_variants.py <perf dir>      (after generators/build.py --perf <perf dir>)
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "generators"))
from build import perf_market  # noqa: E402
from fixgen import SOH, encode  # noqa: E402

out = sys.argv[1]


def put(name, text):
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(name, len(text.encode()), "bytes")


for sessions in (1, 20, 50):
    put(f"sessions-{sessions:02d}-1000.log", perf_market(7300 + sessions, 1000, sessions).text())
base = open(os.path.join(out, "mix-1000.log"), encoding="utf-8").read().split("\n")[:-1]
rng = random.Random(77)
for share in (10, 50, 100):
    lines = []
    for line in base:
        if rng.randrange(100) < share:                       # break the CheckSum of this message
            line = line[:-4] + f"{(int(line[-4:-1]) + 7) % 256:03d}" + SOH
        lines.append(line)
    put(f"malformed-{share:03d}pct-1000.log", "\n".join(lines) + "\n")
# the byte limit: 999 messages padded to exactly 1,048,575 / 1,048,576 / 1,048,577 bytes
text = "\n".join(base[:999]) + "\n"
for target in (1048575, 1048576, 1048577):
    room = target - len(text.encode())
    head = [(35, "0"), (49, "PAD"), (56, "PAD"), (34, 1), (52, "20261127-09:00:00.000")]
    n = room - len(encode("FIX.4.4", head + [(58, "")]) + "\n")
    while True:                                              # BodyLength digits change with the padding
        m = encode("FIX.4.4", head + [(58, "P" * n)]) + "\n"
        if len(m) == room:
            break
        n += room - len(m)
    put(f"bytes-{target}.log", text + m)
chain = [encode("FIX.4.4", [(35, "G"), (49, "A"), (56, "B"), (34, i + 1), (11, f"C{i + 1}"), (41, f"C{i}"), (55, "ACME"), (54, 1), (38, 100)]) for i in range(10000)]
put("chain-10000.log", "\n".join(chain) + "\n")
