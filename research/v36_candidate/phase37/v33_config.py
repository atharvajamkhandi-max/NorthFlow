"""
research/v36_candidate/phase37/v33_config.py
Isolated configuration and feature flags for MODEL_V3.3_CANDIDATE.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class V33Config:
    model_version: str = "MODEL_V3.3_CANDIDATE"
    specification_version: str = "3.3.0-CANDIDATE"
    use_hgb: bool = True
    use_conformal: bool = True
    use_regime_60d: bool = True
    use_cross_sectional_rank: bool = True
    use_parent_industry_stock_projection: bool = True
    
    # Hyperparameters
    hgb_max_iter: int = 80
    hgb_max_depth: int = 4
    hgb_l2_reg: float = 2.0
    hgb_learning_rate: float = 0.1
    random_state: int = 42
    
    # Calibration parameters
    conformal_quantile_scale: float = 1.30
    regime_60d_offsets: dict = None

    def __post_init__(self):
        if self.regime_60d_offsets is None:
            object.__setattr__(self, 'regime_60d_offsets', {
                "WEAK_BULL": 12.22,
                "WEAK_BEAR": -5.67,
                "SIDEWAYS": 4.01,
                "HIGH_VOLATILITY": 0.0
            })
