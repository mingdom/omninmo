# Docker Containerization of Folio Application

**Date:** 2025-04-02
**Author:** Dong Ming
**Status:** Completed

## Overview

This devlog documents the process of containerizing the Folio application using Docker. The goal was to create a Docker container that can run the Folio application and be accessed from the host machine.

## Implementation Details

### Initial Setup

1. Created a Dockerfile with Python 3.11 as the base image
2. Installed necessary dependencies
3. Copied application code
4. Configured the container to run the application

### Issues Encountered and Workarounds

#### Issue 1: NotRequired Type Error

The first issue we encountered was with the `NotRequired` type from the `typing` module. The application was using `NotRequired` which is only available in Python 3.11+, but our initial container was using Python 3.9.

**Error:**
```
ImportError: cannot import name 'NotRequired' from 'typing' (/usr/local/lib/python3.9/typing.py)
```

**Workarounds tried:**
1. Switching to Python 3.11 (still had issues)
2. Using `typing_extensions.NotRequired` instead of `typing.NotRequired`
3. Modifying the import statement to use a try/except block to handle different Python versions

**Final solution:**
We switched to Python 3.11 and modified the import statement in `data_model.py` to use the standard `typing.NotRequired`.

#### Issue 2: Module Import Errors

After fixing the `NotRequired` issue, we encountered problems with module imports. The application was using absolute imports (e.g., `from src.data_fetcher_factory import create_data_fetcher`), but these weren't working in the container environment.

**Error:**
```
ModuleNotFoundError: No module named 'src.data_fetcher_factory'
```

**Workarounds tried:**
1. Copying specific files to the container
2. Modifying the Python path

**Final solution:**
1. Copied the entire `src` directory to maintain the project structure
2. Modified import statements in `utils.py` to use relative imports:
   - Changed `from src.data_fetcher_factory import create_data_fetcher` to `from ..data_fetcher_factory import create_data_fetcher`
   - Changed `from src.lab.option_utils import ...` to `from ..lab.option_utils import ...`

#### Issue 3: Network Binding

The application was binding to `127.0.0.1` inside the container, which meant it wasn't accessible from outside the container.

**Error:**
Connection reset when trying to access the application from the host machine.

**Final solution:**
1. Modified `app.py` to accept a `--host` parameter
2. Updated the Dockerfile to run the application with `--host 0.0.0.0` to bind to all interfaces

### User Experience Improvements

We made several improvements to enhance the user experience when running the application in a Docker container:

1. **Improved Startup Message**: Modified the application to display a clear message indicating that it's running in a Docker container and providing the correct URL to access it from the host machine:

```
🚀 Folio is running inside a Docker container!
📊 Access the dashboard at: http://localhost:8050
💻 (The app is bound to 0.0.0.0:8050 inside the container)
```

This addresses the common confusion where the application reports it's running on `0.0.0.0:8050` inside the container, but users need to access it via `localhost:8050` from the host machine.

### Remaining Questions/Issues

1. **Import Structure**: The current import structure is not ideal. We're using a mix of absolute and relative imports, which can be confusing and error-prone. A more consistent approach would be better.

2. **Module Organization**: The application's module organization could be improved to make it more container-friendly. Currently, we're copying the entire `src` directory, but a more modular approach would be better.

3. **Environment Variables**: We're setting environment variables in the docker-compose.yml file, but a more comprehensive approach to configuration management would be beneficial.

## Final Implementation

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8050

# Install only the necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install all required packages
RUN pip install --no-cache-dir \
    dash==2.14.2 \
    dash-bootstrap-components==1.5.0 \
    yfinance>=0.2.37 \
    PyYAML==6.0.1 \
    requests==2.31.0 \
    scipy>=1.11.0 \
    pandas==2.2.1 \
    numpy==1.26.4

# Copy all necessary application code
COPY src ./src

# Expose the port
EXPOSE 8050

# Run the application with Python directly
CMD ["python", "-m", "src.folio.app", "--port", "8050", "--host", "0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  folio:
    image: folio:latest
    ports:
      - "8050:8050"
    environment:
      - PORT=8050
      - PYTHONPATH=/app
      - DATA_SOURCE=yfinance
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped
```

### Code Changes

1. Modified `src/folio/app.py` to add support for the `--host` parameter:

```python
parser.add_argument(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Host to run the server on",
)
```

2. Updated the `run_server` call to use the host parameter:

```python
app.run_server(debug=args.debug, port=args.port, host=args.host)
```

3. Added improved startup message to help users access the application:

```python
# Display a helpful message about where to access the app
is_docker = os.path.exists('/.dockerenv')
if is_docker and args.host == '0.0.0.0':
    logger.info(f"\n\n🚀 Folio is running inside a Docker container!")
    logger.info(f"📊 Access the dashboard at: http://localhost:{args.port}")
    logger.info(f"💻 (The app is bound to {args.host}:{args.port} inside the container)\n")
else:
    logger.info(f"\n\n🚀 Folio is running!")
    logger.info(f"📊 Access the dashboard at: http://localhost:{args.port}\n")
```

4. Modified `src/folio/utils.py` to use relative imports:

```python
from ..data_fetcher_factory import create_data_fetcher
from ..lab.option_utils import calculate_option_delta, parse_option_description
```

## Conclusion

The Folio application is now successfully containerized and can be run using Docker. The application is accessible at http://localhost:8050 when the container is running.

While we've implemented several workarounds to get the application running in a container, there are still some architectural improvements that could be made to make the application more container-friendly.
