"""
Frozen Model Specification: EARLY_RADAR_V1_FROZEN.
Early Sector Radar Pre-Breakout Probability & Lead-Time Detection Engine.
Governance Rule: Zero parameter tuning during prospective out-of-sample validation.
"""

from typing import Dict, Any

EARLY_RADAR_V1_FROZEN: Dict[str, Any] = {
    "model_version": "EARLY_RADAR_V1_FROZEN",
    "feature_version": "PRECURSOR_7_FEATURE_SET",
    "calibration_method": "ISOTONIC_PROBABILITY_CALIBRATION_10_DECILES",
    "primary_horizon": "5D_MAJOR_EXPANSION",
    "supported_horizons": ["1D", "2D", "3D", "4D", "5D"],
    "created_at": "2026-08-24T01:00:00Z",
    "governance_status": "FROZEN_PROSPECTIVE_VALIDATION",
    
    # Feature Windows & Weights
    "accumulation_pressure_weights": {
        "breadth_acceleration_5d": 0.25,
        "volatility_compression_20_60": 0.25,
        "delivery_directional_intensity_20d": 0.25,
        "volume_ratio_20d": 0.25
    },
    "composite_radar_weights": {
        "pre_breakout_score": 0.50,
        "accumulation_pressure": 0.50,
        "extension_penalty_20d_max": 25.0
    },
    
    # Validated Alert Thresholds
    "alert_thresholds": {
        "PRE_BREAKOUT": 75.0,
        "EARLY": 65.0,
        "WATCH": 55.0,
        "NONE": 0.0
    },
    
    # Key Hypotheses & Cohort Rules
    "turnaround_cohort_rule": {
        "v3_2_max": 55.0,
        "early_radar_min": 65.0,
        "expected_lead_days_mean": 3.1
    },
    "cross_stock_synchronization_threshold": 55.0,
    
    # Historical Benchmark Performance (2020-2026 In-Sample + Holdout)
    "benchmarks": {
        "precision_at_1": "22.5%",
        "precision_at_3": "19.8%",
        "precision_at_5": "18.5%",
        "untouched_2026_precision_at_5": "17.4%",
        "baseline_lift_2026": "1.74x",
        "pre_event_discovery_rate": "87.5%",
        "average_lead_time_days": 3.1,
        "net_portfolio_cagr_30bps": "+25.2%",
        "portfolio_sharpe_30bps": 1.35,
        "portfolio_max_drawdown": "-9.8%"
    }
}
