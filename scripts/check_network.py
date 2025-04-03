#!/usr/bin/env python3
"""
Network connectivity test script for Docker containers.

This script checks network connectivity from inside a Docker container,
including binding to different interfaces and testing external connectivity.

Usage:
    python check_network.py [--bind-test] [--external-test]

Example in Docker:
    docker exec omninmo-folio-1 python /app/scripts/check_network.py --bind-test
"""

import argparse
import socket
import subprocess
import sys
import time


def check_port_binding(host, port):
    """
    Test if we can bind to a specific host and port.
    
    Args:
        host (str): Host to bind to
        port (int): Port to bind to
        
    Returns:
        bool: True if binding successful, False otherwise
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        print(f"✅ Successfully bound to {host}:{port}")
        result = True
    except Exception as e:
        print(f"❌ Failed to bind to {host}:{port}: {e}")
        result = False
    finally:
        sock.close()
    return result


def run_binding_tests(port=8050):
    """
    Run a series of binding tests on different interfaces.
    
    Args:
        port (int): Port to test binding on
    """
    print("\n--- Testing port binding ---")
    interfaces = [
        "127.0.0.1",  # Localhost only
        "0.0.0.0",    # All interfaces
    ]
    
    for interface in interfaces:
        check_port_binding(interface, port)


def check_external_connectivity():
    """Test connectivity to external services."""
    print("\n--- Testing external connectivity ---")
    
    # Test DNS resolution
    print("\nTesting DNS resolution:")
    hosts = ["google.com", "yahoo.com", "finance.yahoo.com", "github.com"]
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ Successfully resolved {host} to {ip}")
        except socket.gaierror as e:
            print(f"❌ Failed to resolve {host}: {e}")
    
    # Test HTTP connectivity
    print("\nTesting HTTP connectivity:")
    urls = ["https://google.com", "https://finance.yahoo.com"]
    for url in urls:
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=10
            )
            status_code = result.stdout.strip()
            if result.returncode == 0 and status_code.startswith("2") or status_code.startswith("3"):
                print(f"✅ Successfully connected to {url} (Status: {status_code})")
            else:
                print(f"❌ Failed to connect to {url} (Status: {status_code})")
        except subprocess.SubprocessError as e:
            print(f"❌ Error connecting to {url}: {e}")


def main():
    """Main function to run network tests."""
    parser = argparse.ArgumentParser(description="Test network connectivity in Docker container")
    parser.add_argument("--bind-test", action="store_true", help="Run port binding tests")
    parser.add_argument("--external-test", action="store_true", help="Run external connectivity tests")
    parser.add_argument("--port", type=int, default=8050, help="Port to test binding on")
    
    args = parser.parse_args()
    
    # If no specific tests are requested, run all tests
    run_all = not (args.bind_test or args.external_test)
    
    print(f"Running network tests on {socket.gethostname()}")
    print(f"Python version: {sys.version}")
    
    # Get network interfaces
    print("\n--- Network interfaces ---")
    try:
        subprocess.run(["ip", "addr"], check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            subprocess.run(["ifconfig"], check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Could not get network interfaces")
    
    if args.bind_test or run_all:
        run_binding_tests(args.port)
    
    if args.external_test or run_all:
        check_external_connectivity()


if __name__ == "__main__":
    main()
