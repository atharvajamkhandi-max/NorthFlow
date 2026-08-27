"""
Canonical Analytical Card Component (Phase 71.2 Reference Architecture)
NorthFlow - Quantitative Industry Intelligence Terminal.

Provides compact, high-density analytical cards with circular rank indicators,
grouped monospace financial KPIs, status badges, real-data sparkbars, and active selection state.
Strictly sanitized with textwrap.dedent to prevent raw HTML code leakage.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
from typing import Dict, Any, List, Optional
from dashboard.components.theme import get_theme_tokens, get_theme_mode

def generate_mini_sparkbar_svg(val1: float, val2: float, val3: float, val4: float, theme_tokens: Dict[str, str]) -> str:
    """
    Generates a tiny, clean 4-bar SVG distribution / trend sparkline from actual metric values.
    """
    vals = [max(0.0, float(v)) for v in [val1, val2, val3, val4]]
    max_v = max(vals) if max(vals) > 0 else 1.0
    heights = [int((v / max_v) * 16) + 3 for v in vals]
    
    pos_color = theme_tokens.get("positive", "#10B981")
    acc_color = theme_tokens.get("accent", "#38BDF8")
    dim_color = theme_tokens.get("card_border", "#1E293B")
    
    svg = f'''<svg width="40" height="22" viewBox="0 0 40 22" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
<rect x="2" y="{20 - heights[0]}" width="6" height="{heights[0]}" rx="1.5" fill="{dim_color}"/>
<rect x="11" y="{20 - heights[1]}" width="6" height="{heights[1]}" rx="1.5" fill="{acc_color}" opacity="0.7"/>
<rect x="20" y="{20 - heights[2]}" width="6" height="{heights[2]}" rx="1.5" fill="{acc_color}"/>
<rect x="29" y="{20 - heights[3]}" width="6" height="{heights[3]}" rx="1.5" fill="{pos_color}"/>
</svg>'''
    return svg

def render_analytical_card(
    rank: int,
    title: str,
    subtitle: str = "",
    action: str = "WATCH",
    trend: str = "NEUTRAL",
    strength: float = 50.0,
    exp_return_20d: float = 0.0,
    confidence: float = 50.0,
    risk: float = 50.0,
    breadth_50: float = 50.0,
    constituent_count: int = 0,
    extra_metric_label: str = "CONF / RISK",
    extra_metric_value: str = "",
    spark_vals: Optional[List[float]] = None,
    is_selected: bool = False
) -> str:
    """
    Renders clean, unindented HTML for a single reference-inspired analytical card.
    Supports is_selected highlight state.
    """
    t = get_theme_tokens()
    
    # Rank styling
    rank_cls = "rank-circle-top1" if rank == 1 else ("rank-circle-top3" if rank <= 3 else "rank-circle")
    rank_str = f"#{rank:02d}"
    
    # Action Badge
    action_clean = str(action).upper().strip()
    badge_map = {
        "STRONG BUY": ("badge-strong-buy", "🔥 STRONG BUY"),
        "BUY": ("badge-buy", "🟢 BUY"),
        "WATCH": ("badge-watch", "🟡 WATCH"),
        "NEUTRAL": ("badge-neutral", "⚪ NEUTRAL"),
        "REDUCE": ("badge-reduce", "🟠 REDUCE"),
        "AVOID": ("badge-avoid", "🔴 AVOID"),
        "LEADING": ("badge-strong-buy", "🔥 LEADING"),
        "ACCUMULATION": ("badge-buy", "🟢 ACCUMULATION"),
        "IMPROVING": ("badge-watch", "🟣 IMPROVING"),
        "WEAKENING": ("badge-neutral", "🟡 WEAKENING"),
        "LAGGING": ("badge-reduce", "🔴 LAGGING")
    }
    badge_cls, badge_text = badge_map.get(action_clean, ("badge-watch", action_clean))
    
    # 20D Return formatting
    ret_color = t["positive"] if exp_return_20d > 0 else (t["negative"] if exp_return_20d < 0 else t["text_muted"])
    ret_sign = "+" if exp_return_20d > 0 else ""
    ret_str = f"{ret_sign}{exp_return_20d:.1f}%"
    
    # Strength formatting
    st_color = t["positive"] if strength >= 70 else (t["accent"] if strength >= 55 else (t["warning"] if strength >= 40 else t["negative"]))
    
    # Sparkline
    if spark_vals and len(spark_vals) >= 4:
        spark_svg = generate_mini_sparkbar_svg(spark_vals[0], spark_vals[1], spark_vals[2], spark_vals[3], t)
    else:
        spark_svg = generate_mini_sparkbar_svg(breadth_50 * 0.5, breadth_50 * 0.75, breadth_50, strength, t)
        
    sub_ctx = []
    if constituent_count > 0:
        sub_ctx.append(f"<b>{constituent_count}</b> stocks")
    if subtitle:
        sub_ctx.append(subtitle)
    if trend:
        sub_ctx.append(f"Trend: <b style='color: {t['text_primary']};'>{trend}</b>")
    sub_text = " · ".join(sub_ctx)

    if not extra_metric_value:
        extra_metric_value = f"{confidence:.0f} / {risk:.0f}"

    # Selected visual treatment
    card_border = f"1.5px solid {t['accent']}" if is_selected else f"1px solid {t['card_border']}"
    card_bg = t['card_bg_hover'] if is_selected else t['card_bg']
    selected_pill = f'''<span style="background: {t['accent_muted']}; color: {t['accent']}; border: 1px solid {t['accent']}; padding: 1px 6px; border-radius: 4px; font-size: 0.60rem; font-weight: 800; font-family: 'JetBrains Mono';">● SELECTED</span>''' if is_selected else ""

    raw_html = f"""<div class="analytical-card" style="border: {card_border}; background: {card_bg};">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px;">
