.DEFAULT_GOAL := help
PKG = clfd
PKG_DIR = clfd
LINE_LENGTH = 100
TESTS_DIR = tests/

dist: clean ## Build source distributions
	python -m build --sdist

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

clean: ## Remove all python cache and build files
	find . -type f -name "*.o" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf clfd.egg-info/

upload_test: ## Upload the distribution source to the TEST PyPI
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: ## Upload the distribution source to the REAL PyPI
	twine upload dist/*

lint: ## Run linting
	isort --check-only --profile black --line-length ${LINE_LENGTH}  ${PKG_DIR}/
	flake8 --show-source --statistics --max-line-length ${LINE_LENGTH}  ${PKG_DIR}/
	black --exclude .+\.ipynb --check --line-length ${LINE_LENGTH}  ${PKG_DIR}/

format: ## Apply automatic formatting
	black --exclude .+\.ipynb --line-length ${LINE_LENGTH} ${PKG_DIR}/
	isort --profile black --line-length ${LINE_LENGTH} ${PKG_DIR}/

test: ## Run unit tests
	MPLBACKEND=Agg pytest -vv ${TESTS_DIR}

.PHONY: dist install uninstall help clean tests
