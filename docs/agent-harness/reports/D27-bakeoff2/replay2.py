"""D27 bake-off 2: the spec pass and the prove step on a fallback model with no tools.
Reads run files, host ticket copies, repository history and the trusted repo; calls only throwaway
profiles; model-written tests run only in a container with no network; writes only beside itself."""
import glob, hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile, threading, time, tomllib
from pathlib import Path

KIT = Path.home() / ".local/share/agent-harness/kit"
sys.path.insert(0, str(KIT / "src"))
from harness import repos, reviewer, specs  # noqa: E402

OUT = Path(__file__).parent
RUNS = Path("/srv/lab/agent-harness/work/runs")
REPO = Path.home() / ".local/state/agent-harness/trusted/fix-lens.git"
RECORDS = Path.home() / ".local/state/agent-harness/records"
TICKETS = Path.home() / ".local/state/agent-harness/tickets"
DOCS = Path.home() / "product-design"
P = "docs/agent-harness/fix-lens"
DEPS = "/srv/lab/agent-harness/deps/fix-lens/node_modules"
CFG = repos.effective(tomllib.loads((KIT / "harness.host.toml").read_text()), Path("/srv/lab/agent-harness/work/fix-lens"), KIT)
SPEC_SCHEMA = reviewer.load_schema("spec_findings", KIT)
PROOF_SCHEMA = reviewer.load_schema("proof", KIT)
PROOF_SCHEMA = {**PROOF_SCHEMA, "properties": {**PROOF_SCHEMA["properties"], "test_source": {"type": "string"}},
                "required": [*PROOF_SCHEMA["required"], "test_source"]}  # fmt: skip
