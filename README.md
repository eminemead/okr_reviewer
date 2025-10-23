# OKR Reviewer Project

This project generates OKR reports from Feishu API data stored in DuckDB.

## Features

- **Timestamped Reports**: Each report generation creates a new file with timestamp (e.g., `okr_report_20241201_143022.md`)
- **Multiple Data Sources**: Supports both open_ids and fellow_ad_accounts methods
- **Rate Limiting**: Respects Feishu API rate limits (100 requests/minute)
- **Error Handling**: Graceful handling of API errors and missing data

## Files

- `okr_ingest2.py` - **Main script**: Uses fellow_ad_accounts from DuckDB to fetch OKRs directly
- `generate_okr_report.py` - Convenience script to generate reports with timestamped filenames
- `okr_ingest.py` - Legacy script: Uses open_ids from DuckDB (not needed for current workflow)
- `okr_script1.py` - Fetches Feishu open_ids for email addresses (not needed for current workflow)
- `get_okr_list` - Shell script for OKR list operations

## Environment Variables

Set these environment variables before running:

```bash
export FEISHU_ACCESS_TOKEN="your_feishu_access_token"
export DUCKDB_PATH="/path/to/your/database.db"
export DUCKDB_TABLE="your_table_name"
export DUCKDB_COLUMN="your_column_name"
```

## Usage

### Method 1: Using the Pipeline Orchestrator (Recommended)

The `main_orchestrator.py` script runs the complete OKR processing pipeline:

```bash
# Run complete pipeline with default settings
uv run python main_orchestrator.py

# Custom configuration
uv run python main_orchestrator.py --okr_limit 5 --port 8080

# Skip dashboard (run all other steps)
uv run python main_orchestrator.py --skip-dashboard
```

Or use the shell wrapper:
```bash
# Basic usage
./run_pipeline.sh

# Custom settings: OKR limit, skip dashboard, port
./run_pipeline.sh 5 true 8080
```

### Method 2: Individual Scripts

```bash
# Generate OKR report (uses fellow_ad_accounts method by default)
uv run python generate_okr_report.py

# Specify number of OKRs per user
uv run python generate_okr_report.py --okr_limit 5

# Extract metrics from reports
uv run python extract_okr_metrics.py

# Export data to CSV
uv run python export_metrics.py

# Generate insights
uv run python summary_insights.py
```

### Method 3: Direct script execution

```bash
# Generate OKR report directly
uv run python okr_ingest2.py
```

**Note**: The `okr_ingest.py` script is not needed for the current workflow as `okr_ingest2.py` fetches all required data directly.

## Report Files

Reports are generated with timestamped filenames to prevent overwriting:

- Format: `okr_report_YYYYMMDD_HHMMSS.md`
- Example: `okr_report_20241201_143022.md`

Each report contains:
- User information
- OKR periods
- Objectives with progress and scores
- Key Results with progress and scores
- Alignment information
- Progress reports

## Database Schema

The system uses the following DuckDB table:

```sql
SELECT fellow_ad_account 
FROM onvo_employee_fellow_maturity_info_1d_a
WHERE fellow_emp_status_name = '在职' 
  AND is_intern = false 
  AND is_fellow = true 
  AND fellow_ad_account IS NOT NULL
```

This query fetches all active fellow employees' ad accounts directly from the database.

## API Rate Limiting

The system automatically handles Feishu API rate limits:
- Maximum 100 requests per minute
- Automatic sleep when limit is reached
- Progress tracking and reporting

## Error Handling

- Missing access tokens are caught with clear error messages
- API errors are logged and reported in the output
- Database connection errors are handled gracefully
- Individual user failures don't stop the entire process

## Recent Changes

- **Timestamped Reports**: All reports now use unique filenames with timestamps
- **Convenience Script**: Added `generate_okr_report.py` for easier usage
- **Better Error Messages**: Improved error reporting and user feedback
- **Documentation**: Added comprehensive README 