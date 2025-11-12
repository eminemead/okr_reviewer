#!/usr/bin/env python3
"""
Export OKR metrics from DuckDB to CSV format.
"""

import os
import duckdb
import pandas as pd
from datetime import datetime

def main():
    # Connect to the database
    con = duckdb.connect('okr_metrics.db')
    
    # Export all data
    print("Exporting OKR metrics to CSV files...")
    
    # Ensure output directory exists
    output_dir = os.path.join("outputs", "csv")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Export all data
    all_data = con.execute("""
        SELECT 
            owner,
            period,
            metric_type,
            value,
            unit,
            objective
        FROM okr_metrics 
        ORDER BY owner, period, metric_type
    """).df()
    
    all_path = os.path.join(output_dir, 'okr_metrics_all.csv')
    all_data.to_csv(all_path, index=False, encoding='utf-8-sig')
    print(f"✓ Exported {len(all_data)} records to {all_path}")
    
    # 2. Export summary by owner and metric type
    summary = con.execute("""
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
    
    summary_path = os.path.join(output_dir, 'okr_metrics_summary.csv')
    summary.to_csv(summary_path, index=False, encoding='utf-8-sig')
    print(f"✓ Exported {len(summary)} summary records to {summary_path}")
    
    # 3. Export by metric type
    for metric_type in ['新增建联量', '试驾量', '锁单量', '交付量']:
        metric_data = con.execute(f"""
            SELECT 
                owner,
                period,
                value,
                unit,
                objective
            FROM okr_metrics 
            WHERE metric_type = '{metric_type}'
            ORDER BY value DESC
        """).df()
        
        filename = f'okr_metrics_{metric_type}.csv'
        path = os.path.join(output_dir, filename)
        metric_data.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"✓ Exported {len(metric_data)} {metric_type} records to {path}")
    
    # 4. Export top performers
    top_performers = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_metrics,
            COUNT(*) as metric_count,
            COUNT(DISTINCT metric_type) as metric_types
        FROM okr_metrics 
        GROUP BY owner
        ORDER BY total_metrics DESC
    """).df()
    
    top_path = os.path.join(output_dir, 'okr_metrics_top_performers.csv')
    top_performers.to_csv(top_path, index=False, encoding='utf-8-sig')
    print(f"✓ Exported {len(top_performers)} top performers to {top_path}")
    
    # 5. Export by period
    period_summary = con.execute("""
        SELECT 
            period,
            metric_type,
            SUM(value) as total_value,
            COUNT(*) as count,
            unit
        FROM okr_metrics 
        GROUP BY period, metric_type, unit
        ORDER BY period, total_value DESC
    """).df()
    
    period_path = os.path.join(output_dir, 'okr_metrics_by_period.csv')
    period_summary.to_csv(period_path, index=False, encoding='utf-8-sig')
    print(f"✓ Exported {len(period_summary)} period records to {period_path}")
    
    # 6. Create a pivot table (wide format)
    pivot_data = con.execute("""
        SELECT 
            owner,
            period,
            SUM(CASE WHEN metric_type = '新增建联量' THEN value ELSE 0 END) as new_connections,
            SUM(CASE WHEN metric_type = '试驾量' THEN value ELSE 0 END) as test_drives,
            SUM(CASE WHEN metric_type = '锁单量' THEN value ELSE 0 END) as orders,
            SUM(CASE WHEN metric_type = '交付量' THEN value ELSE 0 END) as deliveries
        FROM okr_metrics 
        GROUP BY owner, period
        ORDER BY owner, period
    """).df()
    
    pivot_path = os.path.join(output_dir, 'okr_metrics_pivot.csv')
    pivot_data.to_csv(pivot_path, index=False, encoding='utf-8-sig')
    print(f"✓ Exported {len(pivot_data)} pivot records to {pivot_path}")
    
    # Print summary statistics
    print("\n=== Export Summary ===")
    print(f"Total records exported: {len(all_data)}")
    print(f"Unique owners: {all_data['owner'].nunique()}")
    print(f"Unique periods: {all_data['period'].nunique()}")
    print(f"Metric types: {all_data['metric_type'].unique()}")
    
    # Show top 5 owners
    print("\nTop 5 Owners by Total Metrics:")
    top_5 = top_performers.head(5)
    for _, row in top_5.iterrows():
        print(f"  {row['owner']}: {row['total_metrics']} total metrics")
    
    con.close()
    print("\n✓ All exports completed successfully!")

if __name__ == "__main__":
    main()

