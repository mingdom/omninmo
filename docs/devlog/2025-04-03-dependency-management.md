# Dependency Management Improvements

Date: 2025-04-03

## Overview

This document details improvements to the dependency management system for the Folio application. The changes establish a clear separation between production dependencies (required for the Folio app) and development dependencies (required for development, testing, and other tools).

## Changes Made

### 1. Reorganized Requirements Files

The project now uses two distinct requirements files with clear separation of concerns:

1. **requirements-docker.txt**: Contains all dependencies needed for the Folio app in production
   - Core libraries (pandas, numpy, scipy)
   - Web application dependencies (dash, dash-bootstrap-components)
   - Data source dependencies (yfinance)
   - Server dependencies (uvicorn)

2. **requirements.txt**: Contains only additional dependencies needed for development
   - Machine learning libraries (scikit-learn, xgboost)
   - Development tools (pytest, ruff)
   - Visualization tools (matplotlib, plotly)
   - Model tracking (mlflow, shap)

This approach ensures:
- A single source of truth for each dependency
- Minimal Docker images with only necessary dependencies
- Clear separation between production and development requirements

### 2. Updated Installation Process

Modified `scripts/install-reqs.sh` to:
- First install all dependencies from `requirements-docker.txt`
- Then install additional development dependencies from `requirements.txt`

```bash
# Install Folio app dependencies from requirements-docker.txt
echo "Installing Folio app dependencies from requirements-docker.txt..."
while IFS= read -r package || [ -n "$package" ]; do
    # Skip empty lines and comments
    if [[ -z "$package" || "$package" =~ ^# ]]; then
        continue
    fi
    install_package "$package"
done < "$PROJECT_ROOT/requirements-docker.txt"

# Install additional development dependencies from requirements.txt
echo "Installing additional development dependencies from requirements.txt..."
while IFS= read -r package || [ -n "$package" ]; do
    # Skip empty lines and comments
    if [[ -z "$package" || "$package" =~ ^# ]]; then
        continue
    fi
    # Skip matplotlib as we've already installed it
    if [[ "$package" != matplotlib* ]]; then
        install_package "$package"
    fi
done < "$PROJECT_ROOT/requirements.txt"
```

### 3. Updated Dockerfile

The Dockerfile now uses `requirements-docker.txt` for a cleaner and more maintainable approach:

```dockerfile
# Copy requirements file
COPY requirements-docker.txt .

# Install all required packages
RUN pip install --no-cache-dir -r requirements-docker.txt
```

## Benefits

1. **Cleaner Docker Images**: Docker images only include the dependencies actually needed for production.

2. **Simplified Dependency Management**: Each dependency has a single source of truth, making updates easier.

3. **Improved Development Experience**: Developers can easily see which dependencies are for production vs. development.

4. **Reduced Conflicts**: Separating dependencies reduces the chance of version conflicts.

5. **Better Documentation**: The requirements files now clearly document the purpose of each dependency.

## Usage

- For production/Docker: Use `requirements-docker.txt`
- For development: Use both `requirements-docker.txt` and `requirements.txt`
- For adding new dependencies:
  - If needed for the Folio app: Add to `requirements-docker.txt`
  - If only needed for development: Add to `requirements.txt`

## Version Pinning Strategy

The project uses a mixed approach to version pinning:

1. **Security-Critical Components**: For components where security is paramount (like Uvicorn and Dash), we use minimum version constraints without upper bounds:
   ```
   uvicorn>=0.27.1
   dash>=2.14.2
   ```
   This ensures we always get the latest security updates for these critical components.

2. **Other Dependencies**: For other dependencies, we pin specific versions to ensure consistency and reproducibility.

This approach balances security needs with stability during early development. As the application matures and gets more traffic, we may revisit this strategy and implement more strict version pinning.

## Future Considerations

1. **Dependency Pinning**: Consider implementing a more robust dependency pinning strategy using tools like pip-tools as the application matures.

2. **Environment-Specific Requirements**: If needed, create additional requirements files for specific environments (e.g., `requirements-test.txt`).

3. **Dependency Auditing**: Implement regular dependency auditing to check for security vulnerabilities and outdated packages.

4. **Version Constraints**: As the application stabilizes, consider adding upper bounds to version constraints (e.g., `uvicorn>=0.27.1,<0.28.0`) to prevent unexpected breaking changes.
