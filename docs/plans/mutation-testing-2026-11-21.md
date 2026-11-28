# Mutation testing: review gate and backlog parsers (2026-11-21)

Advisory mutation testing of `shared/scripts/gate_reviews.py` and
`shared/scripts/backlog.py` with mutmut 3.8.1. The mutation score is a
diagnostic: it is not a release gate and must not be "fixed" by weakening the
review rules. Only tests changed in this pass; no production behaviour changed.

## Scope and method

mutmut 3.8.1 has no line-range filter, so "changed lines only" is implemented
with the supported scoping: mutate only test-covered lines in the two modules,
which are the files this planning pass touched (`gate_reviews.py` since
`07083fa`; `backlog.py` is its parser dependency). The run mutates every
function on a covered line, not only lines touched by a diff.

Configuration lives in `[tool.mutmut]` in `pyproject.toml`:

- `source_paths` — the two modules.
- `pytest_add_cli_args_test_selection` — `shared/scripts/tests`.
- `also_copy` — `shared/` and the phase template/prompt directories the
  generation CLIs read, so copied scripts still resolve their resources.
- `mutate_only_covered_lines = true`.

`make mutate` runs it. Reproduction:

```bash
make mutate                                   # run, then list survivors
uv run --with "mutmut==3.8.1" mutmut results  # survivors only
uv run --with "mutmut==3.8.1" mutmut show <mutant>
```

`shared/scripts/tests/conftest.py` carries two guards that only act when
`mutmut` is imported (they are no-ops under `make check`):

- Subprocess CLI tests must not inherit `MUTANT_UNDER_TEST`, otherwise the
  child interpreter imports the trampoline and tries to read mutmut's config
  from the test's temporary working directory. mutmut keeps the active mutant
  in process-local state, so removing the variable does not change the mutant
  under test; it keeps subprocesses on unmutated code.
- mutmut derives mutant keys from the path relative to the working directory
  (`shared.scripts.backlog.x_parse_story_map__mutmut_1`), while the tests
  import the modules flat with `shared/scripts` on `sys.path`. The conftest
  aliases the package-qualified module into `sys.modules` so coverage and
  trampoline keys line up without rewriting every test import.

## Results

| Run | Scored mutants | Killed | Survived | Score |
| --- | --- | --- | --- | --- |
| Before | 2784 | 2210 | 574 | 79.4% |
| After initial test additions | 2784 | 2568 | 216 | 92.2% |
| After PR #24 review fixes | 2784 | 2571 | 213 | 92.3% |

Twenty-two further mutations are reported as "not checked" (mutants that could
not be applied); they are excluded from both scores.

## What the new tests pin

54 tests were added across `test_gate_reviews.py`, `test_artifact_status.py`,
`test_provenance_snapshot.py` and `test_backlog.py`:

- Assumption expiry is valid through `review_by` and expires the day after;
  `review_by` may equal `checked_at`.
- Answers and change resolutions recorded at the same timestamp as an approval
  still require reapproval; answers and change events at exactly the question
  or change raise time are valid.
- Every unanswered question is reported, answers are matched to their own
  question, questions do not leak across lanes, and reapproval uses the
  decision for that gate and lane.
- Feedback is scoped to its own lane; stale approvals name the affected roles.
- Optional decision fields (`source_commit`, `recorded_by`, `attestation`) are
  accepted and type-checked; artifacts must be strings; the lane `epic` flag is
  a boolean and defaults to `false`.
- Policy digests ignore key order and pin the canonical JSON encoding.
- The seven-day warning window includes the `review_by` day, `warning_days=0`
  is allowed, and the projected status is evaluated at the requested day.
- Portal views report every pending lane for a role, keep other roles'
  decisions separate, and exclude answered or other-role questions.
- Story-map headers are matched case-insensitively by title, column defaults
  and trace fallbacks are defined, and malformed rows, duplicate rows,
  frontmatter comments/empty blocks/BOM, fence stripping, story-file filtering
  and requirement rows are covered.
- Build order breaks priority ties by epic before ID.

Two additional tests from PR #24 review pin cross-gate decision scope when two
gates share `E01`, and keep the receipt fixture's initial gate evaluation on
November 21 even when the host clock is later. The existing equality-date test
also evaluates on its stated date. Rerunning all initial survivors killed three
more mutants: `_evaluate_gate_data` 116 and 230 (gate filters) and
`generation_receipt` 120. No production code changed.

## Reading the remaining survivors

213 mutants survive. They are grouped in the appendix as:

- **W — wording, labels, or field-name mutations (130).** Many alter only
  human-readable errors or labels passed to `reject_symlink`; others rename
  output fields, which can be part of the API contract and are *not* equivalent.
  Triage field-name survivors as test gaps where consumers rely on those keys;
  do not freeze incidental prose merely to raise the score.
