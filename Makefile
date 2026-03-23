.PHONY: install test lint format security-scan synth diff deploy clean sample setup-secrets help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (Lambda + dev + infra)
	pip install -r requirements-dev.txt
	cd infra && pip install -r requirements.txt

test: ## Run pytest suite
	python -m pytest tests/ -v --tb=short

lint: ## Run ruff linter
	ruff check lambda/ tests/

format: ## Auto-format code with ruff
	ruff format lambda/ tests/
	ruff check --fix lambda/ tests/

security-scan: ## Run bandit security scanner
	bandit -r lambda/ -ll

synth: ## CDK synthesize (preview CloudFormation template)
	cd infra && cdk synth

diff: ## CDK diff (preview infrastructure changes)
	cd infra && cdk diff

deploy: ## CDK deploy to AWS
	cd infra && cdk deploy

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf cdk.out .cdk.staging htmlcov .coverage samples/

sample: ## Generate a sample post locally (no API keys needed)
	python scripts/generate_sample.py

setup-secrets: ## Create AWS Secrets Manager entries (interactive)
	bash scripts/setup_secrets.sh
