# Data Caching System

## Overview
The omninmo project uses a file-based caching system to store stock data and reduce API calls. This document explains how the caching system works and its configuration.

## Implementation

### Location
- Cache files are stored in the `cache/` directory at the project root
- Each ticker's data is stored in a separate CSV file
- Filename format: `{ticker}_{period}_{interval}.csv` (e.g., `AAPL_5y_1d.csv`)

### Current Behavior
- The `DataFetcher` class in `src/v2/data_fetcher.py` implements caching
- When data is requested, it first checks if a cache file exists
- If the cache file exists, it loads the data from cache regardless of age
- If no cache file exists, it fetches from the API and saves to cache
- **No TTL (Time To Live) is currently implemented**
- Cache can be manually cleared with `make clear-cache`

### Configuration
- The cache directory is configurable in `config.yaml` under `data.fmp.cache_dir`
- A TTL value exists in the config under `app.cache.ttl` (3600 seconds) but is not currently used

## Limitations
1. No automatic cache invalidation based on age
2. No partial updates (must refetch all data)
3. No cache headers or metadata stored with files
