"""Wait for a proof result and print it. For jobs: the CLI refuses a plain `sleep`.

    python3 docs/agent-harness/jobs/wait-proof.py <40-character sha> [seconds, default 480]

Exit 0 and the result's text when it is there; exit 3 and one line when it has not come in time.
"""

import re
import sys
import time
from pathlib import Path

RESULTS = Path("/var/lib/harness-jobs/proof/results")


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2 or not re.fullmatch(r"[0-9a-f]{40}", argv[0]):
        print("usage: wait-proof.py <40-character sha> [seconds]", file=sys.stderr)
        return 2
    limit = min(int(argv[1]) if len(argv) == 2 else 480, 540)
    result = RESULTS / f"{argv[0]}.txt"
    deadline = time.monotonic() + limit
    while not result.is_file():
        if time.monotonic() >= deadline:
            print(f"NOT YET: no result for {argv[0]} after {limit} s")
            return 3
        time.sleep(10)
    print(result.read_text(errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
