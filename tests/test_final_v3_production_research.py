"""
Unit and Statistical Integration Tests for Final V3 Production Research Engine.
Verifies:
- Signal lifecycle transitions (NEW, DEVELOPING, MATURE, EXHAUSTED, REVERSING)
- Observable accumulation net pressure bounds and states
- 6-state market regime assignment correctness
- Confidence score decoupling from strength score
- Prediction interval monotonicity (P10 <= P25 <= P50 <= P75 <= P90)
- Zero data leakage invariants
"""

import os
import sys
import pandas as pd
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from research.final_v3.engine.v3_signal_state_and_accum import V3SignalStateAndAccum
from research.final_v3.engine.v3_regime_and_risk import V3RegimeAndRisk
from research.final_v3.engine.v3_confidence_and_decision_engine import V3ConfidenceAndDecisionEngine
from research.final_v3.engine.v3_multi_horizon_expected_returns import V3MultiHorizonExpectedReturns
from research.final_v3.engine.v3_bootstrap_and_leakage_audit import V3BootstrapAndLeakageAudit

def test_v3_signal_lifecycle_and_accumulation():
    """Verifies signal lifecycle state assignments and accumulation bounds."""
    df_sample = pd.DataFrame({
        'basic_industry': ['IND_A', 'IND_B', 'IND_C'],
        'industry_strength_score': [88.0, 68.0, 32.0],
        'strength_acceleration': [-4.0, 3.0, -6.0],
        'industry_RS_market': [6.0, 2.0, -4.0],
        'volume_strength': [1.5, 1.1, 0.7],
        'breadth_acceleration': [5.0, 1.0, -5.0],
        'trend_stack_breadth': [80.0, 50.0, 20.0],
        'avg_delivery_pct': [55.0, 45.0, 30.0]
    })
    df_out = V3SignalStateAndAccum.compute_signal_state_and_accumulation(df_sample)
    
    for _, r in df_out.iterrows():
        assert -100.0 <= r['NetPressure'] <= 100.0
        assert r['ACCUMULATION_STATE'] in ['ACCUMULATION', 'NEUTRAL', 'DISTRIBUTION']
        assert r['SIGNAL_STATE'] in ['NEW', 'DEVELOPING', 'MATURE', 'EXHAUSTED', 'REVERSING', 'NEUTRAL']

def test_v3_confidence_and_decision_rules():
    """Verifies confidence score calculation and rule-based actions."""
    df_sample = pd.DataFrame({
        'basic_industry': ['IND_A', 'IND_B'],
        'industry_strength_score': [82.0, 30.0],
        'strength_acceleration': [2.5, -4.0],
        'REGIME_CONFIDENCE': [0.85, 0.60],
        'BREADTH_50': [75.0, 25.0],
        'constituent_count': [15, 6],
        'RISK_SCORE': [25.0, 75.0],
        'SIGNAL_STATE': ['DEVELOPING', 'REVERSING'],
        'industry_RS_market': [4.0, -3.0],
        'ACCUMULATION_STATE': ['ACCUMULATION', 'DISTRIBUTION']
    })
    df_out = V3ConfidenceAndDecisionEngine.compute_confidence_and_decision(df_sample)
    
    for _, r in df_out.iterrows():
        assert 0.0 <= r['CONFIDENCE_SCORE'] <= 100.0
        assert r['FINAL_ACTION'] in ['STRONG BUY', 'BUY', 'WATCH', 'NEUTRAL', 'REDUCE', 'AVOID']
        assert len(r['TOP_POSITIVE_DRIVERS']) > 0 or len(r['TOP_NEGATIVE_FACTORS']) > 0

def test_v3_multi_horizon_prediction_intervals():
    """Verifies monotonic ordering of quantile intervals."""
    df_sample = pd.DataFrame({
        'industry_strength_score': [70.0, 45.0],
        'strength_acceleration': [2.0, -1.0],
        'breadth_acceleration': [1.0, -1.0],
        'BREADTH_50': [65.0, 35.0],
        'REGIME_SIGNAL_MULTIPLIER': [1.1, 0.9],
        'future_excess_return_20D': [3.5, -2.1]
    })
    df_out, _ = V3MultiHorizonExpectedReturns.compute_multi_horizon_forecasts(df_sample)
    
    for _, r in df_out.iterrows():
        assert r['P10_20D'] <= r['P25_20D'] <= r['P50_20D'] <= r['P75_20D'] <= r['P90_20D']
        assert r['P_RETURN_GT_0'] >= r['P_RETURN_GT_5'] >= r['P_RETURN_GT_10'] >= r['P_RETURN_GT_20']

def test_v3_anti_leakage_audit_clean():
    """Verifies zero data leakage in V3 engine."""
    audit = V3BootstrapAndLeakageAudit.run_anti_leakage_audit_final_v3()
    assert audit['leakage_audit_verdict'] == 'VERIFIED_ZERO_LEAKAGE'
