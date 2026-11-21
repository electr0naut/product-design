"""Shared test-session guards.

Two mutmut-specific adjustments live here. Neither changes behaviour when the
suite runs under plain ``pytest``/``make check``.

* Subprocess CLI tests inherit this process's environment. mutmut sets
  ``MUTANT_UNDER_TEST`` so the trampoline in a mutated module can dispatch to
  the selected mutant; a child interpreter that imports the mutated script also
  imports the trampoline, which then tries to re-read mutmut's configuration
  from the child's temporary working directory and fails. mutmut keeps the
  active mutant in process-local state as well, so removing the variable here
  does not change which mutant the test process runs, and it keeps subprocesses
  on the unmutated code they are meant to exercise.
* mutmut derives mutant keys from the source path relative to the working
  directory (``shared.scripts.backlog.x_parse_story_map__mutmut_1``), while the
  tests import the modules flat (``import backlog``) with ``shared/scripts`` on
  ``sys.path``. Aliasing the package-qualified module into ``sys.modules``
  lets the trampoline record keys mutmut can match without rewriting every
  test import.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parents[1]

MUTATED_MODULES = ("backlog", "gate_reviews")


def pytest_configure(config: object) -> None:
    if "mutmut" not in sys.modules:
        return
    os.environ.pop("MUTANT_UNDER_TEST", None)
    for path in (str(SCRIPTS), str(ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
    for name in MUTATED_MODULES:
        module = importlib.import_module(f"shared.scripts.{name}")
        sys.modules.setdefault(name, module)
