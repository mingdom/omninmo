# Makefile for omninmo project

# Variables
SHELL := /bin/bash
PYTHON := python3
VENV_DIR := venv
SCRIPTS_DIR := scripts
LOGS_DIR := logs
SRC_DIR := src.v2
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)
PORT := 5000

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  env         - Set up and activate a virtual environment"
	@echo "  install     - Install dependencies and set script permissions"
	@echo "  train       - Train the model (use --sample for training with sample data)"
	@echo "  predict     - Run predictions using console app (usage: make predict [NVDA])"
	@echo "  mlflow      - Start the MLflow UI to view training results (optional: make mlflow PORT=5001)"
	@echo "  folio       - Start the portfolio dashboard with debug mode enabled"
	@echo "               Options: portfolio=path/to/file.csv (use custom portfolio file)"
	@echo "  portfolio   - Start the portfolio dashboard with sample portfolio and debug mode"
	@echo "  clean       - Clean up generated files and caches"
	@echo "               Options: --cache (also clear data cache)"
	@echo "  lint        - Run type checker and linter"
	@echo "               Options: --fix (auto-fix linting issues)"
	@echo "  test        - Run all tests in the tests directory"
	@echo "  integration-test - Run integration tests that require external API access"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run the Docker container"
	@echo "  docker-up    - Start the application with docker-compose"
	@echo "  docker-down  - Stop the docker-compose services"
	@echo "  docker-logs  - Tail the Docker logs"
	@echo "  docker-test  - Run tests in a Docker container"

# Set up virtual environment
.PHONY: env
env:
	@echo "Setting up virtual environment..."
	@bash $(SCRIPTS_DIR)/setup-venv.sh
	@echo "Activating virtual environment..."
	@echo "NOTE: To use the virtual environment in your current shell, run: source activate-venv.sh"
	@echo "The virtual environment will be automatically activated for all make commands."

# Install dependencies
.PHONY: install
install:
	@echo "Installing dependencies..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Installation Log $(TIMESTAMP) ===" && \
	echo "Starting installation at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	$(PYTHON) -m pip install --upgrade pip && \
	bash $(SCRIPTS_DIR)/install-reqs.sh) 2>&1 && \
	echo "Setting script permissions..." && \
	chmod +x $(SCRIPTS_DIR)/*.sh && \
	chmod +x $(SCRIPTS_DIR)/*.py && \
	echo "Installation complete at: $$(date)") | tee $(LOGS_DIR)/install_$(TIMESTAMP).log
	@echo "Installation log saved to: $(LOGS_DIR)/install_$(TIMESTAMP).log"

# Train the model
.PHONY: train
train:
	@echo "Training the model..."
	@source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. $(PYTHON) -m $(SRC_DIR).train $(if $(findstring --sample,$(MAKECMDGOALS)),--force-sample,)

# Run predictions
.PHONY: predict
predict:
	@echo "Running predictions..."
	@source $(VENV_DIR)/bin/activate && \
	if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		TICKERS=$$(echo "$(filter-out $@,$(MAKECMDGOALS))" | tr ',' ' '); \
		echo "Predicting for: $$TICKERS"; \
		PYTHONPATH=. $(PYTHON) -m $(SRC_DIR).console_app --tickers $$TICKERS; \
	else \
		echo "Running predictions on watchlist..."; \
		PYTHONPATH=. $(PYTHON) -m $(SRC_DIR).console_app; \
	fi

# Start the MLflow UI
.PHONY: mlflow
mlflow:
	@echo "Starting MLflow UI on http://127.0.0.1:$(PORT)..."
	@echo "Press Ctrl+C to stop the server."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/run_mlflow.py $(if $(PORT),--port $(PORT),)

