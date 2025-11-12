#!/usr/bin/env python3
"""
Sequential Script Runner Tool

This tool runs a list of Python scripts in sequence, stopping on the first failure.

Usage:
    python run_sequential.py script1.py script2.py ...

Example:
    python run_sequential.py generate_okr_report.py extract_okr_metrics.py export_metrics.py
"""

import sys
import subprocess
import os
from pathlib import Path

def run_script(script_path, args=None):
    """Run a single script and return success status."""
    if not Path(script_path).exists():
        print(f"Error: {script_path} does not exist")
        return False

    cmd = ["uv", "run", "python", script_path]
    if args:
        cmd.extend(args)

    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, cwd=os.getcwd())
        print(f"✓ {script_path} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_path} failed with exit code {e.returncode}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_sequential.py script1.py [script2.py ...]")
        sys.exit(1)

    scripts = sys.argv[1:]
    print(f"Running {len(scripts)} scripts sequentially...")

    for script in scripts:
        if not run_script(script):
            print("Stopping due to failure.")
            sys.exit(1)

    print("All scripts completed successfully!")

if __name__ == "__main__":
    main()
