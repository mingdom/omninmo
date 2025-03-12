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
	@echo "  install     - Install dependencies"
	@echo "  train       - Train the model (now uses v2 by default)"
	@echo "  train-sample - Train the model using sample data (uses v2)"
	@echo "  predict     - Run predictions using console app (uses watchlist from config)"
	@echo "  predict-ticker - Predict rating for a specific ticker (usage: make predict-ticker TICKER=AAPL)"
	@echo "  clean       - Clean up generated files"
	@echo "  clear-cache - Clear the data cache"
	@echo "  pipeline    - Run the full pipeline (training and prediction)"
	@echo "  executable  - Make all scripts executable"

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

# Train the model (using v2)
.PHONY: train
train: clear-cache
	@echo "Training the model (v2)..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_train.py

# Train the model using sample data (using v2)
.PHONY: train-sample
train-sample: clear-cache
	@echo "Training the model using sample data (v2)..."
	@source $(VENV_DIR)/bin/activate && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_train.py --force-sample

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
	$(PYTHON) $(SCRIPTS_DIR)/v2_train.py --force-sample && \
	$(PYTHON) $(SCRIPTS_DIR)/v2_predict.py --sample

# Make all scripts executable
.PHONY: executable
executable:
	@echo "Making all scripts executable..."
	@bash $(SCRIPTS_DIR)/make_executable.sh
	@chmod +x $(SCRIPTS_DIR)/v2_predict.py
	@chmod +x $(SCRIPTS_DIR)/v2_train.py 