#!/usr/bin/env bash
# Runs the whole validation and rebuilds reports/results.json, reports/test-matrix.md and reports/benchmark-results.csv.
#   FIX_LENS_DIR=<product folder> WORK=<empty scratch folder> bash tests/run_all.sh [quick]
# "quick" skips the downloads, the engine, the browser and the benchmarks (about 2 minutes instead of about 15).
set -uo pipefail
cd "$(dirname "$0")/.."
: "${FIX_LENS_DIR:?set FIX_LENS_DIR to the folder with the FIX Lens index.html}"
: "${WORK:?set WORK to a scratch folder outside the repository}"
export FIX_LENS_DIR
mode="${1:-full}"
mkdir -p "$WORK" reports/partial

echo "== 1. datasets and ground truth (fixed seeds)"
python3 generators/build.py
echo "== 2. hand-built cases"
node tests/run_cases.mjs | tail -1
echo "== 3. simulated and engine datasets, format equivalence"
node tests/run_datasets.mjs | tail -1
if [ "$mode" != "quick" ]; then
  echo "== 4. external sources (downloads only)"
  bash sources/fetch.sh "$WORK/src" > "$WORK/fetch.log" 2>&1 || echo "BLOCKED: a download failed, see $WORK/fetch.log"
  python3 -I tests/dictionary_check.py --product "$FIX_LENS_DIR" --orchestra "$WORK/src/orchestra" --quickfix "$WORK/src/quickfix/repo/spec" --out reports/partial/dictionary.json
  python3 -I tests/external_test.py --sources "$WORK/src" > "$WORK/external.log" && tail -3 "$WORK/external.log"
  echo "== 5. property-based and differential tests (needs hypothesis; quickfix for the differential)"
  if [ ! -x "$WORK/venv/bin/python" ]; then python3 -m venv "$WORK/venv" && "$WORK/venv/bin/pip" install -q hypothesis==6.170.22 quickfix==1.16.0; fi
  "$WORK/venv/bin/python" tests/property_test.py | grep -E "^(PASS|FAIL|BLOCKED)"
  echo "== 6. performance datasets, a copy of the product with the limit lifted, benchmarks"
  python3 generators/build.py --perf "$WORK/perf" && python3 benchmarks/make_variants.py "$WORK/perf" > /dev/null
  rm -rf "$WORK/fix-lens-nolimit" && cp -r "$FIX_LENS_DIR" "$WORK/fix-lens-nolimit" && rm -rf "$WORK/fix-lens-nolimit/.git"
  sed -i 's/bytes <= 1048576 \&\& messages <= 1000/bytes <= 16777216 \&\& messages <= 10000/' "$WORK/fix-lens-nolimit/src/limits.js"
  node benchmarks/bench_node.mjs --perf "$WORK/perf" --lifted "$WORK/fix-lens-nolimit" --out reports/partial/bench-node.json | tail -5
  echo "== 7. the page in Chromium (Playwright must be resolvable by node)"
  node tests/browser_test.cjs --perf "$WORK/perf" --lifted "$WORK/fix-lens-nolimit" | grep -E "^(PASS|FAIL|[0-9]+ browser)"
  echo "== 8. the product's own tests"
  (cd "$FIX_LENS_DIR" && npx vitest run 2>&1 | tail -6)
fi
echo "== reports"
node tests/report.mjs
