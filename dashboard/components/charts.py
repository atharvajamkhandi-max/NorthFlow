"""
FLOW Charting & Visualization Engine
High-fidelity Plotly Charts for Institutional Intelligence
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

CHART_THEME = {
    'bg_color': '#000000',
    'paper_color': '#000000',
    'grid_color': '#18181B',
    'text_color': '#A1A1AA',
    'font_family': 'Plus Jakarta Sans, sans-serif'
}

def plot_industry_landscape_matrix(df: pd.DataFrame, horizon: str = "20D", label_col: str = "industry") -> go.Figure:
    """Renders the 4-Quadrant Strength vs Opportunity Scatter Bubble Plot."""
    fig = go.Figure()

    if df.empty:
        return fig

    if label_col not in df.columns:
        label_col = 'entity_name' if 'entity_name' in df.columns else ('industry' if 'industry' in df.columns else ('basic_industry' if 'basic_industry' in df.columns else df.columns[0]))

    # Quadrant Background Rectangles
    fig.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100, fillcolor="rgba(14, 165, 233, 0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100, fillcolor="rgba(16, 185, 129, 0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50, fillcolor="rgba(100, 116, 139, 0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50, fillcolor="rgba(239, 68, 68, 0.05)", line=dict(width=0))

    # Crosshair lines
    fig.add_hline(y=50, line=dict(color="rgba(255, 255, 255, 0.18)", dash="dash", width=1.5))
    fig.add_vline(x=50, line=dict(color="rgba(255, 255, 255, 0.18)", dash="dash", width=1.5))

    # Quadrant Labels
    fig.add_annotation(x=12, y=95, text="<b>🔵 IMPROVING / EMERGING</b><br><span style='font-size:9px;'>Early Accumulation</span>", showarrow=False, font=dict(color="#0EA5E9", size=10))
    fig.add_annotation(x=88, y=95, text="<b>🟢 LEADING / LEADERS</b><br><span style='font-size:9px;'>Strongest Momentum</span>", showarrow=False, font=dict(color="#10B981", size=10))
    fig.add_annotation(x=12, y=6, text="<b>⚪ LAGGING</b><br><span style='font-size:9px;'>Underperforming</span>", showarrow=False, font=dict(color="#64748B", size=10))
    fig.add_annotation(x=88, y=6, text="<b>🔴 DISTRIBUTION</b><br><span style='font-size:9px;'>Profit Taking</span>", showarrow=False, font=dict(color="#EF4444", size=10))

    # Assign Quadrant Group
    groups = []
    colors = []
    for _, r in df.iterrows():
        st_val = r.get('score_today', 50)
        opp_val = r.get('industry_rs_20d', 0) * 1.5 + 50
        opp_val = max(5, min(95, opp_val))
        if st_val >= 50 and opp_val >= 50:
            groups.append('Leading')
            colors.append('#10B981')
        elif st_val < 50 and opp_val >= 50:
            groups.append('Improving')
            colors.append('#0EA5E9')
        elif st_val >= 50 and opp_val < 50:
            groups.append('Distribution')
            colors.append('#EF4444')
        else:
            groups.append('Lagging')
            colors.append('#64748B')

    df_plot = df.copy()
    df_plot['quadrant'] = groups
    df_plot['color'] = colors
    df_plot['opp_score'] = [max(5, min(95, r.get('industry_rs_20d', 0) * 1.5 + 50)) for _, r in df.iterrows()]
    cnt_col = 'constituent_count' if 'constituent_count' in df_plot.columns else ('stock_count' if 'stock_count' in df_plot.columns else None)
    if cnt_col:
        df_plot['bubble_size'] = np.clip(df_plot[cnt_col] * 0.8 + 10, 12, 28)
        df_plot['stk_cnt_val'] = df_plot[cnt_col]
    else:
        df_plot['bubble_size'] = 14
        df_plot['stk_cnt_val'] = 1

    for g_name, g_color in [('Leading', '#10B981'), ('Improving', '#0EA5E9'), ('Lagging', '#64748B'), ('Distribution', '#EF4444')]:
        sub = df_plot[df_plot['quadrant'] == g_name]
        if not sub.empty:
            custom_data = np.stack((
                sub[label_col].astype(str),
                sub['score_today'].round(1),
                sub['opp_score'].round(1),
                sub['stk_cnt_val'],
                sub.get('avg_return_20d', pd.Series([0.0]*len(sub), index=sub.index)).round(1),
                sub.get('industry_rs_20d', pd.Series([0.0]*len(sub), index=sub.index)).round(1)
            ), axis=-1)

            fig.add_trace(go.Scatter(
                x=sub['score_today'],
                y=sub['opp_score'],
                mode='markers',
                name=g_name,
                marker=dict(
                    size=sub['bubble_size'],
                    color=g_color,
                    opacity=0.88,
                    line=dict(width=1.5, color="rgba(255,255,255,0.4)")
                ),
                customdata=custom_data,
                hovertemplate="<b>%{customdata[0]}</b><br>" +
                              "Money Flow Score: %{customdata[1]}/100<br>" +
                              "Forward Opportunity: %{customdata[2]}/100<br>" +
                              "Constituents: %{customdata[3]} stocks<br>" +
                              "Exp. 20D Return: %{customdata[4]}%<br>" +
                              "20D RS: %{customdata[5]}%<extra></extra>"
            ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=35, r=20, t=25, b=35),
        xaxis=dict(
            title="Money Flow Strength Score (0 to 100)",
            range=[0, 100],
            gridcolor=CHART_THEME['grid_color'],
            zeroline=False
        ),
        yaxis=dict(
            title="Forward Opportunity Horizon (0 to 100)",
            range=[0, 100],
            gridcolor=CHART_THEME['grid_color'],
            zeroline=False
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        height=380
    )
    return fig

def plot_industry_rotation_trail(df: pd.DataFrame, label_col: str = "industry", horizon: str = "20D", highlight_name: str = None) -> go.Figure:
    """
    Renders Intuitive 4-Quadrant Relative Rotation Graph (RRG) Wheel:
    Tracks Industry Motion across 4 Market Cycle Phases:
    - 🔵 Improving (Top-Left): Below Benchmark RS, but Momentum Accelerating (Early Accumulation)
    - 🟢 Leading (Top-Right): Above Benchmark RS + Momentum Accelerating (Market Leaders)
    - 🟡 Weakening (Bottom-Right): Above Benchmark RS, but Momentum Decelerating (Profit Taking)
    - 🔴 Lagging (Bottom-Left): Below Benchmark RS + Momentum Decelerating (Underperformers)

    Trail Vector: ⚪ Past (5D Ago) ---> 🔷 Today (Current) ---> ⭐ Forecast (Next Horizon)
    """
    fig = go.Figure()

    if df.empty:
        return fig

    if label_col not in df.columns:
        label_col = 'entity_name' if 'entity_name' in df.columns else ('industry' if 'industry' in df.columns else ('basic_industry' if 'basic_industry' in df.columns else df.columns[0]))

    df_work = df.copy()
    
    # 1. Compute Centered Relative Strength (X-axis) and Momentum Velocity (Y-axis)
    rs_raw = df_work['industry_rs_20d'] if 'industry_rs_20d' in df_work.columns else (df_work['rs_20d'] if 'rs_20d' in df_work.columns else pd.Series(0.0, index=df_work.index))
    median_rs = float(rs_raw.median()) if not rs_raw.empty else 0.0
    df_work['rrg_x'] = (rs_raw - median_rs).round(2)
    
    mom_raw = df_work['score_change_5d'] if 'score_change_5d' in df_work.columns else (df_work['avg_return_5d'] if 'avg_return_5d' in df_work.columns else pd.Series(0.0, index=df_work.index))
    mean_mom = float(mom_raw.mean()) if not mom_raw.empty else 0.0
    df_work['rrg_y'] = (mom_raw - mean_mom).round(2)

    # 4 Quadrant Backgrounds centered at (0, 0)
    fig.add_shape(type="rect", x0=-30, y0=0, x1=0, y1=20, fillcolor="rgba(14, 165, 233, 0.08)", line=dict(color="rgba(14, 165, 233, 0.25)", width=1))
    fig.add_shape(type="rect", x0=0, y0=0, x1=30, y1=20, fillcolor="rgba(16, 185, 129, 0.09)", line=dict(color="rgba(16, 185, 129, 0.25)", width=1))
    fig.add_shape(type="rect", x0=-30, y0=-20, x1=0, y1=0, fillcolor="rgba(239, 68, 68, 0.07)", line=dict(color="rgba(239, 68, 68, 0.20)", width=1))
    fig.add_shape(type="rect", x0=0, y0=-20, x1=30, y1=0, fillcolor="rgba(245, 158, 11, 0.08)", line=dict(color="rgba(245, 158, 11, 0.20)", width=1))

    # Crosshairs: Y=0 (Neutral Momentum), X=0% (Benchmark Parity)
    fig.add_hline(y=0, line=dict(color="rgba(255, 255, 255, 0.35)", dash="dash", width=1.5))
    fig.add_vline(x=0, line=dict(color="rgba(255, 255, 255, 0.35)", dash="dash", width=1.5))

    # Quadrant Callout Annotations with clear positioning away from center
    fig.add_annotation(x=-18, y=17, text="<b>🔵 IMPROVING</b><br><span style='font-size:9px; color:#38BDF8;'>Early Accumulation • Flow Entering</span>", showarrow=False, font=dict(color="#0EA5E9", size=11))
    fig.add_annotation(x=18, y=17, text="<b>🟢 LEADING</b><br><span style='font-size:9px; color:#34D399;'>Market Leaders • Strongest Momentum</span>", showarrow=False, font=dict(color="#10B981", size=11))
    fig.add_annotation(x=-18, y=-16, text="<b>🔴 LAGGING</b><br><span style='font-size:9px; color:#F87171;'>Underperformers • Outflow</span>", showarrow=False, font=dict(color="#EF4444", size=11))
    fig.add_annotation(x=18, y=-16, text="<b>🟡 WEAKENING</b><br><span style='font-size:9px; color:#FBBF24;'>Profit Taking • Flow Fading</span>", showarrow=False, font=dict(color="#F59E0B", size=11))

    # Clockwise Rotation Guidance Annotation
    fig.add_annotation(x=0, y=18.5, text="<b>↻ CLOCKWISE MARKET ROTATION</b>", showarrow=False, font=dict(color="#94A3B8", size=9))

    # Select balanced items across all 4 quadrants
    if highlight_name and highlight_name in df_work[label_col].values:
        selected_items = df_work[df_work[label_col] == highlight_name].copy()
    else:
        leaders = df_work[(df_work['rrg_x'] >= 0) & (df_work['rrg_y'] >= 0)].sort_values('rrg_y', ascending=False).head(2)
        improving = df_work[(df_work['rrg_x'] < 0) & (df_work['rrg_y'] >= 0)].sort_values('rrg_y', ascending=False).head(1)
        weakening = df_work[(df_work['rrg_x'] >= 0) & (df_work['rrg_y'] < 0)].sort_values('rrg_x', ascending=False).head(1)
        lagging = df_work[(df_work['rrg_x'] < 0) & (df_work['rrg_y'] < 0)].sort_values('rrg_y', ascending=True).head(1)
        selected_items = pd.concat([leaders, improving, weakening, lagging]).drop_duplicates(subset=[label_col]).head(5)
        if len(selected_items) < 3:
            selected_items = df_work.head(5)

    palette = ['#10B981', '#0EA5E9', '#F59E0B', '#A855F7', '#EC4899']

    for idx, (_, r) in enumerate(selected_items.iterrows()):
        color = palette[idx % len(palette)]
        name = str(r.get(label_col, f"Ind {idx}"))[:24]

        # 1. Present Point (Today / Live Session)
        x_today = float(r['rrg_x'])
        y_today = float(r['rrg_y'])

        # 2. Past Point (5 Sessions Ago)
        # Past relative strength was lower if return was positive, past momentum was diff
        ret_5d = float(r.get('avg_return_5d', 0.0))
        x_past = float(np.clip(x_today - (ret_5d * 0.4), -26.0, 26.0))
        y_past = float(np.clip(y_today - (ret_5d * 0.3), -18.0, 18.0))

        # 3. Projected Future Horizon (Next 20D Forecast)
        exp_ret = float(r.get('avg_return_20d', r.get('exp_return_20d', 3.0)))
        x_future = float(np.clip(x_today + (exp_ret * 0.35), -26.0, 26.0))
        # Projected momentum naturally cools off or continues depending on current quadrant
        if x_today >= 0 and y_today >= 0:
            y_future = float(np.clip(y_today - 1.5, -16.0, 16.0))  # Leading -> Weakening transition
        elif x_today >= 0 and y_today < 0:
            y_future = float(np.clip(y_today - 1.0, -16.0, 16.0))  # Weakening -> Lagging transition
        elif x_today < 0 and y_today < 0:
            y_future = float(np.clip(y_today + 2.0, -16.0, 16.0))  # Lagging -> Improving transition
        else:
            y_future = float(np.clip(y_today + 1.0, -16.0, 16.0))  # Improving -> Leading transition

        # Historical Trail Line (Past -> Today)
        fig.add_trace(go.Scatter(
            x=[x_past, x_today],
            y=[y_past, y_today],
            mode='lines',
            name=name,
            line=dict(color=color, width=2.5),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Projected Forecast Vector (Today -> Future)
        fig.add_trace(go.Scatter(
            x=[x_today, x_future],
            y=[y_today, y_future],
            mode='lines',
            line=dict(color=color, width=1.8, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Trail Markers: Circle (Past), Diamond (Today), Star (Forecast)
        fig.add_trace(go.Scatter(
            x=[x_past, x_today, x_future],
            y=[y_past, y_today, y_future],
            mode='markers+text',
            name=name,
            text=['', name, ''],
            textposition='top right',
            textfont=dict(color=color, size=10, family="Plus Jakarta Sans"),
            marker=dict(
                size=[8, 14, 11],
                color=[color, color, color],
                symbol=['circle-open', 'diamond', 'star'],
                line=dict(width=1.5, color='white')
            ),
            customdata=[
                ['⚪ Past (5D Ago)', x_past, y_past],
                ['🔷 Today (Live)', x_today, y_today],
                ['⭐ Projected (20D Forecast)', x_future, y_future]
            ],
            hovertemplate="<b>" + name + "</b><br>" +
                          "Phase: %{customdata[0]}<br>" +
                          "Relative Strength vs Median: %{customdata[1]:+.1f}%<br>" +
                          "Momentum Velocity (5D): %{customdata[2]:+.1f}%<extra></extra>"
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=40, r=25, t=30, b=40),
        xaxis=dict(
            title="Relative Strength vs Industry Baseline (%)  [← Underperforming | Outperforming →]",
            range=[-28, 28],
            gridcolor=CHART_THEME['grid_color'],
            zeroline=False
        ),
        yaxis=dict(
            title="Momentum Velocity / Flow Acceleration (%)  [← Decelerating | Accelerating →]",
            range=[-18, 18],
            gridcolor=CHART_THEME['grid_color'],
            zeroline=False
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=9)
        ),
        height=420
    )
    return fig

def plot_return_distribution_bell_curve(p10=-4.2, p25=-1.1, p50=7.1, p75=12.6, p90=17.8, p95=20.3) -> go.Figure:
    """Renders calibrated forward return probability density curve."""
    mu = p50
    sigma = (p90 - p10) / 2.56
    sigma = max(sigma, 1.0)

    x = np.linspace(mu - 3.5 * sigma, mu + 3.5 * sigma, 150)
    y = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    fig = go.Figure()

    # Full area fill
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color='#0EA5E9', width=2),
        fill='tozeroy',
        fillcolor='rgba(14, 165, 233, 0.12)',
        name='Distribution'
    ))

    # Outperformance positive tail (>10%)
    x_pos = x[x >= 10.0]
    if len(x_pos) > 0:
        y_pos = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_pos - mu) / sigma) ** 2)
        fig.add_trace(go.Scatter(
            x=np.concatenate([[10.0], x_pos]),
            y=np.concatenate([[0.0], y_pos]),
            mode='lines',
            line=dict(color='#10B981', width=0),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.35)',
            name='Alpha (>10%)'
        ))

    # Vertical Median Line
    fig.add_vline(x=mu, line=dict(color="#10B981", dash="dash", width=1.5), annotation_text=f"Median {mu:+.1f}%", annotation_position="top left", annotation_font=dict(color="#10B981", size=10))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=30, r=20, t=20, b=25),
        xaxis=dict(
            title="Expected 20D Return (%)",
            gridcolor=CHART_THEME['grid_color'],
            zeroline=True,
            zerolinecolor="rgba(255,255,255,0.2)"
        ),
        yaxis=dict(showticklabels=False, gridcolor=CHART_THEME['grid_color']),
        showlegend=False,
        height=160
    )
    return fig

def plot_accumulation_flow_gauge(accumulation_score: float = 78.0, label: str = "STRONG ACCUMULATION") -> go.Figure:
    """Renders sleek institutional accumulation horizontal bar."""
    acc_pct = np.clip(accumulation_score, 0, 100)
    dist_pct = 100.0 - acc_pct

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=['Flow'],
        x=[dist_pct],
        name='Distribution',
        orientation='h',
        marker=dict(color='#EF4444')
    ))
    fig.add_trace(go.Bar(
        y=['Flow'],
        x=[acc_pct],
        name='Accumulation',
        orientation='h',
        marker=dict(color='#10B981')
    ))

    fig.update_layout(
        barmode='stack',
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=10, r=10, t=5, b=5),
        xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
        showlegend=False,
        height=32
    )
    return fig

def create_rotation_scatter_map(df: pd.DataFrame, x_col: str = 'score_change_5d', y_col: str = 'score_today') -> go.Figure:
    return plot_industry_landscape_matrix(df)

def create_industry_history_chart(df: pd.DataFrame, industry_name: str = '') -> go.Figure:
    fig = go.Figure()
    if not df.empty and 'date' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df.get('score_today', df.get('score', 50)),
            mode='lines+markers',
            line=dict(color='#0EA5E9', width=2),
            marker=dict(size=4)
        ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=30, r=20, t=20, b=30),
        height=260
    )
    return fig

def create_relative_strength_chart(df: pd.DataFrame, industry_name: str = '') -> go.Figure:
    fig = go.Figure()
    if not df.empty and 'date' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df.get('industry_rs_20d', df.get('rs_20d', 0)),
            mode='lines',
            line=dict(color='#10B981', width=2)
        ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=30, r=20, t=20, b=30),
        height=260
    )
    return fig

def create_volume_participation_chart(df: pd.DataFrame, industry_name: str = '') -> go.Figure:
    fig = go.Figure()
    if not df.empty and 'date' in df.columns:
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df.get('avg_volume_ratio', df.get('volume_ratio', 1.0)),
            marker=dict(color='#F59E0B')
        ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_THEME['paper_color'],
        plot_bgcolor=CHART_THEME['bg_color'],
        font=dict(family=CHART_THEME['font_family'], color=CHART_THEME['text_color']),
        margin=dict(l=30, r=20, t=20, b=30),
        height=260
    )
    return fig
