#!/usr/bin/env python3
"""
Generate key insights from OKR metrics data.
"""

import duckdb
import pandas as pd

def main():
    # Connect to the database
    con = duckdb.connect('okr_metrics.db')
    
    print("=== OKR Metrics Key Insights ===\n")
    
    # 1. Overall Statistics
    print("1. OVERALL STATISTICS")
    print("=" * 50)
    stats = con.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT owner) as unique_owners,
            COUNT(DISTINCT period) as unique_periods,
            COUNT(DISTINCT metric_type) as unique_metric_types
        FROM okr_metrics
    """).df()
    
    print(f"Total Records: {stats.iloc[0]['total_records']:,}")
    print(f"Unique Owners: {stats.iloc[0]['unique_owners']}")
    print(f"Unique Periods: {stats.iloc[0]['unique_periods']}")
    print(f"Metric Types: {stats.iloc[0]['unique_metric_types']}")
    print()
    
    # 2. Metrics by Type
    print("2. METRICS BY TYPE")
    print("=" * 50)
    metrics_by_type = con.execute("""
        SELECT 
            metric_type,
            SUM(value) as total_value,
            COUNT(*) as count,
            AVG(value) as avg_value,
            MAX(value) as max_value,
            unit
        FROM okr_metrics 
        GROUP BY metric_type, unit
        ORDER BY total_value DESC
    """).df()
    
    for _, row in metrics_by_type.iterrows():
        print(f"{row['metric_type']}:")
        print(f"  Total: {row['total_value']:,} {row['unit']}")
        print(f"  Count: {row['count']} records")
        print(f"  Average: {row['avg_value']:.1f} {row['unit']}")
        print(f"  Maximum: {row['max_value']} {row['unit']}")
        print()
    
    # 3. Top Performers
    print("3. TOP 10 PERFORMERS (by total metrics)")
    print("=" * 50)
    top_performers = con.execute("""
        SELECT 
            owner,
            SUM(value) as total_metrics,
            COUNT(*) as metric_count,
            COUNT(DISTINCT metric_type) as metric_types
        FROM okr_metrics 
        GROUP BY owner
        ORDER BY total_metrics DESC
        LIMIT 10
    """).df()
    
    for i, (_, row) in enumerate(top_performers.iterrows(), 1):
        print(f"{i:2d}. {row['owner']:<20} {row['total_metrics']:>8,.0f} total metrics ({row['metric_types']} types)")
    print()
    
    # 4. Top performers by each metric type
    metric_types = ['新增建联量', '试驾量', '锁单量', '交付量']
    for metric_type in metric_types:
        print(f"4. TOP 5 PERFORMERS - {metric_type}")
        print("=" * 50)
        top_by_type = con.execute(f"""
            SELECT 
                owner,
                SUM(value) as total_value,
                COUNT(*) as metric_count
            FROM okr_metrics 
            WHERE metric_type = '{metric_type}'
            GROUP BY owner
            ORDER BY total_value DESC
            LIMIT 5
        """).df()
        
        for i, (_, row) in enumerate(top_by_type.iterrows(), 1):
            print(f"{i}. {row['owner']:<20} {row['total_value']:>8,.0f}")
        print()
    
    # 5. Distribution Analysis
    print("5. DISTRIBUTION ANALYSIS")
    print("=" * 50)
    
    # Value ranges for each metric type
    for metric_type in metric_types:
        distribution = con.execute(f"""
            SELECT 
                COUNT(*) as count,
                MIN(value) as min_value,
                MAX(value) as max_value,
                AVG(value) as avg_value,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median
            FROM okr_metrics 
            WHERE metric_type = '{metric_type}'
        """).df()
        
        row = distribution.iloc[0]
        print(f"{metric_type}:")
        print(f"  Range: {row['min_value']} - {row['max_value']}")
        print(f"  Average: {row['avg_value']:.1f}")
        print(f"  Median: {row['median']:.1f}")
        print(f"  Count: {row['count']} records")
        print()
    
    # 6. Performance Categories
    print("6. PERFORMANCE CATEGORIES")
    print("=" * 50)
    
    # High performers (top 20%)
    high_performers = con.execute("""
        WITH owner_totals AS (
            SELECT 
                owner,
                SUM(value) as total_metrics
            FROM okr_metrics 
            GROUP BY owner
        ),
        percentiles AS (
            SELECT 
                PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY total_metrics) as threshold
            FROM owner_totals
        )
        SELECT 
            COUNT(*) as high_performers
        FROM owner_totals, percentiles
        WHERE total_metrics >= threshold
    """).df()
    
    print(f"High Performers (top 20%): {high_performers.iloc[0]['high_performers']} owners")
    
    # Owners with all 4 metric types
    complete_owners = con.execute("""
        SELECT 
            COUNT(*) as complete_owners
        FROM (
            SELECT owner
            FROM okr_metrics 
            GROUP BY owner
            HAVING COUNT(DISTINCT metric_type) = 4
        )
    """).df()
    
    print(f"Complete Owners (all 4 metrics): {complete_owners.iloc[0]['complete_owners']} owners")
    print()
    
    # 7. Key Insights
    print("7. KEY INSIGHTS")
    print("=" * 50)
    
    # Most common metric type
    most_common = con.execute("""
        SELECT metric_type, COUNT(*) as count
        FROM okr_metrics 
        GROUP BY metric_type
        ORDER BY count DESC
        LIMIT 1
    """).df()
    
    print(f"• Most tracked metric: {most_common.iloc[0]['metric_type']} ({most_common.iloc[0]['count']} records)")
    
    # Highest average value
    highest_avg = con.execute("""
        SELECT metric_type, AVG(value) as avg_value
        FROM okr_metrics 
        GROUP BY metric_type
        ORDER BY avg_value DESC
        LIMIT 1
    """).df()
    
    print(f"• Highest average value: {highest_avg.iloc[0]['metric_type']} ({highest_avg.iloc[0]['avg_value']:.1f})")
    
    # Most diverse owner (most metric types)
    most_diverse = con.execute("""
        SELECT owner, COUNT(DISTINCT metric_type) as metric_types
        FROM okr_metrics 
        GROUP BY owner
        ORDER BY metric_types DESC
        LIMIT 1
    """).df()
    
    print(f"• Most diverse owner: {most_diverse.iloc[0]['owner']} ({most_diverse.iloc[0]['metric_types']} metric types)")
    
    # Period analysis
    period_stats = con.execute("""
        SELECT period, COUNT(*) as records
        FROM okr_metrics 
        GROUP BY period
        ORDER BY records DESC
        LIMIT 1
    """).df()
    
    print(f"• Most active period: {period_stats.iloc[0]['period']} ({period_stats.iloc[0]['records']} records)")
    print()
    
    # 8. Recommendations
    print("8. RECOMMENDATIONS")
    print("=" * 50)
    print("• Focus on owners with incomplete metric sets to ensure comprehensive tracking")
    print("• Analyze high performers to identify best practices")
    print("• Consider setting minimum thresholds for each metric type")
    print("• Regular monitoring of metric distribution to identify outliers")
    print("• Cross-reference with actual performance data for validation")
    
    con.close()

if __name__ == "__main__":
    main()

