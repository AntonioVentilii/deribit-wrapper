.PHONY: lint check format test docs all

format:
	black .
	ruff format .

lint:
	pylint deribit_wrapper

test:
	pytest --cov=deribit_wrapper --cov-report=term-missing

docs:
	pydocstyle

all: lint check format test docs
