# Makefile for omninmo project

# Variables
SHELL := /bin/bash
PYTHON := python3
VENV_DIR := venv
SCRIPTS_DIR := scripts

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  env         - Set up and activate a virtual environment"
	@echo "  install     - Install dependencies and set script permissions"
	@echo "  train       - Train the model (use --sample for training with sample data)"
	@echo "  predict     - Run predictions using console app (uses watchlist from config)"
	@echo "  predict-ticker - Predict rating for a specific ticker (usage: make predict-ticker TICKER=AAPL)"
	@echo "  mlflow      - Start the MLflow UI to view training results (optional: make mlflow PORT=5001)"
	@echo "  clean       - Clean up generated files"
	@echo "               Options: --cache (also clear data cache)"

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
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) -m pip install --upgrade pip && \
	bash $(SCRIPTS_DIR)/install-reqs.sh
	@echo "Setting script permissions..."
	@chmod +x $(SCRIPTS_DIR)/*.sh
	@chmod +x $(SCRIPTS_DIR)/*.py
	@echo "Installation complete!"

# Train the model
.PHONY: train
train:
	@echo "Training the model..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_train.py $(if $(findstring --sample,$(MAKECMDGOALS)),--force-sample,)

# Run predictions on watchlist
.PHONY: predict
predict:
	@echo "Running predictions on watchlist..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_predict.py

# Predict rating for a ticker
.PHONY: predict-ticker
predict-ticker:
	@if [ -z "$(TICKER)" ]; then \
		echo "Error: TICKER is not set. Usage: make predict-ticker TICKER=AAPL"; \
		exit 1; \
	fi
	@echo "Predicting rating for $(TICKER)..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_predict.py --tickers $(TICKER)

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

# Allow --sample and --cache as targets without actions
.PHONY: --sample --cache
--sample:
--cache: 