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

def main():
    access_token = "u-cNTe_z5ll6NWnRuH9wLee8hklaLQ5l2riO00l5Mw2fhG"
    db_path = "/Users/xiaofei.yin/rill_test.db"
    okr_limit = 1

    conn = duckdb.connect(db_path)
    try:
        # Limit to 5 users for testing
        rows = conn.execute("""
            SELECT fellow_ad_account FROM onvo_employee_fellow_maturity_info_1d_a
            WHERE
                fellow_emp_status_name = '在职'
                AND is_intern = FALSE
                AND fellow_ad_account IS NOT NULL
                AND fellow_workday_cn_title IN ('乐道区域总经理', '乐道区域副总经理', '乐道销售部负责人', '乐道片区总', '乐道行销大区负责人', '乐道区域行销负责人', '乐道战队长', '乐道行销战队长')
            LIMIT 5
        """).fetchall()
        fellow_ad_accounts = [fa for (fa,) in rows if fa]
    finally:
        conn.close()
    print(f"Processing {len(fellow_ad_accounts)} users for OKR export...")

    # Ensure reports output directory exists
    output_dir = os.path.join("outputs", "reports")
    os.makedirs(output_dir, exist_ok=True)

    # Generate unique filename with timestamp in reports folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = os.path.join(output_dir, f"okr_report_manager_test_{timestamp}.md")

    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("# OKR Report Test\n\n")
        requests_this_minute = 0
        start_time = time.time()
        for idx, fellow_ad_account in enumerate(fellow_ad_accounts):
            print(f"Fetching OKR for fellow_ad_account: {fellow_ad_account}")
            try:
                okr_data = fetch_okr_with_fellow_ad_account(fellow_ad_account, access_token, okr_limit)
                print("API response received")
                # Just write a simple line
                f.write(f"## User: {fellow_ad_account}\n- OKRs fetched\n\n")
            except Exception as e:
                print(f"Error fetching OKR for {fellow_ad_account}: {e}")
                f.write(f"## User: {fellow_ad_account}\n- Error: {e}\n\n")
            requests_this_minute += 1
            # Rate limit: 100 requests per minute
            if requests_this_minute >= 100:
                elapsed = time.time() - start_time
                if elapsed < 60:
                    sleep_time = 60 - elapsed
                    print(f"[Rate Limit] Sleeping for {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                requests_this_minute = 0
                start_time = time.time()
    print(f"Test OKR report written to {report_filename}")

if __name__ == "__main__":
    main()
