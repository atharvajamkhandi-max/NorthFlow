"""
Professional Quantitative Research Laboratory for Cash Equity Markets.
Autonomous Alpha Discovery Engine.
"""

__version__ = "1.0.0"
__author__ = "Quantitative Research Group"

from .data.feed import CashMarketDataFeed
from .features.returns import compute_multi_horizon_returns
from .features.momentum import compute_momentum_factors
from .features.acceleration import compute_acceleration_and_curvature
from .features.trend import compute_trend_quality_factors
from .features.volatility import compute_volatility_surface
from .features.volume_delivery import compute_volume_delivery_factors
from .features.breadth_dispersion import compute_industry_breadth_and_dispersion
from .features.reversion_stationarity import compute_mean_reversion_factors
from .regimes.change_point import detect_change_points_cusum
from .regimes.hmm_states import estimate_7state_regime_probabilities
from .emergence.lead_lag import compute_lead_lag_correlations, eval_granger_causality
from .emergence.event_study import run_emergence_event_study
from .emergence.turnaround_detector import detect_industry_turnarounds
from .targets.multi_targets import generate_multi_horizon_targets
from .models.tournament import run_model_search_tournament
from .validation.walk_forward import PurgedWalkForwardValidator
