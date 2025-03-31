# Lab Projects

This directory contains one-off analysis tools and experiments separate from the main v2 project.

## Current Tools

### Portfolio Risk Analysis
Calculates portfolio beta from a Fidelity CSV export.

**Setup:**
1. Export your portfolio from Fidelity as CSV
2. Save it as `portfolio.csv` in this directory (this file is gitignored)

**Usage:**
```bash
# Using portfolio.csv in this directory
make portfolio

# Using a custom CSV file
make portfolio csv=path/to/your/portfolio.csv
```

Dependencies are managed in the root `requirements.txt` under "Lab project dependencies". 