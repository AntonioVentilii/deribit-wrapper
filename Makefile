.PHONY: lint check-format format test docs all

format:
	ruff format .

check-format:
	ruff format --check .

lint:
	pylint deribit_wrapper

test:
	pytest --cov=deribit_wrapper --cov-report=term-missing

docs:
	pydocstyle deribit_wrapper

all: lint check-format test docs
