# Development Plan: Gemini API Integration for Docker Deployment

## Overview

This development plan outlines the steps needed to ensure the Gemini AI integration works properly in the Docker deployment environment, particularly for Hugging Face Spaces. The plan addresses several key issues:

1. Missing Google Generative AI package in Docker requirements
2. Lack of GEMINI_API_KEY environment variable in Docker deployment
3. Need for basic testing of Gemini API functionality
4. Creation of a docker-test command for testing in the container environment

## Current State Analysis

### Issues Identified

1. **Missing Dependencies**: 
   - The `google-generativeai` package is not included in `requirements-docker.txt`
   - This means the Docker container cannot initialize the Gemini client

2. **Environment Variable Handling**:
   - The Gemini client requires a `GEMINI_API_KEY` environment variable
   - This variable is not being passed to the Docker container
   - No fallback mechanism exists for when the API key is missing

3. **Testing Infrastructure**:
   - No specific tests for the Gemini client initialization
   - No way to test the Docker container without manual intervention
   - No end-to-end tests for the AI chat functionality

4. **Docker Configuration**:
   - Docker environment is not properly configured to support the Gemini API
   - No mechanism to pass API keys securely to the container

## Implementation Plan

### 1. Add Missing Dependencies

Update `requirements-docker.txt` to include the Google Generative AI package:

```
# AI/ML dependencies
google-generativeai>=0.3.0  # For Gemini AI integration
```

### 2. Create Basic Gemini API Test

Create a new test file `tests/test_gemini_client.py` that:
- Tests initialization of the Gemini client
- Verifies API key handling
- Makes a minimal API call to check connectivity
- Includes proper mocking to avoid actual API calls during testing

### 3. Update Docker Configuration

Modify the Docker setup to properly handle the Gemini API key:

1. Update `Dockerfile` to accept the API key as a build argument or environment variable
2. Update `docker-compose.yml` to pass through the API key from the host environment
3. Add appropriate error handling in the application for when the API key is missing

### 4. Create `make docker-test` Command

Add a new target to the Makefile that:
- Builds the Docker container with test dependencies
- Runs the test suite inside the container
- Reports test results back to the host
- Uses a separate docker-compose file for testing

### 5. Implement Fallback Mechanism

Add a graceful fallback mechanism in the application when the Gemini API is not available:
- Detect missing API key and provide a user-friendly message
- Disable AI features when the API is not available
- Log appropriate warnings

### 6. End-to-End Testing

Create a comprehensive testing strategy for the AI chat functionality:
- Unit tests for individual components
- Integration tests for the chat workflow
- End-to-end tests in the Docker environment

## Detailed Implementation Steps

### Step 1: Update Requirements

1. Add Google Generative AI package to `requirements-docker.txt`:
   ```
   # AI/ML dependencies
   google-generativeai>=0.3.0  # For Gemini AI integration
   ```

### Step 2: Create Gemini Client Test

1. Create `tests/test_gemini_client.py` with the following tests:
   - Test initialization with valid API key
   - Test error handling with missing API key
   - Test basic API connectivity (with mocking)
   - Test fallback behavior

### Step 3: Update Docker Configuration

1. Modify `Dockerfile` to include:
   ```dockerfile
   # Allow passing Gemini API key
   ARG GEMINI_API_KEY
   ENV GEMINI_API_KEY=${GEMINI_API_KEY}
   ```

2. Update `docker-compose.yml` to include:
   ```yaml
   environment:
     - GEMINI_API_KEY=${GEMINI_API_KEY}
   ```

3. Create a `.env.example` file with:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Step 4: Create Docker Test Command

1. Add to `Makefile`:
   ```makefile
   .PHONY: docker-test
   docker-test:
       @echo "Running tests in Docker container..."
       @docker-compose -f docker-compose.test.yml build
       @docker-compose -f docker-compose.test.yml run --rm folio pytest tests/ -v
   ```

2. Create `docker-compose.test.yml`:
   ```yaml
   version: '3.8'
   
   services:
     folio:
       build: .
       environment:
         - PYTHONPATH=/app
         - GEMINI_API_KEY=${GEMINI_API_KEY}
         - LOG_LEVEL=DEBUG
       volumes:
         - ./tests:/app/tests
       command: pytest tests/ -v
   ```

### Step 5: Implement Fallback Mechanism

1. Update `src/folio/gemini_client.py` to handle missing API key gracefully:
   ```python
   def __init__(self):
       """Initialize the Gemini client with API key from environment."""
       self.api_key = os.environ.get("GEMINI_API_KEY")
       self.is_available = False
       
       if not self.api_key:
           logger.warning("GEMINI_API_KEY environment variable not set. AI features will be disabled.")
           return
           
       try:
           genai.configure(api_key=self.api_key)
           self.model = genai.GenerativeModel(
               model_name="gemini-2.5-pro-exp-03-25",
               generation_config=GenerationConfig(
                   temperature=0.2,
                   top_p=0.95,
                   top_k=40,
                   max_output_tokens=4096,
               ),
               system_instruction=PORTFOLIO_ADVISOR_SYSTEM_PROMPT,
           )
           self.is_available = True
           logger.info("Gemini client initialized successfully")
       except Exception as e:
           logger.error(f"Failed to initialize Gemini client: {e!s}")
   ```

2. Update chat methods to check `is_available` before making API calls

### Step 6: End-to-End Testing

1. Create integration tests for the chat workflow
2. Add Docker-specific tests for the deployment environment
3. Implement a test for the fallback mechanism

## Success Criteria

The implementation will be considered successful when:

1. All tests pass both locally and in the Docker environment
2. The Gemini API is properly initialized in the Docker container
3. The application gracefully handles missing API keys
4. The chat functionality works end-to-end in the Docker environment
5. The `make docker-test` command successfully runs all tests in the container

## Timeline

1. Update requirements and create basic tests: 1 day
2. Update Docker configuration: 1 day
3. Implement fallback mechanism: 1 day
4. Create docker-test command and end-to-end tests: 1 day
5. Testing and iteration: 1 day

Total estimated time: 5 days