PROFILES = {"qwen4-max": "bk-sp-max", "qwen3.7-plus": "bk-sp-plus"}
IMAGE = subprocess.run(["docker", "inspect", "-f", "{{.Image}}", "hermes"], capture_output=True, text=True, check=True).stdout.strip()
SPEC_CASES = [("FXL-1", "-2", "buggy"), ("FXL-1B", "-3", "buggy")] + [(f"FXL-{n}", "", "clean") for n in (10, 11, 12, 13, 14, 17, 18)]
PROVE_CASES = [("FXL-1", "-2", "F1", "8057bbf")] + [("FXL-1B", "-3", f"F{n}", "7f47748") for n in range(1, 5)]


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def from_docs(commit, path):
    return subprocess.run(["git", "-C", str(DOCS), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout


def state(key, tag):
    gates = json.loads((RUNS / key / f"gates{tag}.json").read_text())
    return gates["base"], gates["head"]


def inputs(key, tag):
    """The ticket and design text the review of that state read (or would have read)."""
    if key == "FXL-1":  # no design file existed at its review time, and no spec pass ran then
        return from_docs("3902c8ee", f"{P}/tickets/FXL-1.md").decode(), []
    if key == "FXL-1B":
        return (from_docs("f557ef72", f"{P}/tickets/FXL-1B.md").decode(),
                [("technical-design.md", from_docs("f557ef72", f"{P}/technical-design.md").decode())])
    rec = json.loads(Path(sorted(glob.glob(str(RECORDS / key / "*-review-*.json")))[-1]).read_text())["data"]["copies"]
    design = from_docs(rec["commit"], f"{P}/technical-design.md")
    assert hashlib.sha256(design).hexdigest() == rec["design_sha256"], key
    return (TICKETS / f"{key}.md").read_text(), [("technical-design.md", design.decode())]


def pack(head, extra=(), tests=()):
    names = git("ls-tree", "-r", "--name-only", head).splitlines()
    keep = [n for n in names if (n.startswith("src/") and not n.startswith("src/dictionary/"))
            or n in ("index.html", "package.json", *extra, *tests)]
    return "".join(f"\n\n=== file: {n} ===\n{git('show', f'{head}:{n}')}" for n in sorted(set(keep)))


def spec_prompt(key, tag):
    base, head = state(key, tag)
    ticket, docs = inputs(key, tag)
    plan = reviewer.review_diff(REPO, base, head, CFG)
    diff = "\n".join(plan["chunks"])
    listed = "".join(f"\n\n--- Design document: {n} ---\n{t}" for n, t in docs)
    note = ""
    if plan["excluded"]:
        note = f"\n\nNot shown (generated or vendored, left out by configuration): {', '.join(e['path'] for e in plan['excluded'])}."
    return (
        "You check a code change against the SPECIFICATION it must follow, not against style. "
        "Report only deviations from the quoted text below: interfaces and names, the rules "
        "in the design, and reference values or examples in the ticket (work the reference "
        "inputs through the code and compare with the stated outputs). Never report style, "
        "naming taste or things the text does not say. You have no tools. The repository's source "
        "files at the change are given at the end. For every finding, `spec_ref` must be one "
        "sentence or clause copied word for word from the ticket or a design document, the "
        "text the code deviates from; give the file and the changed line nearest the "
        "deviation, and a concrete input and the wrong output in `failure`. If there is no "
        "deviation, return an empty list.\n\n--- Ticket (full text) ---\n" + ticket + listed
        + f"\n\n--- The change (diff) ---\n{diff}{note}"
        + f"\n\nOutput ONLY one JSON object that matches this schema:\n{json.dumps(SPEC_SCHEMA)}"
        + "\n\n--- Repository source files at the change ---" + pack(head)
    )


def finding(key, tag, fid):
    return next(f for f in json.loads((RUNS / key / f"review{tag}.json").read_text())["findings"] if f["id"] == fid)


def prove_prompt(key, tag, fid):
    _, head = state(key, tag)
    f, c = finding(key, tag, fid), CFG["commands"]
    return (
        "Write the smallest test that FAILS on this code if the finding is true, in the project's "
        f"test style, in one new file under {c.get('test_dir', 'tests/')}. You cannot run it; "
        "it will be run for you. You have no tools: put the new file's whole source in "
        "test_source. Answer with test_file (the new file's path) and test_id: "
        f"the full {c.get('id_kind', 'pytest node id')} of your test, exactly as "
        f"`{c.get('collect_display')}` would print it (for example `{c.get('id_example')}`), not just its "
        f"title. Finding: {json.dumps(f)}"
        + f"\n\nOutput ONLY one JSON object that matches this schema:\n{json.dumps(PROOF_SCHEMA)}"
        + "\n\n--- Repository source files, and one existing test with its helper, for the style ---"
        + pack(head, extra=(f["file"],), tests=("test/framing.test.js", "test/helpers/fix.js"))
    )


def run_test(sha, tfile, source, tid, failure):
    """(proven-style outcome, why) of one new test file on a copy of `sha`, in a closed container."""
    work = Path(tempfile.mkdtemp(prefix="t-", dir=OUT / "scratch"))
    try:
        tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", sha], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            tf.extractall(work, filter="data")
        (work / "node_modules").mkdir()
        (work / tfile).write_text(source)
        subs = reviewer.id_substitutions(CFG["commands"], tid)
        p = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--user", "1000:1000", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--memory", "1g", "--pids-limit", "300", "--tmpfs", "/tmp",
             "-e", "HOME=/tmp", "-v", f"{work}:/w", "-v", f"{DEPS}:/w/node_modules:ro", "-w", "/w",
             "--entrypoint", "node_modules/.bin/vitest", IMAGE, "run", subs["file"], "-t", subs["name_re"],
             "--reporter=junit", "--outputFile=r.xml", "--no-cache"],
            capture_output=True, text=True, timeout=180, check=False)  # fmt: skip
        xml = work / "r.xml"
        if xml.is_symlink() or not xml.is_file():
            return None, f"no report (exit {p.returncode}): {(p.stderr or p.stdout).strip()[-250:]}"
        proven, why = reviewer.proof_outcome(xml, failure, ("AssertionError",))
        if proven is None and p.returncode == 0:
            import xml.etree.ElementTree as ET
            ran = [t for t in ET.parse(xml).getroot().iter("testcase") if t.find("skipped") is None]
            if len(ran) == 1 and ran[0].find("failure") is None and ran[0].find("error") is None:
                return False, "the one test passed"
        return proven, why
    except subprocess.TimeoutExpired:
        return None, "the test run timed out"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def judge_test(key, tag, fid, fixed, ans):
    _, head = state(key, tag)
    f = finding(key, tag, fid)
    tfile, tid, source = ans.get("test_file", ""), ans.get("test_id", ""), ans.get("test_source", "")
    if ans.get("could_not_prove_because") or not tid or not source:
        return {"note": "the model wrote no test: " + str(ans.get("could_not_prove_because"))[:200]}
    if not re.fullmatch(r"test/[A-Za-z0-9][A-Za-z0-9._-]*\.test\.js", tfile):
        return {"note": f"refused path {tfile!r}"}
    if tid.startswith("-") or tid.split(" > ")[0] != tfile:
        return {"note": "test_id does not belong to test_file"}
    exists = tfile in git("ls-tree", "-r", "--name-only", head).splitlines()
    buggy = run_test(head, tfile, source, tid, f["failure"])
    good = run_test(git("rev-parse", fixed).strip(), tfile, source, tid, f["failure"])
    return {"overwrites_existing": exists, "buggy": buggy, "fixed": good,
            "right": buggy[0] is True and good[0] is False and not exists}  # fmt: skip


def ask(model, text):
    return subprocess.run(
        ["docker", "exec", "-i", "-u", "hermes", "-w", "/tmp/bk-sp-empty", "hermes", "hermes", "-p",
         PROFILES[model], "chat", "--query-file", "-", "--oneshot", "-Q", "-t", "context_engine",
         "--ignore-rules", "--max-turns", "2"],
        input=text, capture_output=True, text=True, timeout=900, check=False)  # fmt: skip


def converse(model, text, schema, row):
    for n in (1, 2):
        start = time.time()
        extra = "" if n == 1 else f"\n\nYour previous reply was rejected: {row['calls'][-1]['why']}. Reply with only the JSON object."
        try:
            p = ask(model, text + extra)
            code, out = p.returncode, p.stdout
            why = "" if code == 0 else f"exit {code}: {p.stderr.strip()[-200:]}"
        except subprocess.TimeoutExpired:
            code, out, why = -1, "", "timed out after 900 s"
        got = None
        if code == 0:
            why = "no JSON object in the reply"
            for obj in reviewer.parse_json_objects(out):
                try:
                    reviewer.validate(obj, schema)
                except Exception as exc:
                    why = str(exc)
                    continue
                got, why = obj, ""
                break
        row["calls"].append({"seconds": round(time.time() - start, 1), "exit": code, "why": why, "raw": out[-20000:]})
        if got is not None:
            return got
    return None


def work(model, jobs, lock):
    for kind, case, round_ in jobs:
        row = {"kind": kind, "case": list(case), "round": round_, "model": model, "calls": []}
        if kind == "spec":
            key, tag, label = case
            base, head = state(key, tag)
            ticket, docs = inputs(key, tag)
            text = spec_prompt(key, tag)
            got = converse(model, text, SPEC_SCHEMA, row)
            if got is not None:
                kept, dropped = specs.filter_spec_findings(got["findings"], [ticket, *(t for _, t in docs)])
                reach, low = reviewer.filter_findings(kept, CFG, reviewer.changed_lines(REPO, base, head))
                row |= {"reported": got["findings"], "quote_dropped": dropped, "filter_dropped": low,
                        "reach_review": [f["id"] for f in reach]}
            said = "no valid reply" if got is None else f"{len(got['findings'])} reported, {len(row['reach_review'])} reach the review"
        else:
            key, tag, fid, fixed = case
            text = prove_prompt(key, tag, fid)
            got = converse(model, text, PROOF_SCHEMA, row)
            row |= {"answer": got, "result": judge_test(key, tag, fid, fixed, got) if got else {"note": "no valid reply"}}
            said = json.dumps(row["result"])[:200]
        row["prompt_chars"] = len(text)
        with lock:
            with open(OUT / "results.jsonl", "a") as fh:
                fh.write(json.dumps(row) + "\n")
            print(model, kind, case, "round", round_, "->", said, [c["seconds"] for c in row["calls"]], flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["control"]:  # Claude's recorded proof tests through this same runner
        for key, tag, fid, fixed in PROVE_CASES:
            rec = next(p for p in json.loads((RUNS / key / f"review{tag}.json").read_text())["proofs"] if p["finding_id"] == fid)
            res = judge_test(key, tag, fid, fixed, {**rec, "could_not_prove_because": ""})
            print(key, fid, json.dumps(res))
        raise SystemExit
    if sys.argv[1:] == ["sizes"]:
        for key, tag, label in SPEC_CASES:
            print("spec", key, label, len(spec_prompt(key, tag)))
        for key, tag, fid, _ in PROVE_CASES:
            print("prove", key, fid, len(prove_prompt(key, tag, fid)))
        raise SystemExit
    jobs = [("spec", c, 1) for c in SPEC_CASES] + [("prove", c, 1) for c in PROVE_CASES]
    jobs += [("spec", c, 2) for c in SPEC_CASES[:2]] + [("prove", c, 2) for c in PROVE_CASES]
    lock = threading.Lock()
    threads = [threading.Thread(target=work, args=(m, jobs, lock)) for m in PROFILES]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("ALL DONE", len(jobs), "per model")
