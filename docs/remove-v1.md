# V1 Code Removal Plan

## Overview
This document outlines the steps needed to safely remove the v1 code now that v2 implementation is complete.

## Analysis Findings

### Utils Directory Analysis
After careful analysis of the old utils directory (`src/utils/`), I found:

1. No v2 code imports or uses any of the old utils
2. The v2 implementation is completely self-contained with its own:
   - Configuration handling (`v2/config.py`)
   - Feature engineering (`v2/features.py`)
   - Data fetching (`v2/data_fetcher.py`)
   - Model prediction (`v2/predictor.py`)
3. The only references to old utils are from:
   - `src/utils/trainer.py` (v1 code)
   - `scripts/train_st_model.py` (v1 code, already marked for removal)
4. Conclusion: The entire `src/utils/` directory can be safely removed

## Progress Update

### Completed Steps
1. ✅ Removed `src/models/` directory
2. ✅ Removed `src/utils/` directory
3. ✅ Removed `src/data/` directory
4. ✅ Removed `scripts/train_st_model.py`
5. ✅ Verified config.yaml is v2-focused
6. ✅ Verified README.md is v2-focused
7. ✅ Verified requirements.txt contains only needed dependencies
8. ✅ Verified src/__init__.py is clean

### Current State
- Source code is now clean and v2-focused
- All configuration and documentation is v2-focused
- No unnecessary dependencies in requirements.txt
- Project structure is simplified and focused on v2 implementation

### Remaining Tasks
None - all v1 code has been successfully removed

## Pre-removal Checks
1. Verify that v2 functionality is fully operational
2. Ensure no remaining dependencies on v1 code
3. Back up current state before removal (recommended)

## Components to Remove

### 1. Source Code
- Remove all files in `src/v1/` directory (if it exists)
- Remove any v1-specific files in the root `src/` directory
- Remove any v1-specific tests in `tests/` directory

### 2. Scripts
- Remove v1-specific scripts from `scripts/` directory
- Update any scripts that might reference v1 components

### 3. Dependencies
Review `requirements.txt` to:
- Remove any dependencies only used by v1
- Update version constraints if they were specific to v1

### 4. Configuration
- Remove v1-specific configurations from `config.yaml`
- Update any configuration files that might reference v1 components

### 5. Documentation
- Archive or update documentation that references v1
- Remove v1-specific sections from README files
- Keep historical documentation if useful for reference

## Removal Steps

1. **Backup**
   ```bash
   # Create backup branch
   git checkout -b backup/v1-removal
   git add .
   git commit -m "Backup before v1 removal"
   ```

2. **Remove Source Code**
   ```bash
   # Remove v1 directory
   rm -rf src/v1/
   # Remove v1 tests
   rm -rf tests/v1/
   ```

3. **Update Dependencies**
   - Review and update `requirements.txt`
   - Remove v1-specific dependencies
   - Run tests to ensure v2 still works

4. **Update Configuration**
   - Remove v1 sections from config files
   - Update any v1 references in configuration

5. **Documentation Updates**
   - Update main README.md
   - Remove v1-specific documentation
   - Update any tutorials or guides

6. **Clean Up**
   ```bash
   # Commit changes
   git add .
   git commit -m "Remove v1 code"
   ```

7. **Testing**
   - Run all tests to ensure v2 functionality is not affected
   - Test all main features
   - Verify no v1 dependencies are being called

## Verification Checklist

- [ ] All v1 source code removed
- [ ] No remaining v1 dependencies in requirements.txt
- [ ] Configuration files updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] v2 functionality verified
- [ ] No references to v1 in current codebase

## Rollback Plan

If issues are encountered:
1. Reset to backup branch
2. Investigate issues
3. Create new removal plan if needed

## Notes
- Keep commit history for reference
- Document any issues encountered during removal
- Update this document as needed during the removal process 