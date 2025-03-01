# Makefile for omninmo project

# Variables
SHELL := /bin/bash
PYTHON := python3
PIP := pip3
SCRIPTS_DIR := scripts

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  env         - Set up a virtual environment"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests"
	@echo "  test-app    - Test the application components"
	@echo "  test-watchlist - Test the watch list functionality"
	@echo "  train       - Train the model (now uses XGBoost by default)"
	@echo "  train-rf    - Train the Random Forest model (legacy)"
	@echo "  train-xgb   - Train the XGBoost model"
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
	@echo "  test-model     - Run a simple test of the XGBoost model"
	@echo "  verify-model   - Verify the current model type and configuration"

# Set up virtual environment
.PHONY: env
env:
	@echo "Setting up virtual environment..."
	@bash $(SCRIPTS_DIR)/setup-venv.sh

# Install dependencies
.PHONY: install
install:
	@echo "Installing dependencies..."
	@bash $(SCRIPTS_DIR)/install-reqs.sh

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	@$(PYTHON) $(SCRIPTS_DIR)/run_tests.py

# Test the application components
.PHONY: test-app
test-app:
	@echo "Testing application components..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_app.py

# Test the watch list functionality
.PHONY: test-watchlist
test-watchlist:
	@echo "Testing watch list functionality..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_watchlist.py

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
	@$(PYTHON) $(SCRIPTS_DIR)/train_xgboost_model.py

# Train the Random Forest model (legacy)
.PHONY: train-rf
train-rf: clear-cache
	@echo "Training the Random Forest model (legacy)..."
	@$(PYTHON) $(SCRIPTS_DIR)/train_model.py --model-path models/random_forest_predictor.pkl

# Train the XGBoost model
.PHONY: train-xgb
train-xgb: clear-cache
	@echo "Training the XGBoost model..."
	@$(PYTHON) $(SCRIPTS_DIR)/train_xgboost_model.py

# Train the model using sample data
.PHONY: train-sample
train-sample: clear-cache
	@echo "Training the XGBoost model using sample data..."
	@$(PYTHON) $(SCRIPTS_DIR)/train_xgboost_model.py --force-sample

# Run the Streamlit app
.PHONY: run
run:
	@echo "Running the Streamlit app..."
	@$(PYTHON) $(SCRIPTS_DIR)/run_app.py

# Run the Streamlit app with sample data
.PHONY: run-sample
run-sample:
	@echo "Running the Streamlit app with sample data..."
	@$(PYTHON) $(SCRIPTS_DIR)/run_app.py --sample-data

# Predict rating for a ticker
.PHONY: predict
predict:
	@if [ -z "$(TICKER)" ]; then \
		echo "Error: TICKER is not set. Usage: make predict TICKER=AAPL"; \
		exit 1; \
	fi
	@echo "Predicting rating for $(TICKER)..."
	@$(PYTHON) $(SCRIPTS_DIR)/predict_ticker.py $(TICKER)

# Clean up generated files
.PHONY: clean
clean:
	@echo "Cleaning up generated files..."
	@bash $(SCRIPTS_DIR)/clean.sh

# Run the full pipeline
.PHONY: pipeline
pipeline:
	@echo "Running the full pipeline..."
	@bash $(SCRIPTS_DIR)/run-pipeline.sh

# Make all scripts executable
.PHONY: executable
executable:
	@echo "Making all scripts executable..."
	@bash $(SCRIPTS_DIR)/make_executable.sh

# Model maintenance targets
.PHONY: maintain
maintain:
	@if [ -z "$(MODE)" ]; then \
		echo "Error: MODE parameter is required. Use 'make maintain MODE=daily|weekly|monthly'"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode $(MODE)

maintain-daily:
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode daily

maintain-weekly:
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode weekly

maintain-monthly:
	$(PYTHON) $(SCRIPTS_DIR)/maintain_model.py --mode monthly

# Model comparison target
.PHONY: compare-models
compare-models:
	@echo "Comparing Random Forest and XGBoost models..."
	@if [ -n "$(TICKERS)" ]; then \
		$(PYTHON) $(SCRIPTS_DIR)/compare_models.py --tickers $(TICKERS) --period $(PERIOD); \
	else \
		$(PYTHON) $(SCRIPTS_DIR)/compare_models.py; \
	fi
	@echo "Comparison complete. Results saved to model_comparison directory."
	@echo "Summary:"
	@cat model_comparison/comparison_timestamp.txt

# Simple model test target
.PHONY: test-model
test-model:
	@echo "Running simple model test..."
	$(PYTHON) $(SCRIPTS_DIR)/simple_model_test.py
	@echo "Test complete."

# Verify model target
.PHONY: verify-model
verify-model:
	@echo "Verifying model type and configuration..."
	$(PYTHON) $(SCRIPTS_DIR)/verify_model.py
	@echo "Verification complete."

# Additional targets for specific test cases
.PHONY: test-imports
test-imports:
	@echo "Testing imports..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_imports.py

.PHONY: test-trainer
test-trainer:
	@echo "Testing trainer..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_trainer.py 