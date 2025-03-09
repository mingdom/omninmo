# Makefile for omninmo project

# Variables
SHELL := /bin/bash
PYTHON := python3
VENV_DIR := venv
SCRIPTS_DIR := scripts
TESTS_DIR := tests

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  env         - Set up and activate a virtual environment"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests"
	@echo "  train       - Train the model (now uses XGBoost by default)"
	@echo "  train-sample - Train the model using sample data (uses XGBoost)"
	@echo "  run         - Run the Streamlit app (uses real data by default)"
	@echo "  run-sample  - Run the Streamlit app with generated sample data (use when Yahoo Finance API has issues)"
	@echo "  predict     - Predict rating for a ticker (usage: make predict TICKER=AAPL)"
	@echo "  clean       - Clean up generated files"
	@echo "  clear-cache - Clear the data cache"
	@echo "  pipeline    - Run the full pipeline (tests, training, prediction)"
	@echo "  executable  - Make all scripts executable"
	@echo "  maintain    - Run model maintenance (usage: make maintain MODE=daily|weekly|monthly)"
	@echo "  maintain-daily   - Run daily model update"
	@echo "  maintain-weekly  - Run weekly model retraining"
	@echo "  maintain-monthly - Run monthly model evaluation"
	@echo "  compare-models - Compare Random Forest and XGBoost models"

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
	@echo "Installation complete!"

# Clear the data cache
.PHONY: clear-cache
clear-cache:
	@echo "Clearing data cache..."
	@rm -rf cache/*
	@mkdir -p cache
	@echo "Cache cleared."

# Train the model (now uses XGBoost by default)
.PHONY: train
train: clear-cache
	@echo "Training the XGBoost model (default)..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/train_xgboost_model.py

# Train the model using sample data
.PHONY: train-sample
train-sample: clear-cache
	@echo "Training the XGBoost model using sample data..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/train_xgboost_model.py --force-sample

# Run the Streamlit app
.PHONY: run
run:
	@echo "Running the Streamlit app..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/run_app.py

# Run the Streamlit app with sample data
.PHONY: run-sample
run-sample:
	@echo "Running the Streamlit app with sample data..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/run_app.py --sample-data

# Predict rating for a ticker
.PHONY: predict
predict:
	@if [ -z "$(TICKER)" ]; then \
		echo "Error: TICKER is not set. Usage: make predict TICKER=AAPL"; \
		exit 1; \
	fi
	@echo "Predicting rating for $(TICKER)..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/predict_ticker.py $(TICKER)

# Clean up generated files
.PHONY: clean
clean:
	@echo "Cleaning up generated files..."
	@bash $(SCRIPTS_DIR)/clean.sh

# Run the full pipeline
.PHONY: pipeline
pipeline:
	@echo "Running the full pipeline..."
	@source $(VENV_DIR)/bin/activate && \
	bash $(SCRIPTS_DIR)/run-pipeline.sh

# Make all scripts executable
.PHONY: executable
executable:
	@echo "Making all scripts executable..."
	@bash $(SCRIPTS_DIR)/make_executable.sh
	@chmod +x $(TESTS_DIR)/run_tests.py

# Model maintenance targets
.PHONY: maintain
maintain:
	@if [ -z "$(MODE)" ]; then \
		echo "Error: MODE parameter is required. Use 'make maintain MODE=daily|weekly|monthly'"; \
		exit 1; \
	fi
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode $(MODE)

maintain-daily:
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode daily

maintain-weekly:
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode weekly

maintain-monthly:
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode monthly

# Model comparison target
.PHONY: compare-models
compare-models:
	@echo "Comparing Random Forest and XGBoost models..."
	@source $(VENV_DIR)/bin/activate && \
	if [ -n "$(TICKERS)" ]; then \
		$(PYTHON) $(SCRIPTS_DIR)/compare_models.py --tickers $(TICKERS) --period $(PERIOD); \
	else \
		$(PYTHON) $(SCRIPTS_DIR)/compare_models.py; \
	fi
	@echo "Comparison complete. Results saved to model_comparison directory."
	@echo "Summary:"
	@cat model_comparison/comparison_timestamp.txt

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Please run 'make env' first."; \
		exit 1; \
	fi
	@if [ -f activate-venv.sh ]; then source activate-venv.sh; fi
	@$(PYTHON) -m pytest $(TESTS_DIR) -v
	@echo "Tests completed." 