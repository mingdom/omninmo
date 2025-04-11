# Folio Playground

This directory contains proof-of-concept (POC) implementations and experimental integrations with third-party libraries. The code here is meant for exploration and evaluation before integrating into the main codebase.

## Purpose

- Evaluate third-party libraries for potential integration
- Test new features without modifying the core codebase
- Provide examples of alternative implementations
- Measure performance and accuracy improvements

## Structure

- `poc/`: Proof-of-concept implementations
  - `quantlib_options_poc.py`: QuantLib integration for option calculations
  - (Additional POCs will be added here)

## Usage

Each POC is designed to be a standalone script that can be run independently:

```bash
# Run the QuantLib options POC
python src/playground/poc/quantlib_options_poc.py
```

## Development Process

1. Create a new POC script for your experiment
2. Document your findings and results
3. If valuable, create a plan for integrating into the main codebase
