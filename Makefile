.PHONY: install test run

install:
	poetry install

test:
	poetry run python -m unittest discover -v

run:
	poetry run python api.py