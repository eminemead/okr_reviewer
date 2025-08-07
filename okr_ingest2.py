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

def okr_to_markdown(user, okr_data):
    md = []
    okr_list = okr_data.get('data', {}).get('okr_list', [])
    if not okr_list:
        md.append(f'# OKR Report for {user}\n_No OKRs found._\n')
        return '\n'.join(md)
    md.append(f'# OKR Report for {user}\n')
    for period in okr_list:
        period_name = period.get('name', '')
        md.append(f'## Period: {period_name}')
        objectives = period.get('objective_list', [])
        if not objectives:
            md.append('_No objectives for this period._\n---')
            continue
        for obj_idx, obj in enumerate(objectives, 1):
            obj_content = obj.get('content', '').strip()
            progress = obj.get('progress_rate', {}).get('percent', 0)
            score = obj.get('score', 0)
            progress_report = obj.get('progress_report', '').strip()
            # Alignments
            aligned = obj.get('aligned_objective_list', [])
            aligning = obj.get('aligning_objective_list', [])
            mentioned = obj.get('mentioned_user_list', [])
            md.append(f'\n### Objective {obj_idx}: {obj_content}')
            md.append(f'- **Progress:** {progress}%')
            md.append(f'- **Score:** {score}')
            if aligned:
                md.append('- **Aligns to:**')
                for a in aligned:
                    owner = a.get('owner', {})
                    md.append(f'    - 目标: {a.get("okr_id", "")}, Owner: {owner.get("user_id", "") if owner else ""} (open_id: {owner.get("open_id", "") if owner else ""})')
            if aligning:
                md.append('- **Aligned by:**')
                for a in aligning:
                    owner = a.get('owner', {})
                    md.append(f'    - 目标: {a.get("okr_id", "")}, Owner: {owner.get("user_id", "") if owner else ""} (open_id: {owner.get("open_id", "") if owner else ""})')
            if mentioned:
                md.append('- **Mentioned:** ' + ', '.join(f'{u.get("user_id", "")} (open_id: {u.get("open_id", "")})' for u in mentioned))
            if progress_report:
                md.append(f'- **Progress Report:** {progress_report}')
            # Key Results
            kr_list = obj.get('kr_list', [])
            if kr_list:
                md.append(f'\n#### Key Results:')
                for kr_idx, kr in enumerate(kr_list, 1):
                    kr_content = kr.get('content', '').strip()
                    kr_progress = kr.get('progress_rate', {}).get('percent', 0)
                    kr_score = kr.get('score', 0)
                    md.append(f'{kr_idx}. {kr_content}')
                    md.append(f'    - Progress: {kr_progress}%')
                    md.append(f'    - Score: {kr_score}')
            md.append('\n---')
    return '\n'.join(md)

def main(args):
    conn = duckdb.connect(args.db_path)
    try:
        # Query the new source table with filters, ensuring fellow_ad_account is not null, and limit to 500 rows
        rows = conn.execute("""
            SELECT fellow_ad_account FROM onvo_employee_fellow_maturity_info_1d_a
            WHERE fellow_emp_status_name = '在职' AND is_intern = false AND is_fellow = true AND fellow_ad_account IS NOT NULL
            LIMIT 3000
        """).fetchall()
        fellow_ad_accounts = [fa for (fa,) in rows if fa]
    finally:
        conn.close()
    print(f"Processing {len(fellow_ad_accounts)} users for OKR export...")
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"okr_report_{timestamp}.md"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("# OKR Report\n\n")
        requests_this_minute = 0
        start_time = time.time()
        for idx, fellow_ad_account in enumerate(fellow_ad_accounts):
            print(f"Fetching OKR for fellow_ad_account: {fellow_ad_account}")
            try:
                okr_data = fetch_okr_with_fellow_ad_account(fellow_ad_account, args.access_token, args.okr_limit)
                print(json.dumps(okr_data, indent=2, ensure_ascii=False))
                md = okr_to_markdown(fellow_ad_account, okr_data)
                f.write(md + "\n\n")
            except Exception as e:
                print(f"Error fetching OKR for {fellow_ad_account}: {e}")
                f.write(f"## User: {fellow_ad_account}\n- Error fetching OKR: {e}\n\n")
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
    print(f"OKR report written to {report_filename}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch OKRs for all fellow_ad_accounts in DuckDB and write to markdown report.")
    parser.add_argument("--db_path", type=str, default=os.getenv("DUCKDB_PATH", "/Users/xiaofei.yin/rill_test.db"), help="Path to DuckDB database.")
    parser.add_argument("--access_token", type=str, default=os.getenv("FEISHU_ACCESS_TOKEN"), help="Feishu API access token.")
    parser.add_argument("--okr_limit", type=int, default=2, help="Limit for number of OKRs to fetch per user.")
    args = parser.parse_args()
    main(args) 