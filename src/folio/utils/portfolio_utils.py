"""Portfolio processing utilities."""

# Import the process_portfolio_data function from the main utils module
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the process_portfolio_data function
from src.folio.utils import process_portfolio_data

# Re-export the function
__all__ = ['process_portfolio_data']
