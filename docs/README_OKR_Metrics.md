# OKR Metrics Extraction and Analysis

This project extracts OKR (Objectives and Key Results) metrics from markdown files and stores them in a DuckDB database for analysis.

## Overview

The system extracts four main metrics by owner by monthly:
- **新增建联量** (New Connections): Number of new connections established
- **试驾量** (Test Drives): Number of test drives conducted
- **锁单量** (Orders): Number of orders placed
- **交付量** (Deliveries): Number of deliveries completed

## Files

### Core Scripts

1. **`extract_okr_metrics.py`** - Main extraction script
   - Parses OKR markdown files
   - Extracts metrics using regex patterns
   - Stores data in DuckDB database
   - Provides summary statistics

2. **`query_okr_metrics.py`** - Analysis and query script
   - Demonstrates various SQL queries
   - Shows top performers by metric type
   - Provides database statistics

### Database

- **`okr_metrics.db`** - DuckDB database containing extracted metrics

## Database Schema

```sql
CREATE TABLE okr_metrics (
    id INTEGER PRIMARY KEY,
    owner VARCHAR,           -- Owner name (open_id)
    period VARCHAR,          -- Time period (e.g., "2025 年 7 月")
    metric_type VARCHAR,     -- Type of metric (新增建联量, 试驾量, 锁单量, 交付量)
    value INTEGER,          -- Numeric value
    unit VARCHAR,           -- Unit of measurement (人, 组, 台)
    objective TEXT,         -- Original objective text
    created_at TIMESTAMP    -- Timestamp of record creation
);
```

## Usage

### 1. Extract Metrics from OKR Report

```bash
python3 extract_okr_metrics.py
```

This will:
- Parse the OKR markdown file (`okr_report_20250804_145834.md`)
- Extract 777 metrics from various owners
- Store data in `okr_metrics.db`

### 2. Query and Analyze Data

```bash
python3 query_okr_metrics.py
```

This provides various analyses including:
- Total metrics by type
- Top performers by metric
- Period-wise analysis
- Database statistics

## Sample Results

### Total Metrics by Type
- **新增建联量**: 37,773 total connections (388 records)
- **试驾量**: 3,080 total test drives (119 records)
- **交付量**: 444 total deliveries (153 records)
- **锁单量**: 276 total orders (117 records)

### Top Performers
- **yanan.tao**: 3,540 total metrics
- **zhen.yao2**: 1,290 total metrics
- **pandapia.li**: 1,256 total metrics

## Key Features

### 1. Robust Pattern Matching
The extraction uses multiple regex patterns to capture various formats:
- `新增建联≥100人` (New connections ≥ 100 people)
- `试驾量>40组` (Test drives > 40 groups)
- `锁单2台` (Orders 2 units)
- `交付1台` (Deliveries 1 unit)

### 2. Flexible Data Structure
- Supports multiple time periods
- Handles different units of measurement
- Preserves original objective context

### 3. SQL Analysis Capabilities
- Group by owner, period, metric type
- Calculate totals, averages, counts
- Filter and sort data
- Complex aggregations

## Example Queries

### Top 5 Owners by New Connections
```sql
SELECT 
    owner,
    SUM(value) as total_connections,
    COUNT(*) as metric_count
FROM okr_metrics 
WHERE metric_type = '新增建联量'
GROUP BY owner
ORDER BY total_connections DESC
LIMIT 5;
```

### Metrics by Period
```sql
SELECT 
    period,
    metric_type,
    SUM(value) as total_value,
    COUNT(*) as count
FROM okr_metrics 
GROUP BY period, metric_type
ORDER BY period, total_value DESC;
```

### Owner Performance Summary
```sql
SELECT 
    owner,
    COUNT(DISTINCT metric_type) as metric_types,
    AVG(value) as avg_value,
    SUM(value) as total_value
FROM okr_metrics 
GROUP BY owner
HAVING COUNT(*) > 1
ORDER BY total_value DESC;
```

## Data Quality

The extraction process handles:
- Multiple date formats
- Various numeric expressions (≥, >, =)
- Different units (人, 组, 台, 批, 次)
- Missing or incomplete data gracefully

## Future Enhancements

1. **Automated Updates**: Schedule regular extraction from new OKR reports
2. **Visualization**: Add charts and graphs for better insights
3. **Trend Analysis**: Track performance over time
4. **Goal Tracking**: Compare actual vs. target metrics
5. **Export Options**: CSV, Excel, JSON formats

## Dependencies

- Python 3.9+
- duckdb
- pandas

Install with:
```bash
python3 -m pip install --break-system-packages duckdb pandas
```

## Database Access

The DuckDB database can be accessed using:
- Python with duckdb library
- DuckDB CLI
- Any SQL client that supports DuckDB

Example connection:
```python
import duckdb
con = duckdb.connect('okr_metrics.db')
result = con.execute("SELECT * FROM okr_metrics LIMIT 5").df()
```

