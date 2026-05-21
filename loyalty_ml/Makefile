# Convenience targets for local development.

PY ?= python
PIP ?= pip

.PHONY: install validate segment train-redemption train-uplift recommend api test test-unit test-integration clean

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

validate:
	$(PY) -m scripts.validate_data

segment:
	$(PY) -m scripts.run_segmentation

train-redemption:
	$(PY) -m scripts.run_redemption_training --trials 30

train-uplift:
	$(PY) -m scripts.run_uplift_training

recommend:
	$(PY) -m scripts.run_recommendations

api:
	uvicorn loyalty_ml.api.main:app --host 0.0.0.0 --port 8001 --reload

test:
	pytest

test-unit:
	pytest -m "not integration and not slow"

test-integration:
	pytest -m integration

clean:
	rm -rf artifacts mlruns .pytest_cache .coverage htmlcov **/__pycache__
