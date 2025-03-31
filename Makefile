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
	@echo "  clean       - Clean up generated files"
	@echo "               Options: --cache (also clear data cache)"
	@echo "  lint        - Run Python linter"
	@echo "               Options: --fix (auto-fix issues)"

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
	@if [ "$(findstring --cache,$(MAKECMDGOALS))" != "" ]; then \
		echo "Clearing data cache..."; \
		rm -rf cache/*; \
		mkdir -p cache; \
		echo "Cache cleared."; \
	fi

# Lint Python code
.PHONY: lint lint-fix
lint:
	@echo "Running Python linter..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Lint Check Log $(TIMESTAMP) ===" && \
	echo "Starting lint check at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	echo "Running linter in check-only mode..." && \
	ruff check .; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -ne 0 ]; then \
		echo ""; \
		echo "Linting issues found. To automatically fix issues, run:"; \
		echo "  make lint-fix"; \
	fi; \
	exit $$EXIT_CODE) 2>&1) | tee $(LOGS_DIR)/lint_$(TIMESTAMP).log
	@echo "Lint check log saved to: $(LOGS_DIR)/lint_$(TIMESTAMP).log"

lint-fix:
	@echo "Running Python linter with auto-fix..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@mkdir -p $(LOGS_DIR)
	@(echo "=== Lint Fix Log $(TIMESTAMP) ===" && \
	echo "Starting lint fix at: $$(date)" && \
	(source $(VENV_DIR)/bin/activate && \
	echo "Running linter with auto-fix enabled..." && \
	ruff check --fix .) 2>&1) | tee $(LOGS_DIR)/lint_$(TIMESTAMP).log
	@echo "Lint fix log saved to: $(LOGS_DIR)/lint_$(TIMESTAMP).log"

# Allow --sample and --cache as targets without actions
.PHONY: --sample --cache
--sample:
--cache:

%:
	@: 