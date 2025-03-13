#!/usr/bin/env python3
"""
Script to start the MLflow UI for viewing model training results.
"""

import os
import sys
import argparse
import subprocess

def main():
    """Start the MLflow UI server"""
    parser = argparse.ArgumentParser(description='Start the MLflow UI server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on (default: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the server on (default: 127.0.0.1)')
    args = parser.parse_args()
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Set the MLflow tracking URI
    mlruns_dir = os.path.join(project_root, 'logs/mlruns')
    tracking_uri = f"file:{mlruns_dir}"
    
    print(f"Starting MLflow UI on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")
    
    # Start the MLflow UI
    cmd = [
        "mlflow", "ui",
        "--backend-store-uri", tracking_uri,
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nMLflow UI server stopped.")
    except Exception as e:
        print(f"Error starting MLflow UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 