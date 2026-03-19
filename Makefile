PACKAGE_NAME = dj_cache_panel
PYPI_REPO ?= pypi   # can be 'testpypi' or 'pypi'

.PHONY: help clean build publish test install test_docker_all test_docker_all_clean

help:
	@echo "Makefile targets:"
	@echo "  make clean           		Remove build artifacts"
	@echo "  make build           		Build sdist and wheel (in ./dist)"
	@echo "  make install_requirements 	Install all dev dependencies"
	@echo "  make install         		Install dependencies and package (use INSTALL_VALKEY=true for valkey)"
	@echo "  make uninstall       		Uninstall package"
	@echo "  make uninstall_all   		Uninstall all packages"
	@echo "  make test_install    		Check if package can be imported"
	@echo "  make test_docker           Run tests inside Docker dev container"
	@echo "  make test_docker_all       Run tests on full matrix (Python 3.9-3.14, Django 4.2/5.2/6.0, ±Valkey)"
	@echo "  make test_docker_all_clean Clean test matrix results"
	@echo "  make test_local            Run tests inside local environment"
	@echo "  make test_coverage   		Run tests with coverage report"
	@echo "  make coverage_html   		Generate HTML coverage report"
	@echo "  make publish         		Publish package to PyPI"
	@echo "  make docs            		Build documentation"
	@echo "  make docs_serve      		Serve documentation locally"
	@echo "  make docs_push       		Deploy documentation to GitHub Pages"
	@echo "  make docker_up       		Start all Docker services (dev, Redis, cluster)"
	@echo "  make docker_down     		Stop all Docker services and clean volumes"
	@echo "  make docker_shell    		Open shell in dev container"
	@echo ""
	@echo "Environment variables:"
	@echo "  INSTALL_VALKEY=true  		Install django-valkey (requires Python 3.10+)"
	@echo "  PYTHON_VERSION       		Set Python version for Docker (default: 3.10)"
	@echo "  FILTER_PYTHON        		Filter test matrix by Python version(s) (e.g., '3.10 3.11')"
	@echo "  FILTER_DJANGO        		Filter test matrix by Django version(s) (e.g., '4.2 6.0')"
	@echo "  FILTER_VALKEY        		Filter test matrix by Valkey (true/false)"
	@echo ""
	@echo "Examples:"
	@echo "  make install                            # Install base package"
	@echo "  INSTALL_VALKEY=true make install        # Install with valkey support"
	@echo "  PYTHON_VERSION=3.11 make test_docker    # Test with Python 3.11"
	@echo "  INSTALL_VALKEY=true make test_docker    # Test with valkey support"
	@echo "  make test_docker_all                    # Run full test matrix (25 combinations)"
	@echo "  FILTER_PYTHON=3.12 make test_docker_all # Test only Python 3.12"
	@echo "  FILTER_DJANGO=6.0 make test_docker_all  # Test only Django 6.0"

clean:
	rm -rf build dist *.egg-info

build: clean
	python -m build

install_requirements:
	python -m pip install -r requirements.txt

install: install_requirements
	@if [ "$(INSTALL_VALKEY)" = "true" ] && python -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then \
		echo "Installing with valkey support (Python 3.10+)..."; \
		python -m pip install -e .[dev,valkey]; \
	else \
		echo "Installing base package (valkey not available or Python < 3.10)..."; \
		python -m pip install -e .[dev]; \
	fi

uninstall:
	python -m pip uninstall -y $(PACKAGE_NAME) || true

uninstall_all:
	python -m pip uninstall -y $(PACKAGE_NAME) || true
	python -m pip uninstall -y -r requirements.txt || true
	@echo "All packages in requirements.txt uninstalled"
	@echo "Note that some dependent packages may still be installed"
	@echo "To uninstall all packages, run 'pip freeze | xargs pip uninstall -y'"
	@echo "Do this at your own risk. Use a python virtual environment always."

test_install: build
	python -m pip uninstall -y $(PACKAGE_NAME) || true
	python -m pip install -e .
	python -c "import dj_cache_panel; print('✅ Import success!')"

test_local:
	@echo "Running tests in local environment..."
	@python -m pytest tests/ -v
	@echo "✅ Tests completed"

test_docker:
	@echo "Starting Docker services with PYTHON_VERSION=$${PYTHON_VERSION:-3.10} and INSTALL_VALKEY=$${INSTALL_VALKEY:-false}"
	PYTHON_VERSION=$${PYTHON_VERSION:-3.10} INSTALL_VALKEY=$${INSTALL_VALKEY:-false} docker compose build
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Running tests in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis VALKEY_HOST=valkey MEMCACHED_HOST=memcached python -m pytest tests/ -v"
	@echo "✅ Tests completed"

