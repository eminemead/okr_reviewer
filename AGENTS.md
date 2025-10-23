# OKR Reviewer Agent Guide

## Build/Lint/Test Commands

- **Run full pipeline**: `uv run python main_orchestrator.py --okr_limit 5`
- **Run single test user**: `uv run python main_orchestrator.py --okr_limit 1 --skip-dashboard`
- **Go-to sequence**:
  1. `uv run python generate_okr_report.py --okr_limit 2` (test OKR data in okr_report_*.md)
  2. `uv run python extract_okr_metrics.py outputs/reports/okr_report_*.md` (test data in okr_metrics.db)
  3. `uv run python summary_insights.py` (create heatmap visualization plot)
- **Run individual scripts**: `uv run python generate_okr_report.py --okr_limit 2`
- **Run scripts sequentially**: `python run_sequential.py script1.py script2.py ...`

## Architecture Overview

This is an OKR metrics extraction and visualization system using:
- **Data Source**: Feishu API OKR data
- **Storage**: DuckDB database (`okr_metrics.db`)
- **Dashboard**: FastHTML web interface with Chart.js
- **Pipeline**: Orchestrated via `main_orchestrator.py`
- **Key Components**: API ingestion → metrics extraction → CSV export → web dashboard

## Code Style Guidelines

### Python Conventions
- Use `#!/usr/bin/env python3` shebang
- Type hints with `from typing import List, Dict, Optional, Tuple`
- Docstrings with triple quotes and Args/Returns sections
- Class-based design with descriptive method names
- Environment variables for configuration (e.g., `FEISHU_ACCESS_TOKEN`)

### Naming Conventions
- Functions: `snake_case` with descriptive names
- Classes: `PascalCase` (e.g., `OKRMetricsExtractor`)
- Variables: `snake_case`
- Constants: `UPPER_CASE`

### Error Handling
- Try/except blocks with specific exception types
- `subprocess.run()` with `check=True` and output capture
- Graceful degradation when steps fail
- Clear error messages with context

### Imports
- Standard library first, then third-party, then local
- Group related imports with blank lines
- Use absolute imports within the project
