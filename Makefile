.DEFAULT_GOAL := help
PKG = clfd
PKG_DIR = clfd
TESTS_DIR = ${PKG_DIR}/tests

# NOTE: -e installs in "Development Mode"
# See: https://packaging.python.org/tutorials/installing-packages/

dist: clean ## Build source distributions
	python setup.py sdist

install: ## Install the package
	pip install -e .

# NOTE: remove the .egg-info directory
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

tests: ## Run unit tests
	python -m unittest discover ${TESTS_DIR}

.PHONY: dist install uninstall help clean tests
