#!/usr/bin/env python3
"""
Direct OKR Pipeline Orchestrator
Runs the direct ingest and extract process.
"""

import subprocess
import os
import time
from datetime import datetime


def run_pipeline(okr_limit=2):
    """
    Run the direct OKR pipeline: ingest raw data, then extract metrics.

    Args:
        okr_limit (int): Number of OKRs to fetch per user
    """
    # Get environment variables
    db_path = os.getenv("DUCKDB_PATH", "/Users/xiaofei.yin/rill_test.db")
    access_token = os.getenv("FEISHU_ACCESS_TOKEN")

    if not access_token:
        print("Error: FEISHU_ACCESS_TOKEN environment variable is required.")
        return

    print("Starting direct OKR pipeline...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    start_time = time.time()

    try:
        # Step 1: Ingest raw OKR data
        print("Step 1: Ingesting raw OKR data...")
        ingest_cmd = [
            "python3", "direct_ingest.py",
            "--db_path", db_path,
            "--access_token", access_token,
            "--okr_limit", str(okr_limit)
        ]
        result = subprocess.run(ingest_cmd, check=True, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Step 2: Extract metrics from raw data
        print("Step 2: Extracting metrics from raw data...")
        extract_cmd = [
            "python3", "direct_extract.py",
            "--db-path", db_path
        ]
        result = subprocess.run(extract_cmd, check=True, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        print("-" * 50)
        end_time = time.time()
        duration = end_time - start_time
        print("Direct OKR pipeline completed successfully!")
        print(".2f")

    except subprocess.CalledProcessError as e:
        print(f"Error in pipeline: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run direct OKR pipeline")
    parser.add_argument("--okr_limit", type=int, default=2,
                         help="Number of OKRs to fetch per user (default: 2)")

    args = parser.parse_args()

    run_pipeline(okr_limit=args.okr_limit)


if __name__ == "__main__":
    main()
