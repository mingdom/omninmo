# Setup Guide

This guide provides instructions for setting up the omninmo development environment.

## Prerequisites

- Python 3.8 or higher
- pip3 (Python package installer)
- virtualenv or venv module

## Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/omninmo.git
   cd omninmo
   ```

2. **Set Up a Virtual Environment**

   The easiest way to set up a virtual environment is to use the provided Makefile target:

   ```bash
   make env
   ```

   This will:
   - Create a virtual environment in the `venv` directory
   - Upgrade pip to the latest version
   - Create an activation script (`activate-venv.sh`)

   Alternatively, you can manually create a virtual environment:

   ```bash
   # Using venv
   python3 -m venv venv
   
   # Activate the virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Activate the Virtual Environment**

   ```bash
   source activate-venv.sh
   ```

   You should see a `(venv)` prefix in your terminal prompt indicating that the virtual environment is active.

4. **Install Dependencies**

   ```bash
   make install
   ```

   This will install all required packages, including:
   - streamlit (for the web interface)
   - yfinance (for fetching stock data)
   - pandas (for data manipulation)
   - scikit-learn (for machine learning models)
   - plotly (for interactive visualizations)
   - tqdm (for progress bars)

## Configuration

No additional configuration is required for basic usage. The application uses default settings that work out of the box.

## Running the Application

1. **Train the Model (First Time Only)**

   ```bash
   make train
   ```

2. **Start the Streamlit App**

   ```bash
   make run
   ```

   This will launch the Streamlit web interface, typically at http://localhost:8501

3. **Testing the Model**

   To evaluate model performance:

   ```bash
   make test
   ```

4. **Command-line Predictions**

   For quick predictions without the web interface:

   ```bash
   make predict TICKER=AAPL
   ```

   Replace `AAPL` with any stock ticker (e.g., MSFT, NVDA).

## Using the Makefile

The project includes a Makefile with various targets for common operations:

- `make help` - Show available targets
- `make env` - Set up a virtual environment
- `make install` - Install dependencies
- `make test` - Run all tests
- `make train` - Train the model
- `make run` - Run the Streamlit app
- `make predict TICKER=AAPL` - Predict rating for a ticker
- `make clean` - Clean up generated files
- `make pipeline` - Run the full pipeline (tests, training, prediction)
- `make executable` - Make all scripts executable

## Troubleshooting

### Common Issues

1. **Missing Dependencies**

   If you encounter errors about missing packages, try reinstalling the requirements:

   ```bash
   make install
   ```

2. **Data Fetching Issues**

   If you experience problems with yfinance data fetching, it could be due to API rate limits or connectivity issues. Try again after a short wait.

3. **Import Errors**

   Ensure that you're running the scripts from the project root directory to avoid import path issues.

4. **Virtual Environment Issues**

   If you encounter issues with the virtual environment:
   
   ```bash
   # Remove the existing virtual environment
   rm -rf venv
   
   # Create a new virtual environment
   make env
   
   # Activate the virtual environment
   source activate-venv.sh
   
   # Install dependencies
   make install
   ```

### Getting Help

If you encounter any issues not covered here, please open an issue on the project repository. 