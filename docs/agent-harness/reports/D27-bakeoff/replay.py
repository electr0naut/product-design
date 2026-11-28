"""D27 part 2 bake-off: replay recorded review findings through a fallback model's refute step.
Reads run files and the trusted repo; calls only the throwaway profiles; writes only beside itself."""
import json, os, subprocess, sys, threading, time
from pathlib import Path

KIT = Path.home() / ".local/share/agent-harness/kit"
sys.path.insert(0, str(KIT / "src"))
from harness import reviewer  # noqa: E402

RUNS = Path("/srv/lab/agent-harness/work/runs")
REPO = Path.home() / ".local/state/agent-harness/trusted/fix-lens.git"
OUT = Path(__file__).parent
SCHEMA = reviewer.load_schema("refutations", KIT)
PROFILES = {"qwen4-max": "bk-rv-max", "qwen3.7-plus": "bk-rv-plus"}


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def cases():
    for run in sorted(RUNS.glob("FXL-*")):
        for review in sorted(run.glob("review*.json")):
            tag = review.stem.removeprefix("review")  # "" or "-2": the gates file of the same state
            data = json.loads(review.read_text())
            if not data.get("findings"):
                continue
            gates = json.loads((run / f"gates{tag}.json").read_text())
            acs = json.loads((run / "readiness.json").read_text())["acceptance_criteria"]
            claude = {r["finding_id"]: r for r in data.get("refutations", [])}
            for f in data["findings"]:
                yield {
                    "key": run.name, "review": review.name, "head": gates["head"], "finding": f,
                    "criteria": "\n".join(f"{a['id']}: {a['text']}" for a in acs),
                    "claude": claude.get(f["id"], {}).get("verdict"),
                    "blocked": f["id"] in data["decision"].get("blocking", []),
                }  # fmt: skip


def pack(head, finding_file):
    """The sources at the reviewed commit, in place of Claude's Read tool: every file under src/
    (not the generated dictionaries), the page and package files, and the finding's own file."""
    names = git("ls-tree", "-r", "--name-only", head).splitlines()
    keep = [n for n in names if (n.startswith("src/") and not n.startswith("src/dictionary/"))
            or n in ("index.html", "package.json", finding_file)]
    parts = [f"\n\n=== file: {n} ===\n{git('show', f'{head}:{n}')}" for n in sorted(set(keep))]
    left = sorted(set(names) - set(keep))
    return "".join(parts), left


def prompt(case):
    f, head = case["finding"], case["head"]
    files, left = pack(head, f["file"])
    folders = sorted({n.split("/")[0] for n in left})
    return (
        "You are a different reviewer. Try to REFUTE this finding. You have no tools. The "
        "repository's source files at the change are given at the end; read the ones the "
        "finding's file imports before you decide (a rule may be enforced elsewhere). Verdict: "
        "refuted, stands or unsure."
        "\n\nAcceptance criteria:\n" + case["criteria"]
        + ("\n\nThis finding quotes the ticket or design in `spec_ref`. Judge it against "
           "that quote, not only against the acceptance criteria above." if f.get("spec_ref") else "")
        + f"\n\nFinding: {json.dumps(f)}\n\nCode around the finding (head):\n"
        + reviewer.excerpt(REPO, head, f["file"], f["line"])
        + f"\n\nOutput ONLY one JSON object that matches this schema:\n{json.dumps(SCHEMA)}"
        + f"\n\nRepository files (not included: other files under {', '.join(folders) or 'none'}):"
        + files
    )


def ask(model, text):
    p = subprocess.run(
        ["docker", "exec", "-i", "-u", "hermes", "-w", "/tmp/bk-rv-empty", "hermes", "hermes", "-p",
         PROFILES[model], "chat", "--query-file", "-", "--oneshot", "-Q", "-t", "todo",
         "--ignore-rules", "--max-turns", "2"],
        input=text, capture_output=True, text=True, timeout=900, check=False,
    )  # fmt: skip
    return p.returncode, p.stdout, p.stderr


def verdict_in(raw, fid):
    why = "no JSON object in the reply"
    for obj in reviewer.parse_json_objects(raw):
        try:
            reviewer.validate(obj, SCHEMA)
        except Exception as exc:
            why = str(exc)
            continue
        for r in obj["refutations"]:
            if r["finding_id"] == fid:
                return r, ""
        why = "no verdict for this finding id"
    return None, why


def one(model, case, round_):
    fid = case["finding"]["id"]
    row = {k: case[k] for k in ("key", "review", "head", "claude", "blocked")}
    row |= {"id": fid, "severity": case["finding"]["severity"], "source": case["finding"].get("source", "find"),
            "model": model, "round": round_, "calls": [], "verdict": None}
    text = prompt(case)
    row["prompt_chars"] = len(text)
    for n in (1, 2):
        start = time.time()
        try:
            code, out, err = ask(model, text if n == 1 else f"{text}\n\nYour previous reply was rejected: "
                                 f"{row['calls'][-1]['why']}. Reply with only the JSON object.")
        except subprocess.TimeoutExpired:
            code, out, err = -1, "", "timed out after 900 s"
        got, why = verdict_in(out, fid) if code == 0 else (None, f"exit {code}: {err.strip()[-200:]}")
        row["calls"].append({"seconds": round(time.time() - start, 1), "exit": code, "why": why, "raw": out[-6000:]})
        if got:
            row |= {"verdict": got["verdict"], "reason": got["reason"], "counter": got.get("counter_evidence", "")}
            break
    return row


def work(model, jobs, lock):
    for round_, case in jobs:
        done = one(model, case, round_)
        with lock:
            with open(OUT / "results.jsonl", "a") as fh:
                fh.write(json.dumps(done) + "\n")
            print(model, round_, done["key"], done["review"], done["id"], "claude", done["claude"], "->",
                  done["verdict"], [c["seconds"] for c in done["calls"]], flush=True)


if __name__ == "__main__":
    allc = list(cases())
    if sys.argv[1:] == ["list"]:
        for c in allc:
            print(c["key"], c["review"], c["head"][:7], c["finding"]["id"], c["claude"], "blocked" if c["blocked"] else "", len(prompt(c)))
        print(len(allc), "findings")
        raise SystemExit
    recent = {f"FXL-{n}" for n in range(9, 19)}
    jobs = [(1, c) for c in allc] + [(2, c) for c in allc if c["key"] in recent]
    lock = threading.Lock()
    threads = [threading.Thread(target=work, args=(m, jobs, lock)) for m in PROFILES]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("ALL DONE", len(jobs), "per model")
