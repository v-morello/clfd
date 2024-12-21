.DEFAULT_GOAL := help
PKG = clfd
PKG_DIR = clfd/
LINE_LENGTH = 79
TESTS_DIR = tests/

install: ## Install the package in development mode
	pip install -e .[dev]

uninstall: ## Uninstall the package
	pip uninstall ${PKG}
	rm -rf ${PKG}.egg-info

# GLORIOUS hack to autogenerate Makefile help
# This simply parses the double hashtags that follow each Makefile command
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Print this help message
	@echo "Makefile help for clfd"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run linting
	isort --check-only --profile black --line-length ${LINE_LENGTH}  ${PKG_DIR}  ${TESTS_DIR}
	flake8 --show-source --statistics --max-line-length ${LINE_LENGTH}  ${PKG_DIR}  ${TESTS_DIR}
	black --exclude .+\.ipynb --check --line-length ${LINE_LENGTH}  ${PKG_DIR}  ${TESTS_DIR}

format: ## Apply automatic formatting
	black --exclude .+\.ipynb --line-length ${LINE_LENGTH} ${PKG_DIR}  ${TESTS_DIR}
	isort --profile black --line-length ${LINE_LENGTH} ${PKG_DIR}  ${TESTS_DIR}

test: ## Run unit tests
	MPLBACKEND=Agg pytest -vv --cov ${PKG_DIR}

.PHONY: install uninstall help lint format test
