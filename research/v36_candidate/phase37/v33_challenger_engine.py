"""
research/v36_candidate/phase37/v33_challenger_engine.py
Isolated Inference and Shadow Engine for MODEL_V3.3_CANDIDATE.
Operates strictly point-in-time on isolated data structures.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import HistGradientBoostingRegressor

try:
    from .v33_config import V33Config
except Exception:
    from v33_config import V33Config

class V33ChallengerEngine:
    def __init__(self, config: Optional[V33Config] = None):
        self.config = config or V33Config()
        self.model = HistGradientBoostingRegressor(
            max_iter=self.config.hgb_max_iter,
            max_depth=self.config.hgb_max_depth,
            l2_regularization=self.config.hgb_l2_reg,
            learning_rate=self.config.hgb_learning_rate,
            random_state=self.config.random_state
        )
        self.feature_cols = ["industry_return_1d", "breadth_50", "RISK_SCORE", "CONFIDENCE_SCORE"]
        self.is_fitted = False

    def fit_historical_partition(self, df_train: pd.DataFrame, target_col: str = "future_return_20D"):
        clean_train = df_train.dropna(subset=self.feature_cols + [target_col])
        if len(clean_train) > 0:
            self.model.fit(clean_train[self.feature_cols], clean_train[target_col])
            self.is_fitted = True

    def generate_shadow_prediction(self, row: pd.Series) -> Dict[str, Any]:
        mid_20 = float(row.get("EXPECTED_RETURN_20D", 0.0))
        p10_raw = float(row.get("P10_20D", mid_20 - 10.0))
        p90_raw = float(row.get("P90_20D", mid_20 + 10.0))
        regime = str(row.get("REGIME", "SIDEWAYS"))
        raw_60 = float(row.get("EXPECTED_RETURN_60D", 0.0))
        
        # 1. HGB or Baseline 20D Expected Return
        if self.config.use_hgb and self.is_fitted:
            feat_vals = np.array([[
                float(row.get("industry_return_1d", 0.0)),
                float(row.get("breadth_50", 50.0)),
                float(row.get("RISK_SCORE", 50.0)),
                float(row.get("CONFIDENCE_SCORE", 50.0))
            ]])
            exp_ret_20 = float(self.model.predict(feat_vals)[0])
        else:
            exp_ret_20 = mid_20

        # 2. Conformal Quantile Scaling
        if self.config.use_conformal:
            s = self.config.conformal_quantile_scale
            p10_cal = exp_ret_20 + (p10_raw - mid_20) * s
            p90_cal = exp_ret_20 + (p90_raw - mid_20) * s
        else:
            p10_cal, p90_cal = p10_raw, p90_raw

        # 3. Regime-Aware 60D Calibration
        if self.config.use_regime_60d:
            offset = self.config.regime_60d_offsets.get(regime, 0.0)
            exp_ret_60_cal = raw_60 - offset
        else:
            exp_ret_60_cal = raw_60

        return {
            "prediction_date": str(row.get("date")),
            "entity_id": str(row.get("basic_industry")),
            "entity_type": "INDUSTRY",
            "model_version": self.config.model_version,
            "expected_return_20d": round(exp_ret_20, 2),
            "p10_20d_calibrated": round(p10_cal, 2),
            "p90_20d_calibrated": round(p90_cal, 2),
            "expected_return_60d_calibrated": round(exp_ret_60_cal, 2),
            "regime": regime,
            "rating_action": str(row.get("FINAL_ACTION", "NEUTRAL")),
            "confidence_score": float(row.get("CONFIDENCE_SCORE", 50.0)),
            "risk_score": float(row.get("RISK_SCORE", 50.0))
        }
