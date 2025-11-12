#!/usr/bin/env python3
"""
OKR Report Generator

This script generates OKR reports with timestamped filenames to avoid overwriting previous reports.
"""

import os
import sys
import time
from datetime import datetime
import subprocess

def generate_okr_report(okr_limit=2):
    """
    Generate OKR report using fellow_ad_accounts from DuckDB.
    
    Args:
        okr_limit (int): Number of OKRs to fetch per user
    """
    # Get environment variables
    db_path = os.getenv("DUCKDB_PATH", "/Users/xiaofei.yin/rill_test.db")
    access_token = os.getenv("FEISHU_ACCESS_TOKEN")
    
    if not access_token:
        print("Error: FEISHU_ACCESS_TOKEN environment variable is required.")
        sys.exit(1)
    
    # Use okr_ingest2.py (fellow_ad_accounts method)
    script_name = "okr_ingest2"
    print("Using fellow_ad_accounts method (okr_ingest2)")
    
    # Build command
    cmd = [
        sys.executable, f"{script_name}.py",
        "--db_path", db_path,
        "--access_token", access_token,
        "--okr_limit", str(okr_limit)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    # Start timing the OKR data fetching
    start_time = time.time()

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print("-" * 50)

        # Calculate and display duration
        end_time = time.time()
        duration = end_time - start_time
        print(f"OKR report generation completed successfully!")
        print(f"Duration: {duration/60:.2f} minutes")
        # List the generated report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = os.path.join("outputs", "reports")
        expected_filename = os.path.join(reports_dir, f"okr_report_{timestamp}.md")
        if os.path.exists(expected_filename):
            print(f"Generated report: {expected_filename}")
            file_size = os.path.getsize(expected_filename)
            print(f"File size: {file_size:,} bytes")
        else:
            print("Warning: Expected report file not found. Check for any errors above.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running OKR report generation: {e}")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate OKR report with timestamped filename")
    parser.add_argument("--okr_limit", type=int, default=2,
                       help="Number of OKRs to fetch per user (default: 2)")
    
    args = parser.parse_args()
    
    generate_okr_report(okr_limit=args.okr_limit)

if __name__ == "__main__":
    main() 