# Convenience targets for local development.

PY ?= python
PIP ?= pip

.PHONY: install train score test test-unit test-integration validate drift api lint clean

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

train:
	$(PY) -m scripts.run_training

score:
	$(PY) -m scripts.run_batch_scoring --model catboost_churn

validate:
	$(PY) -m scripts.validate_data

drift:
	$(PY) -m scripts.run_drift_report --reference-date 2017-06-30 --current-date 2017-12-31

test:
	pytest

test-unit:
	pytest -m "not integration and not slow"

test-integration:
	pytest -m integration

api:
	uvicorn churn_ml.api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf artifacts mlruns .pytest_cache .coverage htmlcov **/__pycache__
