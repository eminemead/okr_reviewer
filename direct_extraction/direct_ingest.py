#!/usr/bin/env python3
"""
Direct OKR Data Ingestor for Managers
Fetches OKR data from Feishu API and stores raw JSON in DuckDB.
"""

import duckdb
import requests
import json
import os
import time
from datetime import datetime


def fetch_okr_with_fellow_ad_account(user_id, access_token, limit=2):
    url = f"https://open.feishu.cn/open-apis/okr/v1/users/{user_id}/okrs"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "lang": "zh_cn",
        "limit": limit,
        "offset": 0,
        "user_id_type": "user_id"
    }
    print(f"Requesting: {url} with params {params}")
    response = requests.get(url, headers=headers, params=params)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print("Error details:", response.text)
        raise
    return response.json()


def main(args):
    conn = duckdb.connect(args.db_path)
    try:
        # Create raw OKR table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_okrs_manager (
                user_id VARCHAR,
                okr_data JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Query the new source table with filters for managers, ensuring fellow_ad_account is not null
        rows = conn.execute("""
            SELECT fellow_ad_account FROM onvo_employee_fellow_maturity_info_1d_a
            WHERE
                fellow_emp_status_name = '在职'
                AND is_intern = FALSE
                AND fellow_ad_account IS NOT NULL
                AND fellow_workday_cn_title IN ('乐道区域总经理', '乐道区域副总经理', '乐道销售部负责人', '乐道片区总', '乐道行销大区负责人', '乐道区域行销负责人', '乐道战队长', '乐道行销战队长')
        """).fetchall()
        fellow_ad_accounts = [fa for (fa,) in rows if fa]
    finally:
        conn.close()

    print(f"Processing {len(fellow_ad_accounts)} users for OKR data ingest...")

    # Reconnect for insertion
    conn = duckdb.connect(args.db_path)
    try:
        requests_this_minute = 0
        start_time = time.time()

        for idx, fellow_ad_account in enumerate(fellow_ad_accounts):
            print(f"Fetching OKR for fellow_ad_account: {fellow_ad_account}")
            try:
                okr_data = fetch_okr_with_fellow_ad_account(fellow_ad_account, args.access_token, args.okr_limit)
                print(json.dumps(okr_data, indent=2, ensure_ascii=False))

                # Insert raw data into DB
                conn.execute("""
                    INSERT INTO raw_okrs_manager (user_id, okr_data)
                    VALUES (?, ?)
                """, (fellow_ad_account, json.dumps(okr_data, ensure_ascii=False)))

            except Exception as e:
                print(f"Error fetching OKR for {fellow_ad_account}: {e}")
                # Insert error record
                error_data = {"error": str(e), "timestamp": datetime.now().isoformat()}
                conn.execute("""
                    INSERT INTO raw_okrs_manager (user_id, okr_data)
                    VALUES (?, ?)
                """, (fellow_ad_account, json.dumps(error_data)))

            requests_this_minute += 1
            # Rate limit: 100 requests per minute
            if requests_this_minute >= 100:
                elapsed = time.time() - start_time
                if elapsed < 60:
                    sleep_time = 60 - elapsed
                    print(f"[Rate Limit] Sleeping for {sleep_time:.1f} seconds to respect 100 requests/minute limit...")
                    time.sleep(sleep_time)
                requests_this_minute = 0
                start_time = time.time()

        print(f"Raw OKR data ingested into raw_okrs_manager table")
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch OKRs for all manager fellow_ad_accounts and store raw data in DuckDB.")
    parser.add_argument("--db_path", type=str, default=os.getenv("DUCKDB_PATH", "/Users/xiaofei.yin/rill_test.db"), help="Path to DuckDB database.")
    parser.add_argument("--access_token", type=str, default=os.getenv("FEISHU_ACCESS_TOKEN"), help="Feishu API access token.")
    parser.add_argument("--okr_limit", type=int, default=2, help="Limit for number of OKRs to fetch per user.")
    args = parser.parse_args()
    main(args)
