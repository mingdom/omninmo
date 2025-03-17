# omninmo - Stock Performance Prediction

A machine learning-powered stock rating system that predicts future stock performance.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/d3ming/omninmo.git
cd omninmo

# Set up environment and install dependencies
make env
make install

# Train the model
make train-sample # for quick testing with sample data
make train # once you are ready for a full training run

# Run prediction
make predict     # predict ratings for all stocks in watchlist
make predict NVDA  # predict rating for NVDA stock
```

## What is omninmo?

**Input:** Stock ticker (e.g., `NVDA`)  
**Output:** Rating prediction (e.g., `Strong Buy`)

omninmo analyzes stock price data and technical indicators to predict one of five ratings:
- **Strong Buy** (4)
- **Buy** (3)
- **Hold** (2)
- **Sell** (1)
- **Strong Sell** (0)

## Documentation

For detailed documentation, see the [Documentation Index](./docs/README.md) in the docs directory. Our documentation covers:

- [Architecture Guide](./docs/architecture.md)
- [Features Documentation](./docs/features.md)
- [Model Documentation](./docs/models.md)
- [MLflow Guide](./docs/mlflow-guide.md)
- [Linting Guide](./docs/lint.md)
- [Development Plans](./docs/devplan/)
- [Implementation Progress](./docs/devlog/)

## License

MIT License

Copyright (c) 2025 omninmo Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
