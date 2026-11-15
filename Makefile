PYTHON ?= .venv/bin/python

.PHONY: db-init db-reset test

db-init:
	$(PYTHON) -m api.db

db-reset:
	$(PYTHON) -m api.db --reset

test:
	$(PYTHON) -m unittest discover -s api/tests
