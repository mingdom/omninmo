# CSV Security Implementation

Date: 2025-04-03

## Overview

This document details the implementation of security measures to protect against CSV injection attacks and other security vulnerabilities in the Folio application. These changes were implemented as part of our security hardening efforts for the Hugging Face deployment.

## Problem Statement

The Folio application allows users to upload CSV files containing portfolio data. Without proper validation and sanitization, this feature could be exploited through:

1. **CSV Injection Attacks**: Malicious users could upload CSV files with formula injections (e.g., `=CMD('rm -rf /')`) that could execute when opened in spreadsheet applications.

2. **XSS Attacks**: CSV files could contain HTML/JavaScript code that might be rendered by the application.

3. **Data Validation Issues**: Invalid or malformed CSV files could cause application errors or unexpected behavior.

## Implementation Details

### 1. New Security Module

Created a dedicated security module (`src/folio/security.py`) with the following components:

- **CSV Validation**: Validates uploaded CSV files for proper format, required columns, and file size limits.
- **Content Sanitization**: Sanitizes potentially dangerous content in CSV files.
- **Formula Detection**: Detects and neutralizes formula injections in CSV cells.

### 2. Key Security Functions

#### `validate_csv_upload(contents, filename)`

This function performs comprehensive validation of uploaded CSV files:

- Validates file extension (must be `.csv`)
- Checks file size (enforces a 10MB limit)
- Verifies required columns are present
- Sanitizes content to prevent injection attacks

#### `sanitize_dataframe(df)`

Sanitizes all string columns in a DataFrame to prevent injection attacks:

- Applies cell-level sanitization to all string values
- Provides additional sanitization for columns that might contain formulas
- Preserves legitimate data while neutralizing potentially dangerous content

#### `sanitize_cell(value)` and `sanitize_formula(value)`

These functions handle specific sanitization tasks:

- Neutralize Excel formula triggers (`=`, `@`, `+`, etc.)
- Remove or neutralize HTML/JavaScript code
- Remove command injection characters
- Preserve legitimate data like negative numbers

### 3. Integration Points

The security module is integrated at two key points:

1. **File Upload Handler**: All uploaded CSV files are validated and sanitized before processing.
2. **Sample Portfolio Loading**: The sample portfolio is also sanitized to ensure consistency.

### 4. Testing

Created comprehensive unit tests (`tests/test_security.py`) to verify the security implementation:

- Tests for cell-level sanitization
- Tests for formula detection and neutralization
- Tests for DataFrame sanitization
- Tests for CSV upload validation

## Security Considerations

### Addressed Vulnerabilities

1. **Formula Injection**: Neutralizes formulas by prefixing with an apostrophe (`'`).
2. **HTML/JavaScript Injection**: Removes or neutralizes HTML tags and JavaScript code.
3. **Command Injection**: Removes characters commonly used in command injection attacks.
4. **Input Validation**: Enforces file type, size limits, and required column validation.

### Remaining Considerations

1. **Performance Impact**: The sanitization process adds some overhead to file processing.
2. **False Positives**: Some legitimate data patterns might be flagged as potentially dangerous.
3. **User Experience**: Users should be informed about sanitization to understand any changes to their data.

## Conclusion

The implemented security measures significantly reduce the risk of CSV injection and other attacks through the file upload feature. The solution balances security with usability by preserving legitimate data while neutralizing potentially dangerous content.

## Future Enhancements

1. **Content Security Policy**: Implement CSP headers to further protect against XSS attacks.
2. **Rate Limiting**: Add rate limiting for file uploads to prevent DoS attacks.
3. **User Feedback**: Provide more detailed feedback to users when their files are sanitized.

## Testing Results

All security tests are passing, confirming that:

- Formula injections are properly neutralized
- HTML/JavaScript code is removed or neutralized
- File validation correctly identifies invalid files
- Legitimate data is preserved, including negative numbers and special characters
