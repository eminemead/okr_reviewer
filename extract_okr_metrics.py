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
            period = period_match[0].strip()
            period_content = period_match[1].strip()
            
            # Skip if no objectives
            if '_No objectives for this period._' in period_content:
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
        
        # Define metric patterns
        metric_patterns = {
            '新增建联量': [
                r'新增建联[≥>]*(\d+)',
                r'建联[≥>]*(\d+)',
                r'新增建联量[：:]\s*(\d+)',
                r'建联量[：:]\s*(\d+)',
                r'新增建联(\d+)人',
                r'建联(\d+)人',
                r'新增建联(\d+)组',
                r'建联(\d+)组',
                r'新增建联(\d+)个',
                r'建联(\d+)个',
                r'新增建联(\d+)批',
                r'建联(\d+)批'
            ],
            '试驾量': [
                r'试驾[≥>]*(\d+)',
                r'试驾量[≥>]*(\d+)',
                r'试驾(\d+)个',
                r'试驾(\d+)组',
                r'试驾(\d+)批',
                r'试驾(\d+)人次',
                r'试驾(\d+)次'
            ],
            '锁单量': [
                r'锁单[≥>]*(\d+)',
                r'锁单量[≥>]*(\d+)',
                r'锁单(\d+)台',
                r'锁单(\d+)辆',
                r'锁单(\d+)个',
                r'锁单(\d+)单',
                r'L60锁单(\d+)',
                r'L90锁单(\d+)'
            ],
            '交付量': [
                r'交付[≥>]*(\d+)',
                r'交付量[≥>]*(\d+)',
                r'交付(\d+)台',
                r'交付(\d+)辆',
                r'交付(\d+)个',
                r'交付(\d+)单',
                r'L60交付(\d+)',
                r'L90交付(\d+)'
            ]
        }
        
        # Extract metrics for each type
        for metric_type, patterns in metric_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, objective)
                for match in matches:
                    try:
                        value = int(match)
                        metrics.append({
                            'owner': owner,
                            'period': period,
                            'metric_type': metric_type,
                            'value': value,
                            'unit': self._get_unit(metric_type),
                            'objective': objective[:200] + '...' if len(objective) > 200 else objective
                        })
                    except ValueError:
                        continue
        
        return metrics
    
    def _get_unit(self, metric_type: str) -> str:
        """Get the unit for a metric type."""
        units = {
            '新增建联量': '人',
            '试驾量': '组',
            '锁单量': '台',
            '交付量': '台'
        }
        return units.get(metric_type, '')
    
    def create_duckdb_table(self, db_path: str = ':memory:'):
        """Create DuckDB table and insert the extracted metrics."""
        # Connect to DuckDB
        con = duckdb.connect(db_path)
        
        # Create table
        con.execute("""
            CREATE TABLE IF NOT EXISTS okr_metrics (
                id INTEGER PRIMARY KEY,
                owner VARCHAR,
                period VARCHAR,
                metric_type VARCHAR,
                value INTEGER,
                unit VARCHAR,
                objective TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Convert to DataFrame and insert
        if self.metrics_data:
            df = pd.DataFrame(self.metrics_data)
            # Add an id column to the DataFrame
            df['id'] = range(1, len(df) + 1)
            con.execute("DELETE FROM okr_metrics")  # Clear existing data
            con.execute("INSERT INTO okr_metrics (id, owner, period, metric_type, value, unit, objective) SELECT id, owner, period, metric_type, value, unit, objective FROM df")
        
        return con
    
    def get_metrics_summary(self, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Get a summary of metrics by owner and period."""
        return con.execute("""
            SELECT 
                owner,
                period,
                metric_type,
                SUM(value) as total_value,
                COUNT(*) as metric_count,
                unit
            FROM okr_metrics 
            GROUP BY owner, period, metric_type, unit
            ORDER BY owner, period, metric_type
        """).df()
    
    def get_owner_summary(self, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
        """Get a summary of metrics by owner."""
        return con.execute("""
            SELECT 
                owner,
                metric_type,
                SUM(value) as total_value,
                COUNT(*) as metric_count,
                unit
            FROM okr_metrics 
            GROUP BY owner, metric_type, unit
            ORDER BY owner, metric_type
        """).df()

def main():
    # Initialize extractor
    extractor = OKRMetricsExtractor('okr_report_20250804_145834.md')
    
    # Extract metrics
    print("Extracting metrics from OKR report...")
    metrics = extractor.extract_metrics()
    print(f"Extracted {len(metrics)} metrics")
    
    # Create DuckDB table
    print("Creating DuckDB table...")
    con = extractor.create_duckdb_table('okr_metrics.db')
    
    # Get summaries
    print("\nMetrics Summary by Owner and Period:")
    summary = extractor.get_metrics_summary(con)
    print(summary.head(20))
    
    print("\nOwner Summary:")
    owner_summary = extractor.get_owner_summary(con)
    print(owner_summary.head(20))
    
    # Show some example queries
    print("\nExample Queries:")
    print("1. Total metrics by type:")
    result = con.execute("""
        SELECT metric_type, SUM(value) as total, COUNT(*) as count
        FROM okr_metrics 
        GROUP BY metric_type
        ORDER BY total DESC
    """).df()
    print(result)
    
    print("\n2. Top 10 owners by total metrics:")
    result = con.execute("""
        SELECT owner, SUM(value) as total_metrics, COUNT(*) as metric_count
        FROM okr_metrics 
        GROUP BY owner
        ORDER BY total_metrics DESC
        LIMIT 10
    """).df()
    print(result)
    
    con.close()
    print(f"\nData saved to okr_metrics.db with {len(metrics)} records")

if __name__ == "__main__":
    main()
