#!/usr/bin/env python3
"""
Query OKR metrics from DuckDB database.
"""

import duckdb
import pandas as pd

def main():
    # Connect to the database
    con = duckdb.connect('okr_metrics.db')
    
    print("=== OKR Metrics Analysis ===\n")
    
    # 1. Total metrics by type
    print("1. Total Metrics by Type:")
    result = con.execute("""
        SELECT 
            metric_type,
            SUM(value) as total_value,
            COUNT(*) as count,
            unit
        FROM okr_metrics 
        GROUP BY metric_type, unit
        ORDER BY total_value DESC
    """).df()
    print(result)
    print()
    
    # 2. Top 10 owners by total metrics
    print("2. Top 10 Owners by Total Metrics:")
    result = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_metrics,
            COUNT(*) as metric_count
        FROM okr_metrics 
        GROUP BY owner
        ORDER BY total_metrics DESC
        LIMIT 10
    """).df()
    print(result)
    print()
    
    # 3. Metrics by period
    print("3. Metrics by Period:")
    result = con.execute("""
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
    print(result.head(20))
    print()
    
    # 4. Top owners by each metric type
    print("4. Top 5 Owners by 新增建联量 (New Connections):")
    result = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_connections,
            COUNT(*) as metric_count
        FROM okr_metrics 
        WHERE metric_type = '新增建联量'
        GROUP BY owner
        ORDER BY total_connections DESC
        LIMIT 5
    """).df()
    print(result)
    print()
    
    print("5. Top 5 Owners by 试驾量 (Test Drives):")
    result = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_test_drives,
            COUNT(*) as metric_count
        FROM okr_metrics 
        WHERE metric_type = '试驾量'
        GROUP BY owner
        ORDER BY total_test_drives DESC
        LIMIT 5
    """).df()
    print(result)
    print()
    
    print("6. Top 5 Owners by 锁单量 (Orders):")
    result = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_orders,
            COUNT(*) as metric_count
        FROM okr_metrics 
        WHERE metric_type = '锁单量'
        GROUP BY owner
        ORDER BY total_orders DESC
        LIMIT 5
    """).df()
    print(result)
    print()
    
    print("7. Top 5 Owners by 交付量 (Deliveries):")
    result = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_deliveries,
            COUNT(*) as metric_count
        FROM okr_metrics 
        WHERE metric_type = '交付量'
        GROUP BY owner
        ORDER BY total_deliveries DESC
        LIMIT 5
    """).df()
    print(result)
    print()
    
    # 8. Average metrics by owner
    print("8. Average Metrics by Owner (owners with multiple metrics):")
    result = con.execute("""
        SELECT 
            owner,
            COUNT(DISTINCT metric_type) as metric_types,
            AVG(value) as avg_value,
            SUM(value) as total_value
        FROM okr_metrics 
        GROUP BY owner
        HAVING COUNT(*) > 1
        ORDER BY total_value DESC
        LIMIT 10
    """).df()
    print(result)
    print()
    
    # 9. Sample raw data
    print("9. Sample Raw Data (first 10 records):")
    result = con.execute("""
        SELECT 
            owner,
            period,
            metric_type,
            value,
            unit
        FROM okr_metrics 
        ORDER BY id
        LIMIT 10
    """).df()
    print(result)
    print()
    
    # 10. Database statistics
    print("10. Database Statistics:")
    result = con.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT owner) as unique_owners,
            COUNT(DISTINCT period) as unique_periods,
            COUNT(DISTINCT metric_type) as unique_metric_types
        FROM okr_metrics
    """).df()
    print(result)
    
    con.close()

if __name__ == "__main__":
    main()

