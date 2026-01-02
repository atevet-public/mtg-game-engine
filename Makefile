.PHONY: deps test

deps:
	uv pip install -e ".[dev]"

test:
	python -m pytest src/mtgengine/ -v --cov=src/mtgengine --cov-report=term-missing
