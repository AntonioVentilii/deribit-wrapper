.PHONY: lint check format test docs all

lint:
	pylint deribit_wrapper
	ruff check .

check:
	pyflakes

format:
	black .
	ruff format .

test:
	pytest

docs:
	pydocstyle

all: lint check format test docs
