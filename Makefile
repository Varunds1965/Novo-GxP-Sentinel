.DEFAULT_GOAL := help
PY := python3
export PYTHONPATH := backend

help: ## Show available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

test: ## Run the whole suite with no model present
	$(PY) -m unittest discover -s tests -p 'test_*.py' -t .

seed: ## Rebuild the local evidence store from the corpus
	$(PY) scripts/seed_demo.py

selftest: ## Offline readiness self-test
	$(PY) scripts/offline_self_test.py

sweep: ## Evaluate all 350 audit controls and print the readiness indicator
	$(PY) scripts/run_assessment.py

lint: ## Lint and format check (requires dev extras)
	ruff format --check . && ruff check .

types: ## Strict type check (requires dev extras)
	mypy backend/app

arch: ## Enforce layering contracts (requires dev extras)
	lint-imports --config backend/pyproject.toml

verify: test selftest ## Everything CI enforces that needs no extra packages
	@echo "verify: OK"

.PHONY: help test seed selftest sweep lint types arch verify
