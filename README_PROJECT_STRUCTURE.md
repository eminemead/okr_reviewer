# OKR Reviewer - Project Structure

## Directory Layout

```
okr_reviewer/
├── scripts/                    # All executable scripts
│   ├── ingestion/             # Data ingestion from Feishu API
│   ├── reports/               # OKR report generation
│   ├── metrics/               # Metrics extraction and analysis
│   ├── visualization/         # Heatmap and visualization generation
│   ├── run_pipeline.sh        # Main pipeline orchestrator
│   └── run_sequential.py      # Sequential script runner
├── tests/                      # Test files
├── docs/                       # Documentation
├── archive/                    # Deprecated scripts and old backups
├── outputs/                    # Generated reports and plots (gitignored)
├── .cache/                     # Tool caches (gitignored)
├── pyproject.toml             # Project dependencies
├── AGENTS.md                  # Agent workflow guidelines
└── README.md                  # Main project documentation
```

## Quick Start

### Installation
```bash
uv sync
```

### Run OKR Report Generation
```bash
# Fellows
uv run python scripts/reports/generate_okr_report_fellow.py --okr_limit 2

# Managers
uv run python scripts/reports/generate_okr_report_manager.py --okr_limit 2

# General
uv run python scripts/reports/generate_okr_report.py --okr_limit 2
```

### Extract Metrics
```bash
uv run python scripts/metrics/extract_okr_metrics.py outputs/reports/okr_report_*.md
```

### Generate Visualizations
```bash
bash scripts/visualization/mgr_has_metric_by_company.sh "11 月"
```

## Key Scripts

### Ingestion (`scripts/ingestion/`)
- `okr_ingest_fellow.py` - Fetch OKRs for fellows
- `okr_ingest_manager.py` - Fetch OKRs for managers
- `okr_ingest2.py` - Alternative ingestion method

### Reports (`scripts/reports/`)
- `generate_okr_report_fellow.py` - Generate fellow OKR reports
- `generate_okr_report_manager.py` - Generate manager OKR reports
- `generate_okr_report.py` - General OKR report generation
- `main_orchestrator.py` - Full pipeline orchestration

### Metrics (`scripts/metrics/`)
- `extract_okr_metrics.py` - Extract metrics from markdown reports
- `export_metrics.py` - Export metrics to CSV/other formats
- `query_okr_metrics.py` - Query and analyze metrics

### Visualization (`scripts/visualization/`)
- `summary_insights.py` - Generate insights heatmap
- `mgr_has_metric_by_company.sh` - Manager metrics coverage by company
- `has_metric_by_company.sh` - Metrics coverage heatmap
- `has_metric_by_department.sh` - Metrics coverage by department
- `sum_metric_by_company.sh` - Sum metrics by company

## Environment Setup

Create a `.env` file with:
```
FEISHU_ACCESS_TOKEN=your_token_here
# Optional: DUCKDB_PATH=/path/to/database.db
```

See `.env.example` for template.

## Database

- Primary: `okr_metrics.db` (DuckDB)
- Backup: `archive/okr_metrics.backup.db`
- External: `/Users/xiaofei.yin/rill_test.db` (Feishu data source)

## Workflow

1. **Ingest**: Fetch OKR data from Feishu
   ```bash
   uv run python scripts/reports/generate_okr_report_manager.py --okr_limit 2
   ```

2. **Extract**: Parse metrics from markdown reports
   ```bash
   uv run python scripts/metrics/extract_okr_metrics.py outputs/reports/okr_report_*.md
   ```

3. **Visualize**: Generate heatmaps
   ```bash
   bash scripts/visualization/mgr_has_metric_by_company.sh "11 月"
   ```

## See Also

- `AGENTS.md` - Agent workflow guidelines
- `docs/` - Additional documentation
- `archive/` - Deprecated files and notes
