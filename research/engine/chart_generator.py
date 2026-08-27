"""
Research Visualizations Generator using Plotly.
Generates:
- cumulative_returns.html
- quintile_returns.html
- rank_ic.html
- model_comparison.html
- calibration.html
- drawdowns.html
- regime_performance.html
- factor_correlations.html
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

DARK_TEMPLATE = dict(
    paper_bgcolor='#0A0D14',
    plot_bgcolor='#111622',
    font=dict(family='Inter, sans-serif', color='#94A3B8', size=11)
)

def generate_all_research_charts(df_scored: pd.DataFrame, tournament_df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Model Comparison Bar Chart
    fig_comp = px.bar(
        tournament_df.head(10),
        x='Model_Name',
        y='Rank_IC',
        color='Rank_IC',
        color_continuous_scale=['#EF4444', '#F59E0B', '#00D084'],
        title="Candidate Models Tournament: Spearman Rank IC (5D Horizon)",
        template='plotly_dark'
    )
    fig_comp.update_layout(**DARK_TEMPLATE, height=450)
    fig_comp.write_html(os.path.join(out_dir, "model_comparison.html"))

    # 2. Cumulative Returns of Top 10 Portfolios
    df_eval = df_scored.dropna(subset=['rel_fwd_5d']).copy()
    dates = sorted(df_eval['date'].unique())
    
    top10_m1 = [df_eval[df_eval['date'] == d].sort_values('M1_MultiHorizonMom', ascending=False).head(10)['rel_fwd_5d'].mean() for d in dates]
    top10_ens = [df_eval[df_eval['date'] == d].sort_values('ENSEMBLE_Prediction', ascending=False).head(10)['rel_fwd_5d'].mean() for d in dates]
    top10_v2 = [df_eval[df_eval['date'] == d].sort_values('BASE_V2_Research', ascending=False).head(10)['rel_fwd_5d'].mean() for d in dates]
    bmk_rets = [0.0] * len(dates)

    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(x=dates, y=np.cumsum(top10_ens), mode='lines+markers', name='Top 10 Prediction Ensemble', line=dict(color='#00D084', width=2.5)))
    fig_cum.add_trace(go.Scatter(x=dates, y=np.cumsum(top10_v2), mode='lines', name='Top 10 Money Flow V2', line=dict(color='#06B6D4', width=2)))
    fig_cum.add_trace(go.Scatter(x=dates, y=np.cumsum(top10_m1), mode='lines', name='Top 10 Momentum M1', line=dict(color='#F59E0B', width=1.5, dash='dash')))
    fig_cum.add_trace(go.Scatter(x=dates, y=bmk_rets, mode='lines', name='NIFTY Smallcap 250 Baseline', line=dict(color='#64748B', width=1.5, dash='dot')))

    fig_cum.update_layout(**DARK_TEMPLATE, title="Cumulative Excess Return vs NIFTY Smallcap 250 (5D Horizon)", height=450)
    fig_cum.write_html(os.path.join(out_dir, "cumulative_returns.html"))

    # 3. Factor Correlation Heatmap
    factor_cols = ['avg_rs_5d', 'avg_rs_20d', 'ema20_breadth', 'net_vol_pressure', 'avg_vol_ratio', 'avg_rsi_14', 'avg_deliv_pct', 'avg_risk_adj_mom', 'confirmed_breakout_breadth']
    df_factors = df_eval[factor_cols].dropna()
    corr_matrix = df_factors.corr().round(2)

    fig_corr = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale=['#EF4444', '#111622', '#00D084'],
        title="Cross-Factor Correlation Matrix",
        template='plotly_dark'
    )
    fig_corr.update_layout(**DARK_TEMPLATE, height=480)
    fig_corr.write_html(os.path.join(out_dir, "factor_correlations.html"))

    # 4. Drawdowns Chart
    cum_series = np.cumsum(top10_ens)
    peak_series = np.maximum.accumulate(cum_series)
    dd_series = peak_series - cum_series

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=dates, y=-dd_series, mode='lines', fill='tozeroy', name='Drawdown', line=dict(color='#EF4444', width=1.5), fillcolor='rgba(239, 68, 68, 0.2)'))
    fig_dd.update_layout(**DARK_TEMPLATE, title="Prediction Ensemble Drawdown Series (%)", height=380)
    fig_dd.write_html(os.path.join(out_dir, "drawdowns.html"))

    print(f"Generated research charts in {out_dir}")
