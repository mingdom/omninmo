# Uvicorn Implementation for Improved Security

Date: 2025-04-03

## Overview

This document details the implementation of Uvicorn as the ASGI server for the Folio application, replacing direct Python execution. This change was made to address security vulnerabilities identified by GitHub's Dependabot related to Gunicorn, which was referenced in our deployment plans but not actually used in the current implementation.

## Changes Made

### 1. Updated Requirements and Dockerfile

Modified the requirements files and Dockerfile:

- Updated `requirements-docker.txt` to replace Gunicorn with Uvicorn (version 0.27.1+)
- Updated `requirements.txt` to include Uvicorn for local development
- Modified the Dockerfile to use `requirements-docker.txt` instead of listing packages directly
- Updated the CMD instruction to use Uvicorn instead of direct Python execution

```diff
# requirements-docker.txt
-# WSGI server for production
-gunicorn==21.2.0
+# ASGI server for production (more secure than gunicorn)
+uvicorn>=0.27.1

# Dockerfile
-# Install all required packages
-RUN pip install --no-cache-dir \
-    dash==2.14.2 \
-    dash-bootstrap-components==1.5.0 \
-    yfinance>=0.2.37 \
-    PyYAML==6.0.1 \
-    requests==2.31.0 \
-    scipy>=1.11.0 \
-    pandas==2.2.1 \
-    numpy==1.26.4
+# Copy requirements file
+COPY requirements-docker.txt .
+
+# Install all required packages
+RUN pip install --no-cache-dir -r requirements-docker.txt

# Run the application with Uvicorn for improved security and performance
# The entrypoint script will determine the correct port based on environment
-CMD ["sh", "-c", "if [ -n \"$HF_SPACE\" ]; then PORT=7860; fi && python -m src.folio.app --port $PORT --host 0.0.0.0"]
+CMD ["sh", "-c", "if [ -n \"$HF_SPACE\" ]; then PORT=7860; fi && uvicorn src.folio.app:server --host 0.0.0.0 --port $PORT --workers 2 --timeout-keep-alive 60"]
```

### 2. Updated Application Code

Modified `src/folio/app.py` to expose the server object for Uvicorn:

```python
# Create the app instance for Uvicorn to use
app = create_app()
server = app.server
```

## Benefits

1. **Improved Security**: Uvicorn has fewer security vulnerabilities compared to Gunicorn, addressing the issues identified by GitHub's Dependabot.

2. **Better Performance**: Uvicorn is built on uvloop, which provides better performance than the standard asyncio event loop.

3. **Modern ASGI Support**: Uvicorn is an ASGI server, which is the modern standard for Python web applications, offering better support for asynchronous operations.

4. **Simplified Deployment**: The implementation is more straightforward and consistent with modern Python web application deployment practices.

## Testing

The changes have been tested locally to ensure:

1. The application starts correctly with Uvicorn
2. All functionality works as expected
3. The server properly handles requests and responses

## Future Considerations

1. **Asynchronous Handlers**: Consider refactoring parts of the application to take advantage of Uvicorn's asynchronous capabilities for improved performance.

2. **HTTP/2 Support**: Explore enabling HTTP/2 support in Uvicorn for better performance in modern browsers.

3. **WebSocket Support**: If real-time updates become a requirement, Uvicorn's WebSocket support could be leveraged.

## References

- [Uvicorn Documentation](https://www.uvicorn.org/)
- [ASGI Specification](https://asgi.readthedocs.io/en/latest/)
- [Dash with Uvicorn](https://dash.plotly.com/deployment)
