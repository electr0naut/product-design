.PHONY: check python-check frontend-check format format-check

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
