# Python Linting Configuration

This project uses [Ruff](https://docs.astral.sh/ruff/) for Python linting and code formatting. Ruff is a fast, all-in-one linter and formatter written in Rust.

## Quick Start

```bash
# Check for linting issues
make lint

# Auto-fix linting issues
make lint-fix
```

All lint check outputs are logged to `logs/lint_TIMESTAMP.log` for future reference.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ruff is configured via `pyproject.toml` in the root directory with the following rules enabled:
   - `E`: pycodestyle errors
   - `F`: pyflakes
   - `I`: isort
   - `N`: pep8-naming
   - `UP`: pyupgrade
   - `PL`: pylint
   - `RUF`: ruff-specific rules
   - `W`: pycodestyle warnings

## Usage

### Automatic Formatting

- Files are automatically formatted on save
- Imports are automatically organized on save
- Line length is set to 88 characters (same as Black)

### Manual Commands

You can run Ruff manually using:

```bash
# Check all files
ruff check .

# Fix all auto-fixable issues
ruff check --fix .

# Format a specific file
ruff format src/your_file.py
```

### Common Rules

Our configuration:
- Enforces consistent import ordering
- Catches unused imports and variables
- Enforces consistent naming conventions
- Upgrades Python syntax to newer versions where applicable
- Ignores line length violations (E501) for flexibility in data science code

### Excluded Directories

The following directories are excluded from linting:
- `.git`
- `.venv`
- `venv`
- `__pycache__`
- `build`
- `dist`
- `mlruns`
- `.pytest_cache`
- `.archive`

### Special Cases

- `__init__.py` files: Unused imports (F401) are allowed
- Test files: Magic numbers (PLR2004) are allowed

## IDE Integration

The project includes VSCode/Cursor settings for Ruff integration. These settings enable:
- Real-time linting
- Format on save
- Import organization
- Quick fixes for common issues

## Customizing Rules

To modify linting rules, edit the `[tool.ruff]` section in `pyproject.toml`. See the [Ruff documentation](https://docs.astral.sh/ruff/) for all available options. 