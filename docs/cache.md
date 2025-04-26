# Data Caching System

## Overview
The omninmo project uses a file-based caching system to store stock data and reduce API calls. This document explains how the caching system works and its configuration.

## Implementation

### Location
- Cache files are stored in the `cache/` directory at the project root
- Each ticker's data is stored in a separate CSV file
- Filename format: `{ticker}_{period}_{interval}.csv` (e.g., `AAPL_5y_1d.csv`)

### Current Behavior
- Both `YFinanceDataFetcher` and `DataFetcher` classes implement caching
- When data is requested, it first checks if a cache file exists and if it's valid
- Cache validity is determined by two factors:
  1. Time-to-live (TTL): Cache must be younger than the configured TTL
  2. Market hours: Cache expires daily at 2PM Pacific time to ensure EOD pricing
- If the cache is valid, it loads the data from cache
- If the cache is invalid (expired TTL or after market close), it fetches fresh data from the API
- If no cache file exists, it fetches from the API and saves to cache
- Cache can be manually cleared with `make clear-cache`

### Configuration
- The cache directory is configurable in `config.yaml` under `data.fmp.cache_dir` or `data.yfinance.cache_dir`
- The TTL value is configurable in `config.yaml` under `app.cache.ttl` (in seconds)
- Default TTL is 86400 seconds (1 day) if not specified in config
- Market hours expiry is fixed at 2PM Pacific time

## Usage Examples

### Changing Cache TTL
To change the cache TTL, modify the `app.cache.ttl` value in `config.yaml`:

```yaml
app:
  cache:
    ttl: 86400  # Set to 24 hours (86400 seconds)
```

### Market Hours Expiry
The cache system is configured to expire data daily after market close (2PM Pacific time) to ensure we use end-of-day pricing. This behavior:

- Ensures that we always have fresh data after the market closes
- Prevents using stale data from the previous day when making trading decisions
- Works in conjunction with the TTL setting (cache expires if either condition is met)

### Forcing Cache Refresh
To force a refresh of the cache:
1. Run `make clear-cache` to clear all cached data
2. Set TTL to a very low value (e.g., 1 second) in config.yaml

## Limitations
1. No partial updates (must refetch all data)
2. No cache headers or metadata stored with files
3. No selective cache invalidation (all or nothing)