- **E — equivalent under the current tests (49).** Defaults (`None` versus
  omitted or `False` after `bool()`), redundant boolean conditions, and
  sentinel substitutions. This classification does not prove equivalence for
  every possible input; revisit it if the contract expands.
- **G — behaviour-bearing test gaps (34).** Remaining gaps include history
  filtering (`previously_approved`), the hash-cache `continue`,
  `include_cross_cutting`'s default, the unchecked `unknown` lane list,
  projected status date in `generation_receipt`, multi-gate policy digests,
  and parser corners (fence counts, short rows, table-cell trimming, cycle
  ordering). Cross-gate and cross-lane filters are *already* part of the
  contract: test them with overlapping lane IDs rather than calling them
  owner decisions. The new cross-gate test killed the two known
  `_evaluate_gate_data` gate-filter mutants; any remaining scope-filter
  survivors belong in this test-gap category.

Write tests for contract-covered gaps without changing production behavior.
Ask the owner only where the expected behavior really is unspecified; a
surviving mutant alone is not a policy question.

## Appendix: every surviving mutant

Format: mutant ids within each function; a backticked number is the `__mutmut_<n>` suffix.

- **x__build_order** — gaps: `35`; wording: `11`, `12`
- **x__evaluate_gate_data** — equivalent: `255`, `260`, `262`, `302`, `303`, `304`, `305`, `322`; wording: `14`, `21`, `266`, `267`, `274`, `275`, `288`, `289`, `292`, `293`, `296`, `297`, `300`, `301`, `306`, `307`, `308`, `315`, `316`, `346`, `347`
- **x__find_cycle** — gaps: `8`, `17`
- **x__non_goal_refs** — wording: `9`, `10`
- **x__project_artifact** — gaps: `88`, `94`, `105`, `106`, `155`, `156`, `157`, `225`; equivalent: `1`, `2`, `20`, `32`, `37`, `101`; wording: `16`, `23`, `24`, `35`, `36`, `42`, `43`, `44`, `45`, `203`, `204`, `205`, `206`, `209`, `210`
- **x__scalar** — equivalent: `12`
- **x__section** — wording: `15`
- **x__story_row** — gaps: `4`, `11`, `12`, `25`, `28`; equivalent: `14`, `62`, `71`, `78`; wording: `13`, `19`, `20`, `21`, `22`, `23`, `24`, `31`, `58`, `59`, `60`, `61`, `69`, `70`
- **x__strip_fences** — gaps: `18`, `22`, `26`, `29`, `31`; equivalent: `7`
- **x__table_cells** — gaps: `6`, `7`, `23`, `24`; wording: `51`
- **x__unique** — equivalent: `4`
- **x_artifact_hash** — wording: `7`, `17`
- **x_change_state** — gaps: `5`; equivalent: `11`; wording: `13`, `14`, `18`, `19`
- **x_check_backlog** — equivalent: `2`; wording: `76`, `77`
- **x_feedback_state** — gaps: `5`; wording: `17`, `18`, `19`, `20`
- **x_generation_receipt** — gaps: `14`; equivalent: `29`; wording: `27`, `28`, `42`, `43`, `44`, `45`, `48`, `49`, `91`
- **x_load_manifest_snapshot** — equivalent: `2`; wording: `5`, `6`, `15`
- **x_maybe_enforce_gate** — gaps: `2`, `3`, `29`; equivalent: `51`; wording: `54`, `55`
- **x_nonempty** — equivalent: `4`
- **x_parse_frontmatter** — equivalent: `13`, `25`, `28`; wording: `4`, `29`
- **x_parse_requirements** — equivalent: `23`
- **x_parse_story_map** — gaps: `31`; equivalent: `4`, `5`, `6`, `7`, `24`, `33`, `49`, `50`; wording: `45`, `46`, `47`, `48`, `67`
- **x_parsed_timestamp** — equivalent: `11`; wording: `7`, `8`
- **x_policy_digest** — wording: `14`
- **x_portal_view** — wording: `23`, `24`, `29`, `30`, `33`, `34`, `43`, `44`, `49`, `50`, `53`, `54`, `57`, `58`, `59`, `60`, `61`, `62`, `74`, `75`
- **x_priority_rank** — equivalent: `3`; wording: `10`, `11`, `12`, `15`
- **x_requirement_refs** — wording: `8`
- **x_story_files** — equivalent: `2`, `18`; wording: `5`, `6`, `21`, `22`
- **x_story_refs** — wording: `5`
- **x_validate** — gaps: `125`, `200`; equivalent: `9`, `10`, `63`, `118`, `325`; wording: `48`, `98`, `107`, `121`, `234`, `879`
- **xǁStoryǁhas_tasks** — wording: `7`, `8`
- **xǁStoryǁtext** — equivalent: `7`
