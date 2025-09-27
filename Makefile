.PHONY: lint check format test docs all

format:
	black .
	ruff format .

lint:
	pylint deribit_wrapper
	ruff check .

test:
	pytest

docs:
	pydocstyle

all: lint check format test docs