# Clean up generated files
.PHONY: clean
clean:
	@echo "Cleaning up generated files..."
	@bash $(SCRIPTS_DIR)/clean.sh
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@if [ "$(findstring --cache,$(MAKECMDGOALS))" != "" ]; then \
		echo "Clearing data cache..."; \
		rm -rf cache/*; \
		mkdir -p cache; \
		echo "Cache cleared."; \
	fi

# Lint Python code
.PHONY: lint
lint:
	@echo "Running linter (ruff)..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Code Check Log $(TIMESTAMP) ===" && \
	echo "Starting checks at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	echo "Running linter (ruff)..." && \
	ruff check --fix --unsafe-fixes .) \
	2>&1) | tee $(LOGS_DIR)/code_check_latest.log
	@echo "Check log saved to: $(LOGS_DIR)/code_check_latest.log"

# Allow --fix as target without actions
.PHONY: --fix
--fix:

# Lab Projects
.PHONY: portfolio folio stop-folio port

# Docker targets
.PHONY: docker-build docker-run docker-up docker-down docker-logs docker-compose-up docker-compose-down docker-test deploy-hf

portfolio:
	@echo "Starting portfolio dashboard with sample portfolio.csv and debug mode..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. python3 -m src.folio.app --port 8051 --debug --portfolio src/folio/assets/sample-portfolio.csv

port:
	@echo "Running portfolio analysis..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. python3 src/lab/portfolio.py "$(if $(csv),$(csv),src/folio/assets/sample-portfolio.csv)"

folio:
	@echo "Starting portfolio dashboard with debug mode..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. python3 -m src.folio.app --port 8051 --debug $(if $(portfolio),--portfolio $(portfolio),)

stop-folio:
	@echo "Stopping portfolio dashboard..."
	@PIDS=$$(ps aux | grep "[p]ython.*folio" | awk '{print $$2}'); \
	if [ -n "$$PIDS" ]; then \
		echo "Found folio processes with PIDs: $$PIDS"; \
		for PID in $$PIDS; do \
			echo "Killing process $$PID..."; \
			kill -9 $$PID 2>/dev/null || echo "Failed to kill process $$PID (might require sudo)"; \
		done; \
		echo "All folio processes have been terminated."; \
	else \
		echo "No running folio processes found."; \
	fi

# Test targets
.PHONY: test integration-test
test:
	@echo "Running tests..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Test Run Log $(TIMESTAMP) ===" && \
	echo "Starting tests at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. pytest tests/ -v) 2>&1) | tee $(LOGS_DIR)/test_latest.log
	@echo "Test log saved to: $(LOGS_DIR)/test_latest.log"

# Integration test target
integration-test:
	@echo "Running integration tests..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Integration Test Run Log $(TIMESTAMP) ===" && \
	echo "Starting integration tests at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	PYTHONPATH=. pytest tests/integration/ -v) 2>&1) | tee $(LOGS_DIR)/integration_test_latest.log
	@echo "Integration test log saved to: $(LOGS_DIR)/integration_test_latest.log"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build --debug -t folio:latest .

# Run the Docker container
docker-run:
	@echo "Running Docker container..."
	docker run -p 8050:8050 --env-file .env folio:latest

# Start with docker-compose
docker-up:
	@echo "Starting with docker-compose..."
	docker-compose up -d
	@echo "Folio app launched successfully!"
	@echo "Access the app at: http://localhost:8050"

# Stop docker-compose services
docker-down:
	@echo "Stopping docker-compose services..."
	docker-compose down

# Alias for backward compatibility
docker-compose-up: docker-up
docker-compose-down: docker-down

# Tail Docker logs
docker-logs:
	@echo "Tailing Docker logs..."
	docker-compose logs -f

# Run tests in Docker container
docker-test:
	@echo "Running tests in Docker container..."
	@if [ -z "$$GEMINI_API_KEY" ]; then \
		echo "Warning: GEMINI_API_KEY environment variable not set. Some tests may fail."; \
	fi
	@docker-compose -f docker-compose.test.yml build --build-arg INSTALL_DEV=true
	@docker-compose -f docker-compose.test.yml run --rm folio

# Deploy to Hugging Face Spaces
deploy-hf:
	@echo "Deploying to Hugging Face Spaces..."
	@echo "Checking for Git LFS..."
	@if ! command -v git-lfs &> /dev/null; then \
		echo "Error: Git LFS is not installed. Please install it first."; \
		echo "  macOS: brew install git-lfs"; \
		echo "  Linux: apt-get install git-lfs"; \
		exit 1; \
	fi
	@echo "Checking if Hugging Face Space remote exists..."
	@if ! git remote | grep -q "space"; then \
		echo "Adding Hugging Face Space remote..."; \
		git remote add space git@huggingface.co:mingdom/folio; \
	fi
	@echo "Ensuring Git LFS is tracking .pkl files..."
	@grep -q "*.pkl filter=lfs diff=lfs merge=lfs -text" .gitattributes || \
		echo "*.pkl filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
	@echo "Initializing Git LFS..."
	@git lfs install
	@echo "Pushing to Hugging Face Space..."
	@git push space main:main
	@echo "\n✅ Deployment to Hugging Face Space completed!"
	@echo "Your application is now available at: https://huggingface.co/spaces/mingdom/folio"

%:
	@:
