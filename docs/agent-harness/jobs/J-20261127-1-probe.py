"""J-20261127-1: what a job can and cannot do, seen from inside the real unit. Prints no secret."""

import os
import pwd
import socket
import subprocess
from pathlib import Path

REAL_HOME = Path("/home/harness-job")
SPOOL = Path("/var/lib/harness-jobs")


def attempt(label: str, expected: str, action) -> None:
    try:
        result = action()
        outcome = f"SUCCEEDED {result}".rstrip() if result is not None else "SUCCEEDED"
    except Exception as exc:  # the probe reports every refusal, whatever its kind
        outcome = f"refused ({type(exc).__name__}: {exc})"
    print(f"{label}: {outcome}   [expected: {expected}]")


def run(*argv: str) -> str:
    done = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    return f"exit {done.returncode}: {(done.stdout + done.stderr).strip()[:200]}"


def write_then_remove(path: Path) -> None:
    path.write_text("probe")
    path.unlink()


def connect_docker() -> str:
    with socket.socket(socket.AF_UNIX) as sock:
        sock.connect("/run/docker.sock")
    return "connected"


def main() -> None:
    home = Path(os.environ.get("HOME", ""))
    print(f"user: {pwd.getpwuid(os.getuid()).pw_name} uid {os.getuid()} groups {sorted(os.getgroups())}")
    print(f"HOME: {home}")
    print(f"PATH: {os.environ.get('PATH')}")
    print(f"working folder: {Path.cwd()}")
    for name in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "GIT_CONFIG_GLOBAL"):
        print(f"{name} is set: {name in os.environ}")
    job_id = home.parent.name
    attempt("write the real home", "refused", lambda: write_then_remove(REAL_HOME / ".job-probe"))
    attempt("write the real ~/.ssh", "refused", lambda: write_then_remove(REAL_HOME / ".ssh" / "probe"))
    attempt("write this job's own HOME", "succeeded", lambda: write_then_remove(home / "probe"))
    attempt("write this job's outbox", "succeeded", lambda: write_then_remove(SPOOL / "outbox" / job_id / "probe.tmp"))
    attempt("list /home/ubay", "refused", lambda: len(os.listdir("/home/ubay")))
    attempt("list /srv", "refused", lambda: len(os.listdir("/srv")))
    attempt("list the sealed folder", "refused", lambda: len(os.listdir(SPOOL / "sealed")))
    attempt("write the ledger", "refused", lambda: write_then_remove(SPOOL / "ledger" / "probe"))
    attempt("write the queue", "refused", lambda: write_then_remove(SPOOL / "queue" / "probe"))
    attempt("write the launcher's folder", "refused", lambda: write_then_remove(Path("/usr/local/lib/harness-jobs/probe")))
    attempt("write /usr/local/bin", "refused", lambda: write_then_remove(Path("/usr/local/bin/probe")))
    attempt("connect to the Docker socket", "refused", connect_docker)
    attempt("sudo", "a non-zero exit", lambda: run("sudo", "-n", "true"))
    attempt("crontab -l", "a permission error", lambda: run("crontab", "-l"))
    attempt("git name", "harness-job", lambda: run("git", "config", "--global", "user.name"))
    attempt("remotes of this clone", "none", lambda: run("git", "remote"))
    attempt("kit clone", "a commit id", lambda: run("git", "-C", str(home.parent / "agent-harness"), "log", "-1", "--format=%H"))
    attempt("CLI version", "2.1.332", lambda: run("/usr/local/bin/claude", "--version"))


if __name__ == "__main__":
    main()