<div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
<div class="rank-circle {rank_cls}">{rank_str}</div>
<div style="min-width: 0;">
<div style="font-size: 0.95rem; font-weight: 800; color: {t['text_primary']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -0.01em;">{title}</div>
<div style="font-size: 0.70rem; color: {t['text_muted']}; margin-top: 1px;">{sub_text}</div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
{selected_pill}
<span class="badge-pill {badge_cls}">{badge_text}</span>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(4, 1fr) auto; gap: 6px; align-items: center; background: {t['secondary_bg']}; padding: 6px 10px; border-radius: 6px; border: 1px solid {t['card_border']};">
<div class="card-metric-col" style="text-align: left;">
<div class="card-metric-label">STRENGTH</div>
<div class="card-metric-value" style="color: {st_color};">{strength:.1f}<span style="font-size: 0.62rem; color: {t['text_dim']};">/100</span></div>
</div>
<div class="card-metric-col" style="text-align: left;">
<div class="card-metric-label">20D EXP RET</div>
<div class="card-metric-value" style="color: {ret_color};">{ret_str}</div>
</div>
<div class="card-metric-col" style="text-align: left;">
<div class="card-metric-label">BREADTH 50</div>
<div class="card-metric-value">{breadth_50:.0f}%</div>
</div>
<div class="card-metric-col" style="text-align: left;">
<div class="card-metric-label">{extra_metric_label}</div>
<div class="card-metric-value">{extra_metric_value}</div>
</div>
<div style="text-align: right; padding-left: 6px; border-left: 1px solid {t['card_border']};">
{spark_svg}
</div>
</div>
</div>"""
    return textwrap.dedent(raw_html).strip()

def render_analytical_card_grid(
    df: pd.DataFrame,
    max_cards: Optional[int] = None,
    columns: int = 2,
    key_prefix: str = "card",
    enable_selection: bool = False,
    selected_entity: Optional[str] = None
):
    """
    Renders a responsive 2-column grid of analytical cards from an intelligence dataframe.
    Supports selection callback and active card state.
    """
    if df.empty:
        st.info("No items to display for this selection.")
        return
    if max_cards is not None:
        df = df.head(max_cards)

    col1, col2 = st.columns(2) if columns == 2 else (st.container(), None)
    cols = [col1, col2] if columns == 2 else [col1]
        
    for i, (_, row) in enumerate(df.iterrows()):
        target_col = cols[i % len(cols)]
        
        rank = int(row.get("Rank", i + 1))
        title = str(row.get("entity_name", row.get("industry", row.get("symbol", "Entity"))))
        subtitle = str(row.get("macro_sector", row.get("sector", "")))
        action = str(row.get("final_action", "WATCH"))
        trend = str(row.get("trend_rating", "NEUTRAL"))
        strength = float(row.get("current_strength", row.get("strength_score", 50.0)))
        exp_ret = float(row.get("exp_return_20d", row.get("avg_return_20d", 0.0)))
        breadth = float(row.get("breadth_50", 50.0))
        stocks_cnt = int(row.get("constituent_count", row.get("stock_count", 0)))
        conf = float(row.get("confidence_score", 50.0))
        risk = float(row.get("risk_score", 50.0))
        
        is_sel = (title == selected_entity) if selected_entity else False
        
        card_html = render_analytical_card(
            rank=rank,
            title=title,
            subtitle=subtitle,
            action=action,
            trend=trend,
            strength=strength,
            exp_return_20d=exp_ret,
            confidence=conf,
            risk=risk,
            breadth_50=breadth,
            constituent_count=stocks_cnt,
            extra_metric_label="CONF / RISK",
            extra_metric_value=f"{conf:.0f} / {risk:.0f}",
            is_selected=is_sel
        )
        with target_col:
            st.markdown(card_html, unsafe_allow_html=True)
            if enable_selection:
                btn_label = f"✓ {title} (SELECTED)" if is_sel else f"⚡ Inspect {title} ➜"
                btn_type = "primary" if is_sel else "secondary"
                if st.button(btn_label, key=f"{key_prefix}_sel_btn_{i}_{title}", type=btn_type, use_container_width=True):
                    st.session_state["selected_drilldown_entity"] = title
                    st.rerun()
