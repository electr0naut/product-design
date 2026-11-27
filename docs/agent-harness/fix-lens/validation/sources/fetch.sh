#!/usr/bin/env bash
# Downloads the external material into <dir>, one folder per source, at the commits recorded in manifest.json.
# Downloads only: nothing of this project is sent anywhere. The files are untrusted: nothing in them is run.
#   bash sources/fetch.sh <dir>
set -euo pipefail
dir="${1:?usage: fetch.sh <empty directory>}"
mkdir -p "$dir" && cd "$dir"
get() {   # name, url, commit
  mkdir -p "$1"
  if [ ! -d "$1/repo/.git" ]; then
    git init -q "$1/repo"
    git -C "$1/repo" remote add origin "$2"
    git -C "$1/repo" fetch -q --depth 1 origin "$3" && git -C "$1/repo" checkout -q FETCH_HEAD
  fi
  echo "$1 $(git -C "$1/repo" rev-parse HEAD)"
}
get quickfix          https://github.com/quickfix/quickfix.git                        386ce46e917ae494ab6e90b1be90fd421cdbe3f9
get quickfixj         https://github.com/quickfix-j/quickfixj.git                     2b3d00869c402815d6f73682dfa88d1d520889c1
get log-analyzer      https://github.com/siva-balan/Log-Analyzer.git                  5566b563ccc5fa4276743edd79ecbb2805a729eb
get fix-log-analyzer  https://github.com/vikram-dhamodaran/fix-log-analyzer.git       f89513fbbb565bc9704fb49a1116b3689082bdfc
get study-guide       https://github.com/backstreetbrogrammer/55_FIX_Protocol_Study_Guide.git f452857782589e84941846c7a7b1404c6b195bfc
get fiximulator       https://github.com/FIXimulator/FIXimulator.git                  06f8bb36370197d7d2c795384a18693c24e77165
mkdir -p orchestra
c=ed111f1bd84bb4e7209e52f939aefe83b86cbc7f
for f in "FIX%20Standard/OrchestraFIX42.xml" "FIX%20Standard/OrchestraFIX44.xml" LICENSE; do
  curl -fsS -o "orchestra/$(basename "$f")" "https://raw.githubusercontent.com/FIXTradingCommunity/orchestrations/$c/$f"
done
sha256sum orchestra/* quickfix/repo/spec/FIX42.xml quickfix/repo/spec/FIX44.xml log-analyzer/repo/sample_fix44.log \
  fix-log-analyzer/repo/sample_log.log study-guide/repo/fix_log1.txt "fiximulator/repo/logs/FIX.4.2-FIXIMULATOR-BANZAI.messages.log"
