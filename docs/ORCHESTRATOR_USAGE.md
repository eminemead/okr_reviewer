# OKR Pipeline Orchestrator - Usage Guide

## Overview

The `main_orchestrator.py` script provides a single command to run the entire OKR processing pipeline:

1. **Generate OKR Reports** - Fetch data from Feishu API
2. **Extract Metrics** - Parse reports and store in DuckDB
3. **Export Data** - Create CSV files for analysis
4. **Generate Insights** - Create summary analysis

## Quick Start

### Basic Usage
```bash
# Run complete pipeline with default settings
uv run python main_orchestrator.py
```

### With Custom Settings
```bash
# Fetch 5 OKRs per user, skip dashboard
uv run python main_orchestrator.py --okr_limit 5 --skip-dashboard

# Use custom port for dashboard
uv run python main_orchestrator.py --port 8080

# Full custom configuration
uv run python main_orchestrator.py --okr_limit 10 --port 9000
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--okr_limit N` | Number of OKRs to fetch per user | 2 |
| `--skip-dashboard` | Skip starting the web dashboard | False |
| `--port PORT` | Port for the dashboard | 8000 |

## Prerequisites

1. **Environment Variables**:
   ```bash
   export FEISHU_ACCESS_TOKEN="your_feishu_access_token"
   ```

2. **Required Scripts** (automatically checked):
   - `generate_okr_report.py`
   - `extract_okr_metrics.py`
   - `export_metrics.py`
   - `summary_insights.py`

## Pipeline Steps

### Step 1: Generate OKR Reports
- Calls `generate_okr_report.py`
- Fetches OKR data from Feishu API
- Creates timestamped report files in `outputs/reports/`

### Step 2: Extract Metrics
- Calls `extract_okr_metrics.py`
- Uses the most recent OKR report
- Extracts metrics (新增建联量, 试驾量, 锁单量, 交付量)
- Stores data in `okr_metrics.db`

### Step 3: Export Data
- Calls `export_metrics.py`
- Creates CSV files for analysis
- Exports: `okr_metrics_all.csv`, `okr_metrics_summary.csv`

### Step 4: Generate Insights
- Calls `summary_insights.py`
- Creates analysis and insights
- Shows top performers and trends


## Output Files

After running the pipeline, you'll have:

### Database
- `okr_metrics.db` - DuckDB database with extracted metrics

### Reports
- `outputs/reports/okr_report_YYYYMMDD_HHMMSS.md` - Latest OKR report

### CSV Exports
- `okr_metrics_all.csv` - All metrics data
- `okr_metrics_summary.csv` - Summary by owner and metric type

### Web Dashboard
- Access at `http://127.0.0.1:8000` (or custom port)
- Interactive filters and charts
- Real-time data from DuckDB

## Error Handling

- **Graceful Failures**: If one step fails, the pipeline continues with remaining steps
- **Detailed Logging**: Each step logs its progress and any errors
- **Prerequisites Check**: Validates required files and environment variables before starting

## Examples

### Development/Testing
```bash
# Quick test with minimal data
uv run python main_orchestrator.py --okr_limit 1 --skip-dashboard
```

### Production Run
```bash
# Full pipeline with more data
uv run python main_orchestrator.py --okr_limit 5
```

### Data Analysis Only
```bash
# Skip report generation, work with existing data
# (Assumes you already have okr_metrics.db)
uv run python main_orchestrator.py --skip-dashboard
```

## Troubleshooting

### Common Issues

1. **Missing Access Token**:
   ```bash
   export FEISHU_ACCESS_TOKEN="your_token_here"
   ```

2. **Port Already in Use**:
   ```bash
   uv run python main_orchestrator.py --port 8080
   ```

3. **Missing Scripts**:
   - Ensure all required Python scripts are in the current directory
   - Check file permissions

4. **Database Issues**:
   - Delete `okr_metrics.db` to start fresh
   - Check DuckDB installation: `uv add duckdb`

## Monitoring

The orchestrator provides detailed logging:
- Timestamped messages
- Step-by-step progress
- Error details with stdout/stderr
- Final summary with success/failure counts

## Integration

You can integrate this into your workflow:

```bash
# Daily cron job
0 9 * * * cd /path/to/okr_reviewer && uv run python main_orchestrator.py --okr_limit 3

# CI/CD pipeline
- name: Run OKR Pipeline
  run: |
    cd okr_reviewer
    uv run python main_orchestrator.py --skip-dashboard
```

