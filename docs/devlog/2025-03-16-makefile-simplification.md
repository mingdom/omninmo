# Makefile Simplification Plan

## Current Status
The current Makefile contains several targets that are either no longer used or could be simplified by merging functionality.

## Changes Implemented

### Targets Removed
1. `pipeline` - No longer used in the current workflow
2. `executable` - Functionality moved to `install` target
3. `train-sample` - Merged into `train` target with `--sample` flag
4. `clear-cache` - Merged into `clean` target with `--cache` flag

### Modifications Made
1. `train` target:
   - Added `--sample` flag (simpler name for `--force-sample`)
   - Example: `make train --sample`

2. `clean` target:
   - Kept as primary cleanup command
   - Added `--cache` flag for cache clearing
   - Example: `make clean --cache`

3. `install` target:
   - Now includes script permission setting
   - Automatically makes scripts executable during installation

4. `help` target:
   - Updated to be single source of truth for documentation
   - Improved formatting with options on separate lines
   - Removed documentation for removed targets
   - Added clear flag documentation

## Benefits
- Reduced complexity in the Makefile
- More intuitive command names (e.g. `--sample` instead of `--force-sample`)
- Maintained all necessary functionality through flags
- Better adherence to KISS principle
- Clearer documentation with help text as single source of truth
- More consistent command structure

## Implementation Notes
- Script permissions are now set during installation
- Documentation is centralized in `help` target
- Cache clearing is now an option of `clean` rather than separate command
- Sample data training is now an option of `train` rather than separate command 