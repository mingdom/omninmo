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
	@echo "  train       - Train the model"
	@echo "  train-sample - Train the model using sample data"
	@echo "  run         - Run the Streamlit app"
	@echo "  run-sample  - Run the Streamlit app with sample data"
	@echo "  predict     - Predict rating for a ticker (usage: make predict TICKER=AAPL)"
	@echo "  clean       - Clean up generated files"
	@echo "  clear-cache - Clear the data cache"
	@echo "  pipeline    - Run the full pipeline (tests, training, prediction)"
	@echo "  executable  - Make all scripts executable"

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

# Clear the data cache
.PHONY: clear-cache
clear-cache:
	@echo "Clearing data cache..."
	@rm -rf cache/*
	@mkdir -p cache
	@echo "Cache cleared."

# Train the model
.PHONY: train
train: clear-cache
	@echo "Training the model..."
	@$(PYTHON) $(SCRIPTS_DIR)/train_model.py

# Train the model using sample data
.PHONY: train-sample
train-sample: clear-cache
	@echo "Training the model using sample data..."
	@$(PYTHON) $(SCRIPTS_DIR)/train_model.py --force-sample

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

# Additional targets for specific test cases
.PHONY: test-imports
test-imports:
	@echo "Testing imports..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_imports.py

.PHONY: test-trainer
test-trainer:
	@echo "Testing trainer..."
	@$(PYTHON) $(SCRIPTS_DIR)/test_trainer.py 