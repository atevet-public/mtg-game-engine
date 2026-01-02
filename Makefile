.PHONY: deps test lint fix

deps:
	uv pip install -e ".[dev]"

test:
	python -m pytest src/mtgengine/ -v --cov=src/mtgengine --cov-report=term-missing

lint:
	ruff check src/mtgengine
	mypy --ignore-missing-imports --pretty src/mtgengine

fix:
	ruff check --fix src/mtgengine
	black --fast src/mtgengine
