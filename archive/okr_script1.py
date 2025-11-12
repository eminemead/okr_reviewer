import duckdb
import requests
import json
import os
from typing import List, Dict

def get_fellow_ad_accounts_from_duckdb(db_path: str, table_name: str, column_name: str = "fellow_ad_account") -> List[str]:
    """
    Fetches the list of emails from the specified DuckDB table and column,
    concatenating '@nio.com' to the alias to form the full email address.
    """
    conn = duckdb.connect(db_path)
    try:
        query = f"SELECT {column_name} || '@nio.com' AS email FROM {table_name} WHERE {column_name} IS NOT NULL"
        result = conn.execute(query).fetchall()
        return [row[0] for row in result]
    finally:
        conn.close()

def get_open_ids_from_feishu(emails: List[str], access_token: str) -> Dict:
    """
    Calls the Feishu batch_get_id API to get open_ids for the given emails.
    Processes emails in batches of 50 to comply with API limits.
    """
    url = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    all_user_list = []
    batch_size = 50
    for i in range(0, len(emails), batch_size):
        batch_emails = emails[i:i + batch_size]
        payload = {"emails": batch_emails}
        print(f"\n[DEBUG] Sending batch {i//batch_size + 1}/{(len(emails) + batch_size - 1)//batch_size} to Feishu API:")
        print(f"[DEBUG] Emails: {batch_emails}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        try:
            response.raise_for_status()
            batch_result = response.json()
            print(f"[DEBUG] Feishu API response: {json.dumps(batch_result, indent=2, ensure_ascii=False)}")
            batch_user_list = batch_result.get("data", {}).get("user_list", [])
            all_user_list.extend(batch_user_list)
        except Exception as e:
            print(f"Feishu API error for batch {i//batch_size + 1}: {e}\nResponse: {response.text}")
            continue
    return {
        "code": 0,
        "data": {
            "user_list": all_user_list
        },
        "msg": "success"
    }

def store_open_ids_to_duckdb(db_path: str, table_name: str, user_list: list):
    """
    Stores email and open_id pairs into a DuckDB table.
    """
    conn = duckdb.connect(db_path)
    try:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                email TEXT PRIMARY KEY,
                open_id TEXT
            )
        ''')
        for user in user_list:
            email = user.get("email", "")
            open_id = user.get("open_id")
            if email:
                conn.execute(
                    f"INSERT OR REPLACE INTO {table_name} (email, open_id) VALUES (?, ?)",
                    (email, open_id)
                )
                if not open_id:
                    print(f"Warning: No open_id for {email}")
    except Exception as e:
        print(f"Error storing open_ids to DuckDB: {e}")
    finally:
        conn.close()

def main(args):
    if not args.access_token:
        raise ValueError("Feishu access token must be provided via --access_token or FEISHU_ACCESS_TOKEN env var.")
    emails = get_fellow_ad_accounts_from_duckdb(args.db_path, args.table, args.column)
    print(f"Fetched {len(emails)} emails from DuckDB.")
    if not emails:
        print("No emails found.")
        return
    result = get_open_ids_from_feishu(emails, args.access_token)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    user_list = result.get("data", {}).get("user_list", [])
    if user_list:
        store_open_ids_to_duckdb(args.db_path, "feishu_open_ids", user_list)
        print(f"Stored {len(user_list)} open_ids to DuckDB table 'feishu_open_ids'.")
    else:
        print("No open_ids to store.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Feishu open_ids from DuckDB emails.")
    parser.add_argument("--db_path", type=str, default=os.getenv("DUCKDB_PATH", "/Users/xiaofei.yin/rill_test.db"), help="Path to DuckDB database.")
    parser.add_argument("--table", type=str, default=os.getenv("DUCKDB_TABLE", "onvo_employee_fellow_maturity_info_1d_a"), help="DuckDB table name.")
    parser.add_argument("--column", type=str, default=os.getenv("DUCKDB_COLUMN", "fellow_ad_account"), help="Column name for emails.")
    parser.add_argument("--access_token", type=str, default=os.getenv("FEISHU_ACCESS_TOKEN"), help="Feishu API access token.")
    args = parser.parse_args()
    main(args) 