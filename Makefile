.PHONY: install-uv deps test test-integration lint fix

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

deps:
	uv sync --extra dev

test:
	uv run python -m pytest mtgengine/ -v --cov=mtgengine --cov-report=term-missing

test-integration:
	uv run python -m pytest mtgengine/server/tests/test_end_to_end.py -v -m integration --no-cov -o addopts=''

lint:
	ruff check mtgengine
	mypy --ignore-missing-imports --pretty mtgengine

fix:
	ruff check --fix mtgengine
	black --fast mtgengine
