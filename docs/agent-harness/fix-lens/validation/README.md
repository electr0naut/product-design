# FIX Lens: independent validation and stress test

Done on 2026-11-27 against FIX Lens v1.2 (a read-only rebuild of the trusted main at `6f2f554`), to the scoped
brief in `BRIEF.md`. Nothing in the product was changed. Start with `reports/executive-summary.md`.

## Result in one paragraph

On logs of one session, everything the tool shows was right: 242 automated tests ran, 203 passed, and across
about 9,500 generated and engine-written messages every event, sequence gap, order group and trading figure
matched an independent decimal ground truth, apart from one rounding case. The 30 failures come from 16 defects.
Two are critical (P0) and concern logs that hold several sessions: fills and orders of different counterparties
that happen to share an identifier are merged, so bought and sold quantities and the Account filter can be
wrong without any warning. **Verdict: NOT PRODUCTION READY** until those two are fixed; see
`reports/final-assessment.md` for the conditions under which it can be used meanwhile.

## What is here

| Path | What it holds |
|---|---|
| `BRIEF.md`, `BRIEF-original.md` | the scoped brief this work follows, and the owner's original |
| `environment.json` | product commit, hardware, OS, runtimes, dependency versions, baseline |
| `sources/manifest.json`, `sources/fetch.sh` | every external source: URL, commit, licence, date, SHA-256, what it was used for; the download script |
| `dictionaries/README.md` | which dictionaries were used and what was checked with them (no third-party file is stored) |
| `generators/fixgen.py` | the independent FIX encoder, wire validator and market simulator (decimal arithmetic, seeded) |
| `generators/cases.py` | 106 hand-built cases, each with its expected reading and the clause it rests on |
| `generators/build.py` | writes `datasets/`, `ground-truth/` and `reproductions/`; `--perf DIR` writes the performance sets |
| `generators/engine_quickfix.py` | a real QuickFIX initiator and acceptor over loopback: the second, independent source of traffic |
| `datasets/` | `FIX42/`, `FIX44/`, `multi-session/`, `malformed/`, `performance/`: 112 small logs (0.95 MB) |
| `ground-truth/` | `manifest.json` (seeds, counts, which files are intentionally invalid), one truth file per simulated or engine dataset, `cases.json` for the hand-built cases |
| `tests/` | the runners: cases, datasets and format equivalence, properties and QuickFIX differential, dictionaries, external material, the page in Chromium; `report.mjs` builds the reports |
| `reproductions/` | one or more minimal logs per defect, and `repro.mjs` |
| `benchmarks/` | Node benchmarks of the logic modules, and the variants generator |
| `reports/` | `executive-summary.md`, `architecture-assessment.md`, `test-matrix.md`, `defects.md`, `final-assessment.md`, `results.json`, `benchmark-results.csv`, and `partial/` (the raw output of each runner) |

## How to run it again

Needs Node 22, Python 3.13, and for the full run: git, curl, a C++ compiler (pip builds `quickfix`), and
Playwright with Chromium resolvable by `node`. The product folder is only read.

```
export FIX_LENS_DIR=/path/to/fix-lens          # the folder with index.html and src/
export WORK=/path/to/an/empty/scratch/folder   # downloads, the engine build, large datasets: not in the repository

bash tests/run_all.sh quick     # about 2 minutes: datasets, 106 cases, 88 dataset checks, reports
bash tests/run_all.sh           # about 15 minutes plus a one-off 7-minute build of the QuickFIX package
```

Single steps:

```
python3 generators/build.py                              # datasets/, ground-truth/, reproductions/ (seeds are fixed)
node tests/run_cases.mjs [S07-08]                        # all hand-built cases, or the ones whose id starts so
node tests/run_datasets.mjs                              # simulated + engine datasets, 16 representations each
node reproductions/repro.mjs [FL-01]                     # one defect, or all: expected against actual
bash sources/fetch.sh $WORK/src                          # external material, at the recorded commits
python3 -I tests/dictionary_check.py --product $FIX_LENS_DIR --orchestra $WORK/src/orchestra --quickfix $WORK/src/quickfix/repo/spec --out reports/partial/dictionary.json
python3 -I tests/external_test.py --sources $WORK/src    # public sample logs, QuickFIX acceptance definitions
$WORK/venv/bin/python tests/property_test.py             # Hypothesis properties, QuickFIX differential
$WORK/venv/bin/python generators/engine_quickfix.py --spec $WORK/src/quickfix/repo/spec --work $WORK/engine --out $WORK/engine-out
python3 generators/build.py --perf $WORK/perf && python3 benchmarks/make_variants.py $WORK/perf
node benchmarks/bench_node.mjs --perf $WORK/perf --lifted $WORK/fix-lens-nolimit --out reports/partial/bench-node.json
node tests/browser_test.cjs --perf $WORK/perf --lifted $WORK/fix-lens-nolimit
node tests/report.mjs                                    # results.json, test-matrix.md, benchmark-results.csv
```

Notes:

- The two engine logs in `datasets/` are stored as the engine wrote them. A new engine run gives the same
  conversation with other timestamps, so it is not byte-for-byte reproducible; everything else is.
- `tests/harness.mjs` loads the product's `render.js` under jsdom (the product's own copy, default options, so
  no script runs) to read figures exactly as the page formats them. The same figures were checked in real
  Chromium for the largest dataset (test BR-05).
- No expectation in this folder was taken from the tool's output, from its tests, or from the project's hidden
  acceptance tests, which were not read.
