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
- When data is requested, it first checks if a cache file exists and its age
- If the cache file exists and is younger than the TTL, it loads the data from cache
- If the cache file is older than the TTL, it fetches fresh data from the API
- If no cache file exists, it fetches from the API and saves to cache
- Cache can be manually cleared with `make clear-cache`

### Configuration
- The cache directory is configurable in `config.yaml` under `data.fmp.cache_dir`
- The TTL value is configurable in `config.yaml` under `app.cache.ttl` (in seconds)
- Default TTL is 3600 seconds (1 hour) if not specified in config

## Usage Examples

### Changing Cache TTL
To change the cache TTL, modify the `app.cache.ttl` value in `config.yaml`:

```yaml
app:
  cache:
    ttl: 86400  # Set to 24 hours (86400 seconds)
```

### Forcing Cache Refresh
To force a refresh of the cache:
1. Run `make clear-cache` to clear all cached data
2. Set TTL to a very low value (e.g., 1 second) in config.yaml

## Limitations
1. No partial updates (must refetch all data)
2. No cache headers or metadata stored with files
3. No selective cache invalidation (all or nothing)
