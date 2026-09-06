.PHONY: setup pipeline dashboard

VENV := .venv
PYTHON := $(VENV)/bin/python

# Installs all dependencies: a Python venv for the backend, npm packages for
# the frontend. Idempotent -- safe to re-run.
setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

# Runs the pipeline end-to-end: (re)creates the schema via Alembic and loads
# data/cell-count.csv into teiko.db. Safe to re-run -- load_data.py wipes and
# reloads the three tables each time.
pipeline:
	$(PYTHON) load_data.py

# Builds the frontend and starts the single server (FastAPI, serving both
# /api/* and the built frontend) that presents the dashboard. Runs in the
# foreground so Codespaces can forward the port while it's up.
dashboard:
	cd frontend && npm run build
	$(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