test_coverage:
	@echo "Running tests with coverage"
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 3
	@echo "Running all tests in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis VALKEY_HOST=valkey MEMCACHED_HOST=memcached python -m pytest --cov=dj_cache_panel --cov-report=xml --cov-report=html --cov-report=term-missing tests/"
	@echo "✅ All tests completed"

test_docker_all:
	@mkdir -p test-results
	@docker compose up -d
	@sleep 3
	@echo "🚀 Starting full test matrix (Python 3.9-3.14, Django 4.2/5.2/6.0, ±Valkey)"
	@echo ""
	@bash -c '\
	passed=0; failed=0; total=0; skipped=0; \
	for py in 3.9 3.10 3.11 3.12 3.13 3.14; do \
	  if [ -n "$(FILTER_PYTHON)" ] && ! echo "$(FILTER_PYTHON)" | grep -qw "$$py"; then continue; fi; \
	  for dj in 4.2 5.2 6.0; do \
	    if [ -n "$(FILTER_DJANGO)" ] && ! echo "$(FILTER_DJANGO)" | grep -qw "$$dj"; then continue; fi; \
	    for valkey in false true; do \
	      if [ -n "$(FILTER_VALKEY)" ] && [ "$(FILTER_VALKEY)" != "$$valkey" ]; then continue; fi; \
	      skip=0; \
	      if [ "$$py" = "3.9" ] && ([ "$$dj" != "4.2" ] || [ "$$valkey" = "true" ]); then skip=1; fi; \
	      if [ "$$py" = "3.14" ] && [ "$$dj" = "4.2" ]; then skip=1; fi; \
	      if [ "$$py" = "3.10" ] && [ "$$dj" = "6.0" ]; then skip=1; fi; \
	      if [ "$$py" = "3.11" ] && [ "$$dj" = "6.0" ]; then skip=1; fi; \
	      if [ "$$dj" = "5.2" ] && [ "$$py" = "3.9" ]; then skip=1; fi; \
	      if [ $$skip -eq 1 ]; then skipped=$$((skipped + 1)); continue; fi; \
	      total=$$((total + 1)); combo="py$$py-dj$$dj-valkey$$valkey"; logfile="test-results/$$combo.log"; \
	      printf "  [$$total] Testing $$combo... "; \
	      if docker build -q --build-arg PYTHON_VERSION=$$py --build-arg DJANGO_VERSION=$$dj --build-arg INSTALL_VALKEY=$$valkey -f example_project/Dockerfile -t dj-cache-test:$$combo . > /tmp/$$combo.build 2>&1 && \
	      docker run --rm --network dj-cache-panel_default \
	        -e REDIS_HOST=redis -e VALKEY_HOST=valkey -e MEMCACHED_HOST=memcached -e POSTGRES_HOST=postgres \
	        dj-cache-test:$$combo bash -c "cd /app && python -m pytest tests/ -v" > $$logfile 2>&1; then \
	        echo "✅ PASSED"; passed=$$((passed + 1)); \
	        rm -f /tmp/$$combo.build; \
	      else \
	        echo "❌ FAILED"; failed=$$((failed + 1)); \
	        if [ -f /tmp/$$combo.build ]; then cat /tmp/$$combo.build >> $$logfile; rm -f /tmp/$$combo.build; fi; \
	      fi; \
	    done; \
	  done; \
	done; \
	echo ""; echo "═════════════════════════════════════════════════════"; \
	echo "Test Matrix Summary"; echo "═════════════════════════════════════════════════════"; \
	echo "Total tested: $$total  |  Passed: $$passed  |  Failed: $$failed  |  Skipped: $$skipped"; \
	echo "═════════════════════════════════════════════════════"; \
	{ echo "Results: test-results/"; echo "Total: $$total, Passed: $$passed, Failed: $$failed, Skipped: $$skipped"; } > test-results/summary.txt; \
	if [ $$failed -gt 0 ]; then exit 1; fi; \
	'

test_docker_all_clean:
	@echo "Cleaning test matrix results..."
	@rm -rf test-results/
	@docker image ls --filter=reference='dj-cache-test:*' -q | xargs -r docker rmi -f
	@echo "✅ Cleaned"

coverage_html: test_coverage
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "Open htmlcov/index.html in your browser to view the detailed report"

publish:
	twine upload --repository $(PYPI_REPO) dist/*

docs: install
	mkdocs build

docs_serve:
	mkdocs serve

docs_push: docs
	mkdocs gh-deploy --force

# Docker targets
docker_up:
	@echo "Starting all Docker services..."
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "✅ All services are running:"
	@echo "   Dev container: dj-cache-panel-dev-1"
	@echo ""
	@echo "Run 'make docker_shell' to open a shell in the dev container"

docker_down:
	@echo "Stopping all Docker services and cleaning volumes..."
	@docker compose down -v
	@echo "✅ All services stopped and volumes cleaned"

docker_shell:
	@echo "Opening shell in dev container..."
	@docker compose exec dev bash
