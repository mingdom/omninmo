# Project Overview

## What is omninmo?

omninmo (the palindrome of "omni") is an investor super-app designed to predict stock performance using machine learning and technical analysis. The name reflects our ambition to provide omniscient insights into market movements.

## Vision

Our vision is to democratize stock analysis by providing sophisticated predictions that are accessible to both novice and experienced investors. While professional traders have access to advanced tools and analytics, individual investors often rely on basic charts or third-party recommendations. omninmo aims to bridge this gap by offering algorithmic predictions based on technical indicators and historical patterns.

## Core Functionality

At its core, omninmo takes a stock ticker symbol as input and produces a rating as output:

**Input:** Stock ticker (e.g., `NVDA`)  
**Output:** omninmo Rating (e.g., `Strong Buy`)

The rating system includes five categories:
- Strong Buy
- Buy
- Hold
- Sell
- Strong Sell

Each rating is accompanied by a confidence score and supporting technical indicators to help users understand the reasoning behind the prediction.

## Technical Approach

omninmo uses a multi-faceted approach to stock prediction:

1. **Data Collection**: We fetch historical price and volume data using the yfinance library, which provides access to Yahoo Finance data.

2. **Feature Engineering**: We calculate various technical indicators that traders commonly use, including:
   - Moving averages (simple and exponential)
   - Relative Strength Index (RSI)
   - Moving Average Convergence Divergence (MACD)
   - Bollinger Bands
   - Volume indicators

3. **Machine Learning**: We use a RandomForest classifier to predict stock ratings based on the engineered features. This model is trained on historical data and patterns.

4. **Visualization**: We provide interactive charts and visualizations to help users understand the data and predictions.

## Current State and Roadmap

### Current State (MVP)

The Minimum Viable Product (MVP) focuses on technical analysis and a basic prediction model:
- Streamlit web interface for easy interaction
- Stock data fetching and processing
- Technical indicator calculation
- Basic RandomForest prediction model
- Interactive visualizations

### Future Roadmap

Our ambitious roadmap includes:

1. **Enhanced Data Sources**:
   - Fundamental financial data (earnings, revenue, etc.)
   - News sentiment analysis
   - Social media sentiment

2. **Advanced Models**:
   - Deep learning models for time series prediction
   - Ensemble methods combining multiple prediction approaches
   - Reinforcement learning for adaptive strategies

3. **Expanded Features**:
   - Portfolio optimization recommendations
   - Risk assessment tools
   - Customizable screening criteria

4. **Natural Language Processing**:
   - Earnings transcript analysis
   - News impact assessment
   - SEC filing analysis

## Target Users

omninmo is designed for:

1. **Individual Investors**: Who want data-driven insights without complex analysis
2. **Day Traders**: Who need quick assessments of multiple stocks
3. **Long-term Investors**: Who want to validate their investment theses
4. **Financial Educators**: Who can use the tool to demonstrate technical analysis concepts

## Success Metrics

We measure the success of omninmo by:

1. **Prediction Accuracy**: How often our ratings align with subsequent stock performance
2. **User Adoption**: Number of active users and engagement metrics
3. **Feature Utilization**: Which features and indicators users find most valuable
4. **User Feedback**: Qualitative assessment of the tool's utility

## Getting Involved

We welcome contributions from developers, financial experts, and users. See our [Development Guide](./development_guide.md) for information on how to contribute to the project. 