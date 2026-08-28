.PHONY: lint typecheck check-format format test docs all

format:
	ruff format .

check-format:
	ruff format --check .

lint:
	pylint deribit_wrapper

typecheck:
	mypy

test:
	pytest --cov=deribit_wrapper --cov-report=term-missing

docs:
	pydocstyle deribit_wrapper

all: lint typecheck check-format test docs
