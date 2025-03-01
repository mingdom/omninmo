#!/bin/bash
# Script to run the full pipeline (tests, training, and prediction)

echo "Running the full omninmo pipeline..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Run tests
echo "Running tests..."
python3 "$PROJECT_ROOT/tests/run_tests.py"
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting pipeline."
    exit 1
fi

# Train model
echo "Training model..."
python3 "$SCRIPT_DIR/train_xgboost_model.py"
if [ $? -ne 0 ]; then
    echo "Model training failed. Aborting pipeline."
    exit 1
fi

# Test model specifically
echo "Testing model..."
python3 -m unittest tests.test_model_functionality.TestModelFunctionality
if [ $? -ne 0 ]; then
    echo "Model testing failed. Aborting pipeline."
    exit 1
fi

# Run prediction for a sample ticker
echo "Running prediction for AAPL..."
python3 "$SCRIPT_DIR/predict_ticker.py" AAPL

echo "Pipeline completed successfully!" 