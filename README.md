# Folio - Financial Portfolio Dashboard

Folio is a web-based dashboard for analyzing financial portfolios. It provides visualizations and insights for stocks, options, and other financial instruments.

## Features

- **Portfolio Summary**: View total exposure, beta, and allocation breakdown
- **Position Details**: Analyze individual positions with detailed metrics
- **Filtering & Sorting**: Filter by position type and sort by various metrics
- **Data Integration**: Uses Yahoo Finance API for real-time market data
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Easy on the eyes for financial analysis

## Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/mingdom/omninmo.git
   cd omninmo
   ```

2. Run the application:
   ```bash
   make folio
   ```

3. Or use the sample portfolio:
   ```bash
   make portfolio
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t folio:latest .
   ```

2. Run the container:
   ```bash
   make docker-compose-up
   ```

3. Access the application at http://localhost:8050

## Hugging Face Deployment

The application is deployed on Hugging Face Spaces and can be accessed at:
https://huggingface.co/spaces/mingdom/folio

For detailed deployment instructions, see [docs/huggingface-deployment.md](docs/huggingface-deployment.md).

## Project Structure

- `src/folio/`: Main application code
  - `app.py`: Dash application entry point
  - `components/`: UI components
  - `utils.py`: Utility functions
  - `data_model.py`: Data structures and models
- `src/lab/`: Experimental features and utilities
- `docs/`: Documentation
  - `devlog/`: Development logs
  - `devplan/`: Development plans
- `scripts/`: Utility scripts for development and diagnostics

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test your changes with `make test`
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
