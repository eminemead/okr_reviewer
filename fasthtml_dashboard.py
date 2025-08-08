#!/usr/bin/env python3
from fasthtml.common import *
import duckdb
import json
from typing import Optional

DB_PATH = 'okr_metrics.db'
TRACKED_METRICS = ('新增建联量','试驾量','锁单量','交付量')

app, rt = fast_app()

# --- Data helpers ---

def q(sql: str, *params):
    con = duckdb.connect(DB_PATH)
    try:
        return con.execute(sql, params).df()
    finally:
        con.close()

def metric_filter_clause(owner: Optional[str], period: Optional[str]):
    where = ["metric_type IN (?, ?, ?, ?)"]
    args = list(TRACKED_METRICS)
    if owner:
        where.append("owner = ?")
        args.append(owner)
    if period:
        where.append("period = ?")
        args.append(period)
    return ' WHERE ' + ' AND '.join(where), tuple(args)

# --- UI helpers ---

def kpi_card(title: str, value: float, unit: str):
    return Div(
        H3(title, cls='kpi-title'),
        P(f"{int(value) if value == int(value) else round(value, 2)} {unit}", cls='kpi-value'),
        cls='card'
    )

def header_filters(owner: Optional[str] = None, period: Optional[str] = None):
    owners = q("SELECT DISTINCT owner FROM okr_metrics ORDER BY owner")['owner'].tolist()
    periods = q("SELECT DISTINCT period FROM okr_metrics ORDER BY period")['period'].tolist()

    owner_sel = Select(
        Option("All", value="", selected=not owner),
        *[Option(o, value=o, selected=(o == owner)) for o in owners],
        id='owner', name='owner'
    )
    period_sel = Select(
        Option("All", value="", selected=not period),
        *[Option(p, value=p, selected=(p == period)) for p in periods],
        id='period', name='period'
    )

    # HTMX: On change, refresh kpis, table, and chart using the same query params
    filt_form = Form(
        Group(Label('Owner', _for='owner'), owner_sel),
        Group(Label('Period', _for='period'), period_sel),
        cls='filters',
        hx_get=update_all.to(),
        hx_target='#dashboard',
        hx_swap='outerHTML'
    )
    return filt_form

# --- Partials ---

@rt
def kpis(owner: Optional[str] = None, period: Optional[str] = None):
    where, args = metric_filter_clause(owner, period)
    df = q(f"""
        SELECT metric_type, SUM(value) AS total, ANY_VALUE(unit) AS unit
        FROM okr_metrics
        {where}
        GROUP BY metric_type, unit
    """, *args)
    # Ensure all tracked metrics appear
    m2row = {row['metric_type']: row for _, row in df.iterrows()}
    cards = []
    for mt in TRACKED_METRICS:
        row = m2row.get(mt, {'total': 0, 'unit': {'新增建联量':'人','试驾量':'组','锁单量':'台','交付量':'台'}[mt]})
        cards.append(kpi_card(mt, row['total'] if isinstance(row, dict) else row['total'], row['unit'] if isinstance(row, dict) else row['unit']))
    return Div(*cards, id='kpis', cls='grid')

@rt
def owner_table(owner: Optional[str] = None, period: Optional[str] = None):
    where, args = metric_filter_clause(owner, period)
    df = q(f"""
        SELECT owner, metric_type, SUM(value) AS total
        FROM okr_metrics
        {where}
        GROUP BY owner, metric_type
        ORDER BY owner, metric_type
    """, *args)
    # Pivot in Python for simplicity
    if df.empty:
        return Div(P('No data'), id='owner-table')
    piv = df.pivot_table(index='owner', columns='metric_type', values='total', fill_value=0)
    # Ensure columns order
    cols = [c for c in TRACKED_METRICS if c in piv.columns]
    thead = Thead(Tr(Th('Owner'), *[Th(c) for c in cols]))
    rows = []
    for owner_nm, row in piv.iterrows():
        rows.append(Tr(Td(owner_nm), *[Td(int(row[c])) for c in cols]))
    return Table(thead, Tbody(*rows), id='owner-table', cls='striped')

@rt
def metric_chart(owner: Optional[str] = None, period: Optional[str] = None):
    where, args = metric_filter_clause(owner, period)
    df = q(f"""
        SELECT metric_type, SUM(value) AS total
        FROM okr_metrics
        {where}
        GROUP BY metric_type
    """, *args)
    # Ensure all metrics present in order
    totals = []
    for mt in TRACKED_METRICS:
        val = df.loc[df['metric_type'] == mt, 'total']
        totals.append(float(val.iloc[0]) if not val.empty else 0.0)
    # Chart.js via CDN
    canvas_id = 'metricChart'
    chart_js = Script(src='https://cdn.jsdelivr.net/npm/chart.js')
    cfg = {
        'type': 'bar',
        'data': {
            'labels': list(TRACKED_METRICS),
            'datasets': [{
                'label': 'Total',
                'data': totals,
                'backgroundColor': ['#60a5fa','#34d399','#fbbf24','#f87171']
            }]
        },
        'options': {
            'responsive': True,
            'plugins': {'legend': {'display': False}},
            'scales': {'y': {'beginAtZero': True}}
        }
    }
    init_js = Script(f"""
        (function() {{
          const ctx = document.getElementById('{canvas_id}').getContext('2d');
          if (window._okrChart) window._okrChart.destroy();
          window._okrChart = new Chart(ctx, {cfg});
        }})();
    """.replace('{cfg}', json.dumps(cfg)))
    return Div(
        H3('Totals by Metric'),
        Canvas(id=canvas_id, width=600, height=300),
        chart_js,
        init_js,
        id='chart'
    )

# --- Page and updater ---

@rt
def update_all(owner: Optional[str] = None, period: Optional[str] = None):
    return Div(
        header_filters(owner, period),
        kpis(owner, period),
        metric_chart(owner, period),
        owner_table(owner, period),
        id='dashboard'
    )

@rt("/")
def index(owner: Optional[str] = None, period: Optional[str] = None):
    return Titled(
        "OKR Dashboard",
        Style("""
            .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0}
            .card{padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#fff}
            .kpi-title{margin:0 0 8px 0;font-size:14px;color:#374151}
            .kpi-value{margin:0;font-size:20px;font-weight:700;color:#111827}
            .filters{display:flex;gap:12px;align-items:end;margin:8px 0}
            .filters label{font-size:12px;color:#374151}
            .filters select{padding:6px 8px}
            table.striped{border-collapse:collapse;width:100%;margin-top:12px}
            table.striped th, table.striped td{border:1px solid #e5e7eb;padding:8px;text-align:right}
            table.striped th:first-child, table.striped td:first-child{text-align:left}
            h3{margin:12px 0 6px 0}
        """),
        H1('OKR Dashboard'),
        Div(id='dashboard', hx_get=update_all.to(owner=owner or '', period=period or ''), hx_trigger='load')
    )

if __name__ == "__main__":
    serve(host="0.0.0.0", port=8000)
