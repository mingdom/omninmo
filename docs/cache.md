# Cache System Documentation

## Overview

omninmo uses multiple caching mechanisms to optimize performance and reduce API calls. This document outlines the different types of caches, their purposes, and when they are cleared.

## Cache Types

### 1. Data Cache

The data cache stores stock data fetched from the Financial Modeling Prep (FMP) API.

**Location:**
- Directory: `cache/`
- File format: `fmp_{ticker}_{period}_{interval}.csv`

**Usage:**
- Checked before making API calls
- Stores successful API responses
- Falls back to sample data on cache/API failures

**Invalidation:**
- Automatic: After 24 hours
- Manual: Using `make clear-cache` command
- During weekly model retraining
- When cache read fails

### 2. Streamlit Cache

#### Resource Cache (@st.cache_resource)
Used for long-lived singleton objects that should persist across sessions.

**Applied to:**
- FeatureEngineer instances
- Model instances

**Characteristics:**
- No automatic invalidation
- Persists across multiple user sessions
- Memory-based caching

#### Data Cache (@st.cache_data)
Used for function results that should be recomputed periodically.

**Applied to:**
- analyze_ticker function results

**Characteristics:**
- TTL: 3600 seconds (1 hour)
- Automatically invalidates after TTL
- Per-session caching

### 3. Configuration Cache

Uses Python's @lru_cache decorator for configuration management.

**Characteristics:**
- Memory-based caching
- No automatic invalidation
- Persists until application restart
- Caches parsed YAML configuration

### 4. Model Storage

While not technically a cache, model storage serves a similar purpose for persisting trained models.

**Location:**
- Directory: `models/`
- Format: PKL files (e.g., `stock_predictor_YYYY_MM_DD.pkl`)

**Characteristics:**
- Versioned with timestamps
- Cleared during model retraining
- Supports rollback to previous versions

## Cache Clearing Scenarios

### Manual Clearing

1. `make clean`
   - Cleans all generated files
   - Removes Python cache files
   - Clears data cache
   - Removes model files

2. `make clear-cache`
   - Specifically targets data cache
   - Preserves other generated files

### Automatic Clearing

1. Time-based:
   - Data cache: 24 hours
   - Streamlit data cache: 1 hour

2. Event-based:
   - Weekly model retraining
   - Failed cache reads
   - Invalid cache files

### Error Handling

1. Cache Read Failures:
   - Trigger fresh data fetch
   - Log warning message
   - Continue operation

2. API Failures:
   - Fall back to sample data
   - Log error message
   - Continue operation

## Best Practices

1. Use `make clear-cache` when:
   - Troubleshooting data issues
   - Forcing fresh data fetch
   - After API changes

2. Use `make clean` when:
   - Major version updates
   - Complete system reset needed
   - Troubleshooting system-wide issues

3. Monitor cache health:
   - Check log files for cache errors
   - Verify cache file timestamps
   - Ensure sufficient disk space 