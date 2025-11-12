# Direct OKR Metrics Extraction

This folder contains the refactored OKR metrics extraction system that works directly with raw API data instead of generating and parsing Markdown files.

## Architecture

- **direct_ingest.py**: Fetches OKR data from Feishu API and stores raw JSON in DuckDB
- **direct_extract.py**: Extracts metrics from raw JSON data in DuckDB
- **direct_orchestrator.py**: Orchestrates the full pipeline

## Key Improvements

- Eliminates Markdown generation/parsing step
- Works directly with structured JSON data
- More reliable extraction (no formatting inconsistencies)
- Faster processing (no regex on large text files)

## Usage

### Run full pipeline:
```bash
cd direct_extraction
python3 direct_orchestrator.py --okr_limit 5
```

### Run individual steps:
```bash
# Ingest raw data
python3 direct_ingest.py --db_path okr_metrics.db --access_token YOUR_TOKEN --okr_limit 2

# Extract metrics
python3 direct_extract.py --db-path okr_metrics.db
```

## Data Flow

1. Query manager users from DuckDB
2. Fetch OKR data from Feishu API for each user
3. Store raw JSON in `raw_okrs_manager` table
4. Parse JSON to extract metrics using regex patterns
5. Store metrics in timestamped `okr_metrics_YYYYMMDD_HHMMSS` table
6. Enrich with employee data from external source

## Tables Created

- `raw_okrs_manager`: Raw OKR JSON data
- `okr_metrics_YYYYMMDD_HHMMSS`: Extracted metrics with employee enrichment
- `employee_fellow`: Employee metadata (if available)

## Environment Variables

- `FEISHU_ACCESS_TOKEN`: Required for API access
- `DUCKDB_PATH`: Path to DuckDB database (default: /Users/xiaofei.yin/rill_test.db)
