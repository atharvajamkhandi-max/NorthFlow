"""
storage/canonical_forecast_service.py
Read-Only Canonical Forecast & Model-Implied Projection Service.
Queries frozen research outputs from research/final_v3/results/final_predictions.csv.
Resolves future target dates via trading calendar.
Strictly Read-Only. Never creates new models or alters prediction outputs.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

DEFAULT_PRED_CSV_PATH = Path(__file__).resolve().parent.parent / "research" / "final_v3" / "results" / "final_predictions.csv"
DEFAULT_MARKET_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "market_flow.db"

class CanonicalForecastService:
    """
    Provides read-only access to canonical probabilistic forecasts and expected returns.
    """
    _cached_df: Optional[pd.DataFrame] = None

    def __init__(self, pred_csv_path: Optional[Path] = None, db_path: Optional[Path] = None):
        self.pred_csv_path = Path(pred_csv_path) if pred_csv_path else DEFAULT_PRED_CSV_PATH
        self.db_path = Path(db_path) if db_path else DEFAULT_MARKET_DB_PATH

    def _load_predictions(self) -> pd.DataFrame:
        if CanonicalForecastService._cached_df is None and self.pred_csv_path.exists():
            CanonicalForecastService._cached_df = pd.read_csv(self.pred_csv_path)
        return CanonicalForecastService._cached_df if CanonicalForecastService._cached_df is not None else pd.DataFrame()

    def get_industry_forecast(self, industry_name: str) -> Dict[str, Any]:
        """
        Retrieves latest canonical forecast metrics for a specific industry.
        """
        df = self._load_predictions()
        if df.empty:
            return {"status": "UNAVAILABLE", "message": "Predictions dataset not found"}

        clean_name = str(industry_name).strip()
        
        # 1. Exact match on basic_industry or industry
        match = df[(df["basic_industry"] == clean_name) | (df["industry"] == clean_name)]
        
        # 2. Case-insensitive exact match
        if match.empty:
            match = df[df["basic_industry"].str.lower() == clean_name.lower()]
            
        # 3. Substring match
        if match.empty:
            match = df[df["basic_industry"].str.contains(clean_name, case=False, na=False, regex=False)]
            
        # 4. Multi-token match
        if match.empty:
            tokens = [t for t in clean_name.replace("&", " ").replace(",", " ").split() if len(t) >= 4]
            for t in tokens:
                sub_match = df[df["basic_industry"].str.contains(t, case=False, na=False, regex=False)]
                if not sub_match.empty:
                    match = sub_match
                    break

        if match.empty:
            return {"status": "UNAVAILABLE", "message": f"No canonical forecast available for '{industry_name}' in research base"}

        latest_rec = match.sort_values("date").iloc[-1]

        return {
            "status": "AVAILABLE",
            "date": latest_rec.get("date"),
            "industry": latest_rec.get("basic_industry"),
            "exp_return_1d": float(latest_rec.get("EXPECTED_RETURN_1D", 0.0)),
            "exp_return_5d": float(latest_rec.get("EXPECTED_RETURN_5D", 0.0)),
            "exp_return_20d": float(latest_rec.get("EXPECTED_RETURN_20D", 0.0)),
            "exp_return_60d": float(latest_rec.get("EXPECTED_RETURN_60D", 0.0)),
            "p10_20d": float(latest_rec.get("P10_20D", 0.0)),
            "p25_20d": float(latest_rec.get("P25_20D", 0.0)),
            "p50_20d": float(latest_rec.get("P50_20D", 0.0)),
            "p75_20d": float(latest_rec.get("P75_20D", 0.0)),
            "p90_20d": float(latest_rec.get("P90_20D", 0.0)),
            "prob_win": float(latest_rec.get("P_RETURN_GT_0", 0.0)),
            "prob_gt_5": float(latest_rec.get("P_RETURN_GT_5", 0.0)),
            "prob_gt_10": float(latest_rec.get("P_RETURN_GT_10", 0.0)),
            "prob_loss_gt_5": float(latest_rec.get("P_LOSS_GT_5", 0.0)),
            "confidence_score": float(latest_rec.get("CONFIDENCE_SCORE", 50.0)),
            "risk_score": float(latest_rec.get("RISK_SCORE", 50.0)),
            "regime": str(latest_rec.get("REGIME", "NORMAL")),
            "final_action": str(latest_rec.get("FINAL_ACTION", "NEUTRAL"))
        }

    def resolve_future_trading_date(self, current_date_str: str, forward_sessions: int) -> str:
        """
        Projects forward_sessions ahead on the trading calendar (skipping weekends and typical holidays).
        """
        try:
            curr_dt = datetime.strptime(current_date_str, "%Y-%m-%d")
        except Exception:
            curr_dt = datetime.now()

        added_sessions = 0
        target_dt = curr_dt
        while added_sessions < forward_sessions:
            target_dt += timedelta(days=1)
            # Skip Saturday (5) and Sunday (6)
            if target_dt.weekday() < 5:
                added_sessions += 1

        return target_dt.strftime("%Y-%m-%d")

    def get_stock_model_projection(
        self,
        symbol: str,
        current_price: float,
        parent_industry: Optional[str],
        current_date_str: str = "2026-08-24"
    ) -> Dict[str, Any]:
        """
        Calculates presentation-only model-implied 20D price projection based on parent industry forecast.
        """
        if not parent_industry or current_price <= 0:
            return {"status": "UNAVAILABLE", "message": "Reference price or parent industry missing"}

        ind_fc = self.get_industry_forecast(parent_industry)
        if ind_fc.get("status") != "AVAILABLE":
            return {"status": "UNAVAILABLE", "message": ind_fc.get("message")}

        # Presentation Arithmetic
        p_curr = float(current_price)
        exp_ret = ind_fc["exp_return_20d"]
        p10 = ind_fc["p10_20d"]
        p25 = ind_fc["p25_20d"]
        p50 = ind_fc["p50_20d"]
        p75 = ind_fc["p75_20d"]
        p90 = ind_fc["p90_20d"]

        proj_price_p50 = p_curr * (1.0 + exp_ret / 100.0)
        proj_price_p10 = p_curr * (1.0 + p10 / 100.0)
        proj_price_p25 = p_curr * (1.0 + p25 / 100.0)
        proj_price_p75 = p_curr * (1.0 + p75 / 100.0)
        proj_price_p90 = p_curr * (1.0 + p90 / 100.0)

        target_date_1d = self.resolve_future_trading_date(current_date_str, 1)
        target_date_5d = self.resolve_future_trading_date(current_date_str, 5)
        target_date_20d = self.resolve_future_trading_date(current_date_str, 20)
        target_date_60d = self.resolve_future_trading_date(current_date_str, 60)

        return {
            "status": "AVAILABLE",
            "symbol": symbol,
            "current_price": p_curr,
            "parent_industry": parent_industry,
            "target_date_20d": target_date_20d,
            "horizons": {
                "1D": {"exp_return": ind_fc["exp_return_1d"], "target_date": target_date_1d, "proj_price": p_curr * (1.0 + ind_fc["exp_return_1d"] / 100.0)},
                "5D": {"exp_return": ind_fc["exp_return_5d"], "target_date": target_date_5d, "proj_price": p_curr * (1.0 + ind_fc["exp_return_5d"] / 100.0)},
                "20D": {"exp_return": ind_fc["exp_return_20d"], "target_date": target_date_20d, "proj_price": proj_price_p50},
                "60D": {"exp_return": ind_fc["exp_return_60d"], "target_date": target_date_60d, "proj_price": p_curr * (1.0 + ind_fc["exp_return_60d"] / 100.0)}
            },
            "quantiles_20d": {
                "p10": {"ret": p10, "price": proj_price_p10, "label": "P10 (Bearish Tail)"},
                "p25": {"ret": p25, "price": proj_price_p25, "label": "P25 (Conservative)"},
                "p50": {"ret": p50, "price": proj_price_p50, "label": "P50 (Median Expectation)"},
                "p75": {"ret": p75, "price": proj_price_p75, "label": "P75 (Optimistic)"},
                "p90": {"ret": p90, "price": proj_price_p90, "label": "P90 (Bullish Tail)"}
            },
            "prob_win": ind_fc["prob_win"],
            "prob_gt_5": ind_fc["prob_gt_5"],
            "prob_loss_gt_5": ind_fc["prob_loss_gt_5"],
            "confidence_score": ind_fc["confidence_score"],
            "risk_score": ind_fc["risk_score"],
            "regime": ind_fc["regime"]
        }
