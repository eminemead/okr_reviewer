uv run python - << 'PY'
import duckdb, os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

DB='/Users/xiaofei.yin/dspy/OKR_reviewer/okr_metrics.db'
con=duckdb.connect(DB, read_only=True)
q = """
WITH base AS (
  SELECT COALESCE(e.fellow_city_company_name, 'Unknown') AS company_name,
         m.metric_type,
         m.value
  FROM okr_metrics m
  LEFT JOIN employee_fellow e
    ON m.owner = e.fellow_ad_account
  WHERE m.period = '8 月'
)
SELECT company_name, metric_type,
       COUNT(*) AS total,
       SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) AS nulls,
       100.0 * SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0) AS null_pct
FROM base
WHERE company_name != 'Unknown'
GROUP BY company_name, metric_type
"""
df = con.execute(q).df()
con.close()

if df.empty:
    print('No data for plotting.')
    raise SystemExit(0)

# has_metric percentage
df['has_metric'] = 100.0 - df['null_pct'].astype(float)

pivot = df.pivot(index='company_name', columns='metric_type', values='has_metric').fillna(0.0)
# Order companies by average has_metric descending
pivot['__avg__'] = pivot.mean(axis=1)
pivot = pivot.sort_values('__avg__', ascending=False)
heat = pivot.drop(columns='__avg__')
# Reorder columns
desired = ['新增建联量','试驾量','锁单量','交付量']
available = [c for c in desired if c in heat.columns]
# If any extra columns exist, append them after desired order
extras = [c for c in heat.columns if c not in available]
heat = heat.reindex(columns=available + extras)
labels = heat.round(0).astype(int).astype(str) + '%'

# Chinese font prefs
plt.rcParams['font.sans-serif'] = ['PingFang SC','SF Pro Text','Arial Unicode MS','Heiti SC','Hiragino Sans GB','Microsoft YaHei','SimHei','Noto Sans CJK SC']
plt.rcParams['axes.unicode_minus'] = False

n = heat.shape[0]
fig_h = max(6, min(0.3 * n + 2, 60))
fig_w = 10
plt.figure(figsize=(fig_w, fig_h))
ax = sns.heatmap(heat, annot=labels, fmt='', cmap='Reds', vmin=0, vmax=100, cbar_kws={'label':'Has Metric %'}, annot_kws={'fontsize':8})
# Move metric type axis to top
ax.xaxis.set_label_position('top')
ax.xaxis.tick_top()
plt.xlabel('Metric Type', labelpad=10)
plt.title('August Has-Metric Coverage by Company and Metric Type (higher is better)')
plt.ylabel('City Company')
plt.tight_layout()

outdir='/Users/xiaofei.yin/dspy/OKR_reviewer/outputs/plots'
os.makedirs(outdir, exist_ok=True)
path_png=os.path.join(outdir,'has_metric_august_by_company.png')
plt.savefig(path_png, dpi=200)
print('Saved plot (columns ordered):', path_png)
PY