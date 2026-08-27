"""
pipeline/record_daily_decisions.py
Daily Decision Ledger Recording Cron / Job.
Executes after EOD pipeline to append immutable decision snapshots.
Never modifies models, scoring formulas, or thresholds.
"""

import sys
import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from storage.decision_ledger import DecisionLedger
from dashboard.components.v3_intelligence_loader import get_v3_date_intelligence
from dashboard.components.early_radar_shadow_service import get_cached_early_radar_scores

def record_daily_decisions_for_date(trade_date: str, ledger: Optional[DecisionLedger] = None) -> Dict[str, Any]:
    """
    Extracts canonical point-in-time decisions and records them into the immutable ledger.
    """
    t0 = time.perf_counter()
    if ledger is None:
        ledger = DecisionLedger()

    # 1. Fetch V3 Date Intelligence (Sectors, Subsectors/Industries, Stocks)
    sec_agg, df_sub, df_stk, meta = get_v3_date_intelligence(trade_date)
    actual_date = meta.get("date", trade_date)
    regime = meta.get("market_regime", "NEUTRAL")

    # 2. Fetch Early Sector Radar (Industry level)
    df_radar = get_cached_early_radar_scores(actual_date)
    radar_map = {}
    if not df_radar.empty:
        for _, r in df_radar.iterrows():
            radar_map[r["industry"]] = {
                "early_radar_score": r.get("early_radar_score"),
                "alert_level": r.get("alert_level"),
                "prob_1d": r.get("prob_1d"),
                "prob_3d": r.get("prob_3d"),
                "prob_5d": r.get("prob_5d"),
                "expected_lead_days": r.get("expected_lead_days")
            }

    records_to_insert = []

    # A. Sector Records
    if not sec_agg.empty:
        for _, row in sec_agg.iterrows():
            sec_name = str(row["macro_sector"]).strip()
            records_to_insert.append({
                "trade_date": actual_date,
                "entity_type": "SECTOR",
                "entity_id": sec_name,
                "entity_name": sec_name,
                "model_version": "MODEL_V3.2_FROZEN",
                "score": float(row.get("current_strength", 50.0)),
                "rating_action": str(row.get("final_action", "NEUTRAL")),
                "flow_state": str(row.get("flow_state", "NEUTRAL")),
                "early_radar_score": None,
                "alert_level": None,
                "prob_1d": None,
                "prob_3d": None,
                "prob_5d": None,
                "expected_lead_days": None,
                "breadth_50": float(row.get("breadth_50", 50.0)),
                "confidence_score": float(row.get("confidence_score", 50.0)),
                "risk_score": float(row.get("risk_score", 50.0)),
                "regime_label": regime,
                "parent_industry": None,
                "parent_sector": None,
                "close_price": None
            })

    # B. Industry Records (with Early Radar integration)
    if not df_sub.empty:
        for _, row in df_sub.iterrows():
            ind_name = str(row["niche_subsector"]).strip()
            radar_info = radar_map.get(ind_name, {})
            records_to_insert.append({
                "trade_date": actual_date,
                "entity_type": "INDUSTRY",
                "entity_id": ind_name,
                "entity_name": ind_name,
                "model_version": "MODEL_V3.2_FROZEN",
                "score": float(row.get("current_strength", 50.0)),
                "rating_action": str(row.get("final_action", "NEUTRAL")),
                "flow_state": str(row.get("flow_state", "NEUTRAL")),
                "early_radar_score": radar_info.get("early_radar_score"),
                "alert_level": radar_info.get("alert_level"),
                "prob_1d": radar_info.get("prob_1d"),
                "prob_3d": radar_info.get("prob_3d"),
                "prob_5d": radar_info.get("prob_5d"),
                "expected_lead_days": radar_info.get("expected_lead_days"),
                "breadth_50": float(row.get("breadth_50", 50.0)),
                "confidence_score": float(row.get("confidence_score", 50.0)),
                "risk_score": float(row.get("risk_score", 50.0)),
                "regime_label": regime,
                "parent_industry": None,
                "parent_sector": str(row.get("macro_sector")),
                "close_price": None
            })

    # C. Stock Records
    if not df_stk.empty:
        for _, row in df_stk.iterrows():
            sym = str(row["symbol"]).strip().upper()
            records_to_insert.append({
                "trade_date": actual_date,
                "entity_type": "STOCK",
                "entity_id": sym,
                "entity_name": str(row.get("company_name", sym)),
                "model_version": "MODEL_V3.2_FROZEN",
                "score": float(row.get("stock_strength_score", 50.0)),
                "rating_action": str(row.get("stock_action", "NEUTRAL")),
                "flow_state": None,
                "early_radar_score": None,
                "alert_level": None,
                "prob_1d": None,
                "prob_3d": None,
                "prob_5d": None,
                "expected_lead_days": None,
                "breadth_50": None,
                "confidence_score": None,
                "risk_score": None,
                "regime_label": regime,
                "parent_industry": str(row.get("niche_subsector")),
                "parent_sector": str(row.get("macro_sector")),
                "close_price": float(row.get("close")) if pd.notnull(row.get("close")) else None
            })

    inserted = ledger.record_decisions(records_to_insert)
    t1 = time.perf_counter()

    return {
        "trade_date": actual_date,
        "total_extracted": len(records_to_insert),
        "total_inserted": inserted,
        "execution_ms": round((t1 - t0) * 1000, 2)
    }

if __name__ == "__main__":
    from database.db import Database
    db = Database()
    dates = db.get_existing_price_dates()
    if dates:
        target_d = dates[0]
        print(f"Recording decisions for latest session: {target_d}...")
        res = record_daily_decisions_for_date(target_d)
        print(f"Result: {res}")
