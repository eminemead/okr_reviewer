#!/usr/bin/env python3
"""
Direct OKR Metrics Extractor
Extracts metrics from raw OKR JSON data stored in DuckDB.
"""

import re
import duckdb
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


class DirectOKRMetricsExtractor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.metrics_data = []
        # Track all encountered (owner, period) pairs to ensure completeness later
        self.owner_period_pairs = set()

    def _normalize_period_label(self, raw_period: str) -> Optional[str]:
        """Normalize period to month-only label like '8 月'. Return None if no month found."""
        # Match forms like '2025 年 8 月', '2025年8月', '8月', ' 8 月 '
        m = re.search(r'(?:\\d{4}\\s*年\\s*)?([1-9]|1[0-2])\\s*月', raw_period)
        if not m:
            return None
        month = int(m.group(1))
        return f"{month} 月"

    def extract_metrics(self) -> List[Dict]:
        """Extract metrics from raw OKR data in DuckDB."""
        conn = duckdb.connect(self.db_path)
        try:
            # Query raw OKR data
            rows = conn.execute("""
                SELECT user_id, okr_data
                FROM raw_okrs_manager
                WHERE okr_data NOT LIKE '%"error"%'
            """).fetchall()

            for user_id, okr_data_json in rows:
                try:
                    okr_data = json.loads(okr_data_json)
                    self._process_user_okrs(user_id, okr_data)
                except Exception as e:
                    print(f"Error processing OKR data for {user_id}: {e}")
                    continue
        finally:
            conn.close()

        return self.metrics_data

    def _process_user_okrs(self, user_id: str, okr_data: dict):
        """Process OKR data for a single user."""
        okr_list = okr_data.get('data', {}).get('okr_list', [])
        if not okr_list:
            return

        for period in okr_list:
            period_name = period.get('name', '')
            period_normalized = self._normalize_period_label(period_name)
            if not period_normalized:
                continue

            # Record this owner-period
            self.owner_period_pairs.add((user_id, period_normalized))

            objectives = period.get('objective_list', [])
            for obj in objectives:
                obj_content = obj.get('content', '')
                progress_report = obj.get('progress_report', '')
                # Combine objective content and progress report for extraction
                full_content = f"{obj_content} {progress_report}"

                # Extract metrics from objective content
                metrics = self._extract_metrics_from_content(full_content, user_id, period_normalized)
                self.metrics_data.extend(metrics)

                # Also extract from KR contents
                kr_list = obj.get('kr_list', [])
                for kr in kr_list:
                    kr_content = kr.get('content', '')
                    kr_metrics = self._extract_metrics_from_content(kr_content, user_id, period_normalized)
                    self.metrics_data.extend(kr_metrics)

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content text for better matching."""
        # Remove markdown-like formatting if any
        content = re.sub(r'#{1,6}\\s*', '', content)
        # Normalize Chinese punctuation and spaces
        content = re.sub(r'[（）]', '(', content)
        content = re.sub(r'[）]', ')', content)
        content = re.sub(r'[：]', ':', content)
        content = re.sub(r'\\s+', ' ', content).strip()
        return content

    def _parse_value(self, match_str: str) -> Optional[int]:
        """Parse numeric value from string, handling units like 万, 千, w."""
        match_str = match_str.strip()
        # Match number with optional decimal and unit
        m = re.match(r'(\\d+(?:\\.\\d+)?)\\s*(万|千|w)?', match_str)
        if not m:
            return None
        num_str, unit = m.groups()
        try:
            num = float(num_str)
        except ValueError:
            return None
        multiplier = {'万': 10000, '千': 1000, 'w': 10000}.get(unit, 1)
        return int(num * multiplier)

    def _extract_metrics_from_content(self, content: str, owner: str, period: str) -> List[Dict]:
        """Extract metrics from content text."""
        metrics = []

        # Preprocess content
        content = self._preprocess_content(content)

        # Define metric patterns - same as before
        metric_patterns = {
            # Quantitative metrics
            '新增建联量': [
                r'\\b新增?建联[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*人?\\b',
                r'\\b建联量[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*人?\\b',
                r'\\b(?:新增)?建联\\s*\\(\\s*(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)\\s*\\)\\s*(?:人|组|个|批)?\\b',
            ],
            '试驾量': [
                r'\\b(?:试乘试驾|试乘|试驾)[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:个|组|批|人次|次)?\\b',
                r'\\b(?:试乘试驾|试乘|试驾)量[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:个|组|批|人次|次)?\\b',
            ],
            '锁单量': [
                r'\\b(?:锁单|下单|下订|订车|成交)[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:台|辆|个|单)?\\b',
                r'\\b(?:锁单|下单|下订|订车|成交)量[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:台|辆|个|单)?\\b',
            ],
            '交付量': [
                r'\\b(?:交付|交车|提车)[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:台|辆|个|单)?\\b',
                r'\\b(?:交付|交车|提车)量[≥>=\\s:]*?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)[^\\d]*(?:台|辆|个|单)?\\b',
            ],
            '利润值': [
                r'\\b(?:EBIT|利润)[^\\n]{0,5}?(\\d+(?:\\.\\d+)?(?:\\s*万|\\s*千|\\s*w)?)\\b',
            ],
            # Binary metrics
            '建信量': [
                r'\\b建信[^\\n]*?(?:量|触达|次数|场|次|人|组|个|批)\\b',
            ],
            '直播': [
                r'\\b直播[^\\n]*?(?:场|次|量|次数)\\b',
            ],
            '利润': [
                r'\\b利润\\b',
            ],
            '销能': [
                r'\\b销能\\b',
            ],
            '满意度': [
                r'\\b满意度\\b',
            ],
        }

        binary_metrics = {'建信量', '直播', '利润', '销能', '满意度'}
        quantitative_metrics = {'新增建联量', '试驾量', '锁单量', '交付量', '利润值'}

        # Extract metrics
        extracted_values = {metric_type: set() for metric_type in quantitative_metrics}
        for metric_type, patterns in metric_patterns.items():
            if metric_type in quantitative_metrics:
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        value = self._parse_value(match)
                        if value is None or value in extracted_values[metric_type]:
                            continue
                        if value < 0 or value > 1000000:
                            continue
                        extracted_values[metric_type].add(value)
                        metrics.append({
                            'owner': owner,
                            'period': period,
                            'metric_type': metric_type,
                            'value': value,
                            'unit': self._get_unit(metric_type),
                            'objective': content[:200] + '...' if len(content) > 200 else content
                        })
            elif metric_type in binary_metrics:
                mentioned = any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
                if mentioned:
                    metrics.append({
                        'owner': owner,
                        'period': period,
                        'metric_type': metric_type,
                        'value': 1,
                        'unit': self._get_unit(metric_type),
                        'objective': content[:200] + '...' if len(content) > 200 else content
                    })

        return metrics

    def _get_unit(self, metric_type: str) -> str:
        """Get the unit for a metric type."""
        units = {
            '新增建联量': '人',
            '试驾量': '组',
            '锁单量': '台',
            '交付量': '台',
            '利润值': '元',
            '建信量': 'mention',
            '直播': 'mention',
            '利润': 'mention',
            '销能': 'mention',
            '满意度': 'mention'
        }
        return units.get(metric_type, '')

    def create_duckdb_table(self):
        """Create DuckDB table and insert the extracted metrics."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"okr_metrics_{timestamp}"

        con = duckdb.connect(self.db_path)

        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                owner VARCHAR,
                period VARCHAR,
                metric_type VARCHAR,
                value INTEGER,
                unit VARCHAR,
                objective TEXT,
                mate_fellow_nh_name VARCHAR,
                fellow_city_company_name VARCHAR,
                leader_workday_title VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        if self.metrics_data:
            df = pd.DataFrame(self.metrics_data)
            df.drop_duplicates(subset=['owner', 'period', 'metric_type', 'value', 'unit'], inplace=True)
            df.reset_index(drop=True, inplace=True)
            df = (
                df.sort_values('value')
                  .groupby(['owner', 'period', 'metric_type', 'unit'], as_index=False)
                  .agg({'value': 'max', 'objective': 'first'})
            )

            # Ensure every (owner, period) has all metric types
            tracked_metrics = ['新增建联量', '试驾量', '锁单量', '交付量', '建信量', '直播', '利润', '销能', '满意度', '利润值']
            if self.owner_period_pairs:
                all_pairs_df = pd.DataFrame(list(self.owner_period_pairs), columns=['owner', 'period'])
                metrics_df = pd.DataFrame({'metric_type': tracked_metrics})
                all_pairs_df['key'] = 1
                metrics_df['key'] = 1
                full_grid = all_pairs_df.merge(metrics_df, on='key').drop(columns=['key'])
                df = full_grid.merge(df, on=['owner', 'period', 'metric_type'], how='left')

                unit_map = {
                    '新增建联量': '人', '试驾量': '组', '锁单量': '台', '交付量': '台', '利润值': '元',
                    '建信量': 'mention', '直播': 'mention', '利润': 'mention', '销能': 'mention', '满意度': 'mention'
                }
                df['unit'] = df['unit'].fillna(df['metric_type'].map(unit_map))
                try:
                    df['value'] = df['value'].astype('Int64')
                except Exception:
                    pass

            df['id'] = range(1, len(df) + 1)
            con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_okr_unique_{timestamp} ON {table_name}(owner, period, metric_type, value, unit)")
            con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_okr_unique2_{timestamp} ON {table_name}(owner, period, metric_type)")
            con.execute(f"INSERT INTO {table_name} (id, owner, period, metric_type, value, unit, objective) SELECT id, owner, period, metric_type, value, unit, objective FROM df")

            # Update employee_fellow table (same as before)
            try:
                con.execute("ATTACH '/Users/xiaofei.yin/rill_test.db' AS external_db")
                try:
                    con.execute("SELECT 1 FROM external_db.onvo_employee_fellow_maturity_info_1d_a LIMIT 1")
                    con.execute("""
                        CREATE OR REPLACE TABLE employee_fellow AS
                        SELECT fellow_ad_account, mate_fellow_nh_name, fellow_city_company_name,
                               leader_workday_title, fellow_workday_cn_title, department_5_cn_name, department_5_en_name
                        FROM external_db.onvo_employee_fellow_maturity_info_1d_a
                        WHERE fellow_emp_status_name = '在职' AND is_intern = FALSE AND fellow_ad_account IS NOT NULL
                    """)
                except Exception:
                    pass
                con.execute("DETACH external_db")
            except Exception:
                pass

            try:
                exists = con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'employee_fellow'").fetchone()[0]
                if exists:
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS mate_fellow_nh_name VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS fellow_city_company_name VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS leader_workday_title VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS fellow_workday_cn_title VARCHAR")
                    con.execute(f"""
                        UPDATE {table_name} AS m
                        SET mate_fellow_nh_name = e.mate_fellow_nh_name,
                            fellow_city_company_name = e.fellow_city_company_name,
                            leader_workday_title = e.leader_workday_title,
                            fellow_workday_cn_title = e.fellow_workday_cn_title
                        FROM employee_fellow AS e
                        WHERE m.owner = e.fellow_ad_account
                    """)
            except Exception:
                pass

        return con, table_name

    def get_metrics_summary(self, con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
        """Get a summary of metrics by owner and period."""
        return con.execute(f"""
            SELECT owner, period, metric_type, SUM(value) as total_value, COUNT(*) as metric_count, unit
            FROM {table_name}
            GROUP BY owner, period, metric_type, unit
            ORDER BY owner, period, metric_type
        """).df()

    def get_owner_summary(self, con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
        """Get a summary of metrics by owner."""
        return con.execute(f"""
            SELECT owner, metric_type, SUM(value) as total_value, COUNT(*) as metric_count, unit
            FROM {table_name}
            GROUP BY owner, metric_type, unit
            ORDER BY owner, metric_type
        """).df()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract OKR metrics from raw data in DuckDB")
    parser.add_argument("--db-path", default="okr_metrics.db", help="Path to the DuckDB database file")

    args = parser.parse_args()

    extractor = DirectOKRMetricsExtractor(args.db_path)

    print("Extracting metrics from raw OKR data...")
    metrics = extractor.extract_metrics()
    print(f"Extracted {len(metrics)} metrics")

    print("Creating DuckDB table...")
    con, table_name = extractor.create_duckdb_table()

    print(f"\nMetrics Summary by Owner and Period (table: {table_name}):")
    summary = extractor.get_metrics_summary(con, table_name)
    print(summary.head(20))

    print(f"\nOwner Summary (table: {table_name}):")
    owner_summary = extractor.get_owner_summary(con, table_name)
    print(owner_summary.head(20))

    print("\nExample Queries:")
    print("1. Total metrics by type:")
    result = con.execute(f"""
        SELECT metric_type, SUM(value) as total, COUNT(*) as count
        FROM {table_name}
        GROUP BY metric_type
        ORDER BY total DESC
    """).df()
    print(result)

    print("\n2. Top 10 owners by total metrics:")
    result = con.execute(f"""
        SELECT owner, SUM(value) as total_metrics, COUNT(*) as metric_count
        FROM {table_name}
        GROUP BY owner
        ORDER BY total_metrics DESC
        LIMIT 10
    """).df()
    print(result)

    con.close()
    print(f"\nData saved to {args.db_path} with {len(metrics)} records")


if __name__ == "__main__":
    main()
