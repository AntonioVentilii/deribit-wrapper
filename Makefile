.PHONY: lint check-format format test docs all

format:
	ruff format .

check-format:
	ruff format --check .

lint:
	pylint deribit_wrapper

test:
	pytest

docs:
	pydocstyle

all: lint check-format test docs
