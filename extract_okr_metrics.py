#!/usr/bin/env python3
"""
Extract OKR metrics by owner by monthly from markdown file and store in DuckDB table.
"""

import re
import duckdb
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class OKRMetricsExtractor:
    def __init__(self, markdown_file: str):
        self.markdown_file = markdown_file
        self.metrics_data = []
        # Track all encountered (owner, period) pairs to ensure completeness later
        self.owner_period_pairs = set()
    
    def _normalize_period_label(self, raw_period: str) -> Optional[str]:
        """Normalize period to month-only label like '8 月'. Return None if no month found."""
        # Match forms like '2025 年 8 月', '2025年8月', '8月', ' 8 月 '
        m = re.search(r'(?:\d{4}\s*年\s*)?([1-9]|1[0-2])\s*月', raw_period)
        if not m:
            return None
        month = int(m.group(1))
        return f"{month} 月"
        
    def extract_metrics(self) -> List[Dict]:
        """Extract metrics from the markdown file."""
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by OKR reports for each person
        reports = content.split('# OKR Report for ')
        
        for report in reports[1:]:  # Skip the first empty split
            try:
                # Extract owner name
                owner_match = re.match(r'^([^\n]+)', report)
                if not owner_match:
                    continue
                owner = owner_match.group(1).strip()
                
                # Extract periods and their objectives
                periods = self._extract_periods(report)
                
                for period, objectives in periods:
                    # Record this owner-period even if no metrics matched
                    self.owner_period_pairs.add((owner, period))
                    # If objectives list is empty, no metrics will be extracted (which is correct)
                    for objective in objectives:
                        metrics = self._extract_metrics_from_objective(objective, owner, period)
                        self.metrics_data.extend(metrics)
                        
            except Exception as e:
                print(f"Error processing report: {e}")
                continue
        
        return self.metrics_data
    
    def _extract_periods(self, report: str) -> List[Tuple[str, List[str]]]:
        """Extract periods and their objectives from a report."""
        periods = []
        
        # Find all period sections
        period_pattern = r'## Period: ([^\n]+)\n(.*?)(?=## Period:|$)'
        period_matches = re.findall(period_pattern, report, re.DOTALL)
        
        for period_match in period_matches:
            period_raw = period_match[0].strip()
            period = self._normalize_period_label(period_raw)
            if not period:
                # Skip non-month periods
                continue
            period_content = period_match[1].strip()
            
            # Handle periods with no objectives - still record them but with empty objectives list
            if '_No objectives for this period._' in period_content:
                # Return empty objectives list instead of skipping
                periods.append((period, []))
                continue
            
            # Extract objectives
            objectives = self._extract_objectives(period_content)
            periods.append((period, objectives))
        
        return periods
    
    def _extract_objectives(self, content: str) -> List[str]:
        """Extract objectives from period content."""
        objectives = []
        
        # Find all objective sections
        objective_pattern = r'### Objective \d+: ([^\n]+)\n(.*?)(?=### Objective \d+:|$)'
        objective_matches = re.findall(objective_pattern, content, re.DOTALL)
        
        for objective_match in objective_matches:
            objective_title = objective_match[0].strip()
            objective_content = objective_match[1].strip()
            objectives.append(f"### {objective_title}\n{objective_content}")
        
        return objectives
    
    def _extract_metrics_from_objective(self, objective: str, owner: str, period: str) -> List[Dict]:
        """Extract metrics from a single objective."""
        metrics = []
        
        # Define metric patterns - quantitative metrics extract numbers, binary metrics check for mentions
        metric_patterns = {
            # Quantitative metrics (extract numbers)
            '新增建联量': [
                r'新增?建联[≥>=\s：:]*?(\d+)',
                r'建联量[≥>=\s：:]*?(\d+)',
                r'(?:新增)?建联[（(（]?(\d+)[）)]?人',
                r'(?:新增)?建联[（(（]?(\d+)[）)]?组',
                r'(?:新增)?建联[（(（]?(\d+)[）)]?个',
                r'(?:新增)?建联[（(（]?(\d+)[）)]?批',
                r'(\d+)人[^\n]*建联',
                r'(\d+)组[^\n]*建联',
                r'(\d+)个[^\n]*建联',
                r'(\d+)批[^\n]*建联'
            ],
            '试驾量': [
                r'(?:试乘试驾|试乘|试驾)[≥>=\s：:]*?(\d+)',
                r'(?:试乘试驾|试乘|试驾)量[≥>=\s：:]*?(\d+)',
                r'(?:试乘试驾|试乘|试驾)[（(（]?(\d+)[）)]?个',
                r'(?:试乘试驾|试乘|试驾)[（(（]?(\d+)[）)]?组',
                r'(?:试乘试驾|试乘|试驾)[（(（]?(\d+)[）)]?批',
                r'(?:试乘试驾|试乘|试驾)[（(（]?(\d+)[）)]?人次',
                r'(?:试乘试驾|试乘|试驾)[（(（]?(\d+)[）)]?次',
                r'(\d+)[^\n]*?(?:试乘试驾|试乘|试驾)'
            ],
            '锁单量': [
                r'(?:锁单|下单|下订|订车|成交)[≥>=\s：:]*?(\d+)',
                r'(?:锁单|下单|下订|订车|成交)量[≥>=\s：:]*?(\d+)',
                r'(?:锁单|下单|下订|订车|成交)[（(（]?(\d+)[）)]?台',
                r'(?:锁单|下单|下订|订车|成交)[（(（]?(\d+)[）)]?辆',
                r'(?:锁单|下单|下订|订车|成交)[（(（]?(\d+)[）)]?个',
                r'(?:锁单|下单|下订|订车|成交)[（(（]?(\d+)[）)]?单',
                r'L60锁单(\d+)',
                r'L90锁单(\d+)',
                r'(\d+)台[^\n]*?(?:锁单|下单|下订|订车|成交)'
            ],
            '交付量': [
                r'(?:交付|交车|提车)[≥>=\s：:]*?(\d+)',
                r'(?:交付|交车|提车)量[≥>=\s：:]*?(\d+)',
                r'(?:交付|交车|提车)[（(（]?(\d+)[）)]?台',
                r'(?:交付|交车|提车)[（(（]?(\d+)[）)]?辆',
                r'(?:交付|交车|提车)[（(（]?(\d+)[）)]?个',
                r'(?:交付|交车|提车)[（(（]?(\d+)[）)]?单',
                r'L60交付(\d+)',
                r'L90交付(\d+)',
                r'(\d+)台[^\n]*?(?:交付|交车|提车)'
            ],
            # Binary metrics (1 if mentioned, 0 if not)
            '建信量': [
                r'建信[^\n]*?(?:量|触达|次数|场|次|人|组|个|批)',
                r'(?:量|触达|次数|场|次)[^\n]*?建信',
                r'建信'
            ],
            '直播': [
                r'直播[^\n]*?(?:场|次|量|次数)',
                r'(?:场|次|量|次数)[^\n]*?直播',
                r'直播'
            ],
            '利润': [
                r'利润',
                r'盈利',
                r'收益'
            ],
            '销能': [
                r'销能',
                r'招聘',
                r'招人',
                r'招聘[^\n]*?(?:量|人数|人次|次)',
                r'招人[^\n]*?(?:量|人数|人次|次)',
                r'(?:量|人数|人次|次)[^\n]*?(?:招聘|招人)'
            ],
            '满意度': [
                r'满意度',
                r'满意[^\n]*?(?:率|度)',
                r'用户[^\n]*?满意',
                r'客户[^\n]*?满意'
            ]
        }
        
        # Define which metrics are binary vs quantitative
        binary_metrics = {'建信量', '直播', '利润', '销能', '满意度'}
        quantitative_metrics = {'新增建联量', '试驾量', '锁单量', '交付量'}

        # Extract metrics for each type
        for metric_type, patterns in metric_patterns.items():
            if metric_type in quantitative_metrics:
                # Quantitative metrics: extract numbers
                seen_values_for_metric: set[int] = set()
                for pattern in patterns:
                    matches = re.findall(pattern, objective)
                    for match in matches:
                        try:
                            value = int(match)
                        except ValueError:
                            continue
                        # De-duplicate overlapping regex captures that yield the same numeric value
                        if value in seen_values_for_metric:
                            continue
                        seen_values_for_metric.add(value)
                        metrics.append({
                            'owner': owner,
                            'period': period,
                            'metric_type': metric_type,
                            'value': value,
                            'unit': self._get_unit(metric_type),
                            'objective': objective[:200] + '...' if len(objective) > 200 else objective
                        })
            elif metric_type in binary_metrics:
                # Binary metrics: check if any pattern matches (1 if mentioned, 0 if not)
                mentioned = False
                for pattern in patterns:
                    if re.search(pattern, objective, re.IGNORECASE):
                        mentioned = True
                        break
                # Only add if mentioned (value=1), we'll handle value=0 at the database level
                if mentioned:
                    metrics.append({
                        'owner': owner,
                        'period': period,
                        'metric_type': metric_type,
                        'value': 1,
                        'unit': self._get_unit(metric_type),
                        'objective': objective[:200] + '...' if len(objective) > 200 else objective
                    })
        
        return metrics
    
    def _get_unit(self, metric_type: str) -> str:
        """Get the unit for a metric type."""
        units = {
            # Quantitative metrics
            '新增建联量': '人',
            '试驾量': '组',
            '锁单量': '台',
            '交付量': '台',
            # Binary metrics
            '建信量': 'mention',
            '直播': 'mention',
            '利润': 'mention',
            '销能': 'mention',
            '满意度': 'mention'
        }
        return units.get(metric_type, '')
    
    def create_duckdb_table(self, db_path: str = ':memory:'):
        """Create DuckDB table and insert the extracted metrics."""
        # Generate timestamp for table partitioning
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"okr_metrics_{timestamp}"

        # Connect to DuckDB
        con = duckdb.connect(db_path)

        # Create table with timestamp partition
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
        
        # Convert to DataFrame and insert
        if self.metrics_data:
            df = pd.DataFrame(self.metrics_data)
            # Drop exact duplicate rows to prevent repeated records
            df.drop_duplicates(
                subset=['owner', 'period', 'metric_type', 'value', 'unit'],
                inplace=True
            )
            df.reset_index(drop=True, inplace=True)
            # Collapse multiple values within the same owner/period/metric_type to a single logical record
            # Strategy: keep the maximum value per group, and keep a representative objective
            df = (
                df.sort_values('value')
                  .groupby(['owner', 'period', 'metric_type', 'unit'], as_index=False)
                  .agg({'value': 'max', 'objective': 'first'})
            )
            
            # Ensure every (owner, period) has all 9 metric types, with NULL value if missing
            tracked_metrics = ['新增建联量', '试驾量', '锁单量', '交付量', '建信量', '直播', '利润', '销能', '满意度']
            if self.owner_period_pairs:
                all_pairs_df = pd.DataFrame(list(self.owner_period_pairs), columns=['owner', 'period'])
                metrics_df = pd.DataFrame({'metric_type': tracked_metrics})
                # Cartesian product to generate full grid
                all_pairs_df['key'] = 1
                metrics_df['key'] = 1
                full_grid = all_pairs_df.merge(metrics_df, on='key').drop(columns=['key'])
                # Left join existing values
                df = full_grid.merge(df, on=['owner', 'period', 'metric_type'], how='left')
                # Fill unit using mapping when missing
                unit_map = {
                    '新增建联量': '人',
                    '试驾量': '组',
                    '锁单量': '台',
                    '交付量': '台',
                    '建信量': 'mention',
                    '直播': 'mention',
                    '利润': 'mention',
                    '销能': 'mention',
                    '满意度': 'mention'
                }
                df['unit'] = df['unit'].fillna(df['metric_type'].map(unit_map))
                # Ensure integer nullable dtype for value so NULLs are preserved
                try:
                    df['value'] = df['value'].astype('Int64')
                except Exception:
                    pass
            # Add an id column to the DataFrame after de-duplication
            df['id'] = range(1, len(df) + 1)
            # No need to delete data since we're creating a new partitioned table
            # Add a unique index to protect against duplicates at the DB level
            con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_okr_unique_{timestamp} ON {table_name}(owner, period, metric_type, value, unit)")
            con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_okr_unique2_{timestamp} ON {table_name}(owner, period, metric_type)")
            con.execute(f"INSERT INTO {table_name} (id, owner, period, metric_type, value, unit, objective) SELECT id, owner, period, metric_type, value, unit, objective FROM df")
            
            # Update employee_fellow table from external source database
            try:
                # Attach external database
                con.execute("ATTACH '/Users/xiaofei.yin/rill_test.db' AS external_db")

                # Try to query the source table directly (will fail if it doesn't exist)
                try:
                    con.execute("SELECT 1 FROM external_db.onvo_employee_fellow_maturity_info_1d_a LIMIT 1")
                    print("Updating employee_fellow table from external source...")
                    # Create or replace employee_fellow table from external source
                    con.execute("""
                        CREATE OR REPLACE TABLE employee_fellow AS
                        SELECT
                            fellow_ad_account,
                            mate_fellow_nh_name,
                            fellow_city_company_name,
                            leader_workday_title,
                            fellow_workday_cn_title,
                            department_5_cn_name,
                            department_5_en_name
                        FROM external_db.onvo_employee_fellow_maturity_info_1d_a
                        WHERE
                            fellow_emp_status_name = '在职'
                            AND is_intern = FALSE
                            AND fellow_ad_account IS NOT NULL
                    """)
                    print("employee_fellow table updated successfully")
                except Exception as table_error:
                    print(f"Warning: Source table onvo_employee_fellow_maturity_info_1d_a not found or not accessible: {table_error}")

                # Detach external database
                con.execute("DETACH external_db")

            except Exception as e:
                print(f"Warning: Could not update employee_fellow table from external source: {e}")
                try:
                    con.execute("DETACH external_db")
                except:
                    pass

            # Attempt to enrich with employee attributes if the source table exists
            try:
                exists = con.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name = 'employee_fellow'
                """).fetchone()[0]
                if exists:
                    # Ensure columns exist (idempotent)
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS mate_fellow_nh_name VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS fellow_city_company_name VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS leader_workday_title VARCHAR")
                    con.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS fellow_workday_cn_title VARCHAR")
                    # Populate columns via left join
                    con.execute(f"""
                        UPDATE {table_name} AS m
                        SET mate_fellow_nh_name = e.mate_fellow_nh_name,
                            fellow_city_company_name = e.fellow_city_company_name,
                            leader_workday_title = e.leader_workday_title,
                            fellow_workday_cn_title = e.fellow_workday_cn_title
                        FROM employee_fellow AS e
                        WHERE m.owner = e.fellow_ad_account
                    """)
            except Exception as _:
                pass

        return con, table_name
    
    def get_metrics_summary(self, con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
        """Get a summary of metrics by owner and period."""
        return con.execute(f"""
            SELECT
                owner,
                period,
                metric_type,
                SUM(value) as total_value,
                COUNT(*) as metric_count,
                unit
            FROM {table_name}
            GROUP BY owner, period, metric_type, unit
            ORDER BY owner, period, metric_type
        """).df()
    
    def get_owner_summary(self, con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
        """Get a summary of metrics by owner."""
        return con.execute(f"""
            SELECT
                owner,
                metric_type,
                SUM(value) as total_value,
                COUNT(*) as metric_count,
                unit
            FROM {table_name}
            GROUP BY owner, metric_type, unit
            ORDER BY owner, metric_type
        """).df()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract OKR metrics from markdown file")
    parser.add_argument("markdown_file", nargs="?", default="okr_report_20250804_145834.md",
                       help="Path to the OKR markdown file (default: okr_report_20250804_145834.md)")
    parser.add_argument("--db-path", default="okr_metrics.db",
                       help="Path to the DuckDB database file (default: okr_metrics.db)")
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = OKRMetricsExtractor(args.markdown_file)
    
    # Extract metrics
    print(f"Extracting metrics from OKR report: {args.markdown_file}")
    metrics = extractor.extract_metrics()
    print(f"Extracted {len(metrics)} metrics")
    
    # Create DuckDB table
    print(f"Creating DuckDB table: {args.db_path}")
    con, table_name = extractor.create_duckdb_table(args.db_path)

    # Get summaries
    print(f"\nMetrics Summary by Owner and Period (table: {table_name}):")
    summary = extractor.get_metrics_summary(con, table_name)
    print(summary.head(20))

    print(f"\nOwner Summary (table: {table_name}):")
    owner_summary = extractor.get_owner_summary(con, table_name)
    print(owner_summary.head(20))
    
    # Show some example queries
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
