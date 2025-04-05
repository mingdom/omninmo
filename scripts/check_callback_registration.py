#!/usr/bin/env python3
"""
Script to check for potential callback registration issues in the Folio codebase.

This script scans the codebase for:
1. Components that define register_callbacks functions
2. Whether these functions are properly imported and called in app.py

Usage:
    python scripts/check_callback_registration.py

Example output:
    Scanning for callback registration issues...
    Found register_callbacks in src/folio/components/summary_cards.py
    ✓ register_callbacks from summary_cards is properly imported in app.py
    ✓ register_callbacks is called in app.py
    Scan complete. No issues found.
"""

import re
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import the logger


def scan_for_callback_registration_issues():
    """Scan the codebase for potential callback registration issues."""
    print("Scanning for callback registration issues...")

    components_dir = project_root / "src" / "folio" / "components"
    app_file = project_root / "src" / "folio" / "app.py"

    # Find all register_callbacks functions in component files
    callback_registrations = []
    for file_path in components_dir.glob("**/*.py"):
        if file_path.is_file() and not file_path.name.startswith("__"):
            with open(file_path) as f:
                content = f.read()
                if re.search(r"def\s+register_callbacks", content):
                    # Get the module name relative to src/folio
                    rel_path = file_path.relative_to(project_root / "src" / "folio")
                    module_name = str(rel_path).replace("/", ".").replace(".py", "")
                    component_name = file_path.stem
                    print(f"Found register_callbacks in {file_path}")
                    callback_registrations.append(
                        (module_name, component_name, file_path)
                    )

    if not callback_registrations:
        print("No register_callbacks functions found in component files.")
        return

    # Check if they're called in app.py
    with open(app_file) as f:
        app_content = f.read()

    issues_found = False

    for module, component_name, file_path in callback_registrations:
        # Check for direct import
        direct_import = re.search(
            rf"from\s+{module}\s+import\s+register_callbacks", app_content
        )
        indirect_import = re.search(
            r"from\s+\.components\s+import\s+register_callbacks", app_content
        )

        if direct_import or indirect_import:
            print(
                f"✓ register_callbacks from {component_name} is properly imported in app.py"
            )
        else:
            print(
                f"❌ WARNING: register_callbacks from {component_name} might not be imported in app.py"
            )
            issues_found = True

        # Check for call to register_callbacks
        if re.search(r"register_callbacks\(app\)", app_content):
            print("✓ register_callbacks is called in app.py")
        else:
            print("❌ WARNING: register_callbacks might not be called in app.py")
            issues_found = True

        # Check for potential duplicate registration
        # This is a heuristic and might have false positives
        register_calls = re.findall(r"register_callbacks\(app\)", app_content)
        if len(register_calls) > 1:
            print(
                f"⚠️ CAUTION: register_callbacks is called {len(register_calls)} times in app.py"
            )
            print("  This might lead to duplicate callback registration.")
            issues_found = True

    # Check for components with callbacks but no register_callbacks function
    for file_path in components_dir.glob("**/*.py"):
        if file_path.is_file() and not file_path.name.startswith("__"):
            with open(file_path) as f:
                content = f.read()
                has_callback = re.search(r"@app\.callback", content)
                has_register = re.search(r"def\s+register_callbacks", content)

                if has_callback and not has_register:
                    print(
                        f"❌ WARNING: {file_path} has callbacks but no register_callbacks function"
                    )
                    issues_found = True

    if issues_found:
        print("\nScan complete. Issues were found that need attention.")
        print(
            "Please review the warnings above and fix any callback registration issues."
        )
    else:
        print("\nScan complete. No issues found.")


if __name__ == "__main__":
    scan_for_callback_registration_issues()
