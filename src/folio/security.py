"""
Security utilities for the Folio application.

This module provides security-related functions for validating and sanitizing
user inputs, particularly for CSV file uploads.
"""

import base64
import io
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .logger import logger

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Required columns for portfolio CSV files
REQUIRED_COLUMNS = ['Symbol', 'Quantity', 'Last Price']

# Columns that might contain formulas and need sanitization
FORMULA_RISK_COLUMNS = [
    'Symbol', 'Description', 'Type', 'Current Value',
    'Last Price', 'Last Price Change', 'Today\'s Gain/Loss Dollar',
    'Today\'s Gain/Loss Percent', 'Total Gain/Loss Dollar',
    'Total Gain/Loss Percent', 'Percent Of Account',
    'Cost Basis Total', 'Average Cost Basis'
]

# Regex patterns for detecting potentially malicious content
DANGEROUS_PATTERNS = [
    # Excel formula injection patterns
    r'^=',
    r'^@',
    r'^[+-]',
    r'^-\d',  # Exclude negative numbers
    r'^DDE\(',
    r'^EMBED\(',
    r'^HYPERLINK\(',
    r'^MSEXCEL\|',
    # HTML/JavaScript injection patterns
    r'<script',
    r'javascript:',
    r'<iframe',
    r'<img',
    r'onerror=',
    r'onload=',
    r'onclick=',
    # Command injection patterns
    r'[&|;`]',
    r'\$\(',
    r'`.*`',
]

# Compiled regex patterns for performance
DANGEROUS_REGEX = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE)


def validate_csv_upload(contents: str, filename: str) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Validate and sanitize a CSV file upload.

    Args:
        contents: Base64-encoded contents of the uploaded file
        filename: Name of the uploaded file

    Returns:
        Tuple containing:
        - Validated and sanitized DataFrame
        - Error message (if validation fails, otherwise None)

    Raises:
        ValueError: If validation fails
    """
    # Validate file extension
    if not filename.lower().endswith('.csv'):
        raise ValueError("Only CSV files are supported")

    # Decode base64 content
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
    except Exception as e:
        logger.error(f"Error decoding file content: {e}")
        raise ValueError(f"Invalid file format: {str(e)}")

    # Check file size
    if len(decoded) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(decoded)} bytes (max {MAX_FILE_SIZE})")
        raise ValueError(f"File too large (max {MAX_FILE_SIZE/1024/1024:.1f}MB)")

    # Parse CSV
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise ValueError(f"Invalid CSV format: {str(e)}")

    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        logger.warning(f"Missing required columns: {missing_columns}")
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    # Sanitize data to prevent CSV injection
    df = sanitize_dataframe(df)

    return df, None


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize a DataFrame to prevent CSV injection and other attacks.

    Args:
        df: DataFrame to sanitize

    Returns:
        Sanitized DataFrame
    """
    # Create a copy to avoid modifying the original
    df_safe = df.copy()

    # Sanitize all string columns
    for col in df_safe.columns:
        if df_safe[col].dtype == 'object':
            df_safe[col] = df_safe[col].apply(lambda x: sanitize_cell(x) if pd.notna(x) else x)

    # Additional sanitization for columns that might contain formulas
    for col in FORMULA_RISK_COLUMNS:
        if col in df_safe.columns and df_safe[col].dtype == 'object':
            df_safe[col] = df_safe[col].apply(lambda x: sanitize_formula(x) if pd.notna(x) else x)

    return df_safe


def sanitize_cell(value: Any) -> str:
    """
    Sanitize a cell value to prevent injection attacks.

    Args:
        value: Cell value to sanitize

    Returns:
        Sanitized value
    """
    # Convert to string if not already
    if not isinstance(value, str):
        return str(value)

    # Check for dangerous patterns
    if DANGEROUS_REGEX.search(value):
        logger.warning(f"Potentially dangerous content detected: {value}")
        # Remove or neutralize the dangerous content
        return sanitize_dangerous_content(value)

    return value


def sanitize_formula(value: Any) -> str:
    """
    Specifically sanitize formula-like content in cells.

    Args:
        value: Cell value to sanitize

    Returns:
        Sanitized value
    """
    if not isinstance(value, str):
        return str(value)

    # Neutralize formula triggers, but preserve negative numbers
    if value.startswith(('=', '+', '@')):
        # Prefix with apostrophe to neutralize formula
        return "'" + value

    # Special handling for values starting with '-'
    if value.startswith('-'):
        # Check if it's a negative number (integer or float)
        if re.match(r'^-\d+(\.\d+)?$', value):
            # It's a negative number, leave it as is
            return value
        else:
            # It's not a number, neutralize it
            return "'" + value

    return value


def sanitize_dangerous_content(value: str) -> str:
    """
    Sanitize content identified as potentially dangerous.

    Args:
        value: Content to sanitize

    Returns:
        Sanitized content
    """
    # Replace formula triggers
    value = re.sub(r'^=', "'=", value)
    value = re.sub(r'^@', "'@", value)
    value = re.sub(r'^[+]', "'+", value)

    # Don't modify negative numbers that are actually numbers
    if not re.match(r'^-\d+(\.\d+)?$', value):
        value = re.sub(r'^-', "'-", value)

    # Remove HTML/script tags
    value = re.sub(r'<script.*?>.*?</script>', "[REMOVED]", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'<iframe.*?>.*?</iframe>', "[REMOVED]", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'javascript:', "[REMOVED]", value, flags=re.IGNORECASE)

    # Remove event handlers
    value = re.sub(r'on\w+\s*=', "[REMOVED]=", value, flags=re.IGNORECASE)

    # Remove command injection characters
    value = re.sub(r'[&|;`]', "", value)
    value = re.sub(r'\$\(', "$(", value)
    value = re.sub(r'`.*?`', "", value, flags=re.DOTALL)

    return value
