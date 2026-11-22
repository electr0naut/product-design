.PHONY: check python-check frontend-check format format-check mutate

check: python-check frontend-check

python-check:
	uv run ruff format --check shared/scripts
	uv run ruff check shared/scripts
	uv run pyright
	uv run pytest -q

frontend-check:
	npm run lint
	npm run typecheck
	npm run build

format:
	uv run ruff format shared/scripts
	uv run ruff check --fix shared/scripts

format-check:
	uv run ruff format --check shared/scripts
	uv run ruff check shared/scripts

# Advisory: mutation-test the review gate and backlog parsers. The score is
# diagnostic, not a release gate; see docs/plans/mutation-testing-2026-11-21.md.
mutate:
	uv run --with "mutmut==3.8.1" mutmut run
	uv run --with "mutmut==3.8.1" mutmut results
