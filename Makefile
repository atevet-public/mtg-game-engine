.PHONY: install-uv deps test lint fix

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

deps:
	uv pip install -e ".[dev]"

test:
	python -m pytest mtgengine/ -v --cov=mtgengine --cov-report=term-missing

lint:
	ruff check mtgengine
	mypy --ignore-missing-imports --pretty mtgengine

fix:
	ruff check --fix mtgengine
	black --fast mtgengine
