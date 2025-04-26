# Fix Default Watchlist Configuration

## Issue
The `make predict` command was failing because the application couldn't find the default watchlist configuration. The error occurred because:
1. The code was looking for tickers at `watchlist.default` but they are stored under `app.watchlist.default` in the config data
2. This is because when using the multi-file configuration structure, each file's contents are stored under a key matching its filename (without extension)

## Changes Made
1. Updated `src/v2/console_app.py` to use the correct configuration path:
   - Changed `config.get("watchlist.default")` to `config.get("app.watchlist.default")`
   - This properly accesses the watchlist configuration from app.yaml

2. Added debug logging to `src/v2/config.py` to:
   - Log the configuration loading process
   - Track how configuration keys are accessed
   - Help diagnose similar issues in the future

## Impact
- The `make predict` command should now work correctly with the default watchlist from `app.yaml`
- Better understanding of how the multi-file configuration system works
- Improved logging for configuration-related issues

## Testing
To verify the fix:
1. Run `make predict` without specifying tickers
2. The command should use the default watchlist from `app.yaml`
3. Check the logs to see the configuration loading process 