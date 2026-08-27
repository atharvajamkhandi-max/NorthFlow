"""
Unit and Integration Test Suite for Professional Quantitative Research Laboratory (quant_lab).
Validates mathematical invariants, point-in-time integrity, lead-lag discovery,
probability calibration, and anti-leakage embargo controls.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from quant_lab.data.feed import CashMarketDataFeed
from quant_lab.data.corporate_actions import adjust_for_splits
from quant_lab.data.validation import assert_point_in_time
from quant_lab.features.returns import compute_multi_horizon_returns
from quant_lab.features.momentum import compute_momentum_factors
from quant_lab.features.acceleration import compute_acceleration_and_curvature
from quant_lab.features.trend import compute_trend_quality_factors
from quant_lab.features.volatility import compute_volatility_surface
from quant_lab.features.volume_delivery import compute_volume_delivery_factors
from quant_lab.features.breadth_dispersion import compute_industry_breadth_and_dispersion
from quant_lab.features.reversion_stationarity import compute_mean_reversion_factors
from quant_lab.features.interactions import compute_nonlinear_interactions
from quant_lab.regimes.change_point import detect_change_points_cusum
from quant_lab.regimes.hmm_states import estimate_7state_regime_probabilities
from quant_lab.emergence.lead_lag import compute_lead_lag_correlations, eval_granger_causality
from quant_lab.emergence.turnaround_detector import detect_industry_turnarounds
from quant_lab.targets.multi_targets import generate_multi_horizon_targets
from quant_lab.validation.walk_forward import PurgedWalkForwardValidator
from quant_lab.validation.decile_analysis import compute_decile_spreads
from quant_lab.validation.cost_stress import run_transaction_cost_stress_test
from quant_lab.portfolio.risk_engine import compute_portfolio_var

@pytest.fixture
def sample_cash_data():
    """Generates synthetic multi-symbol daily cash market dataframe for deterministic testing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='B')
    records = []
    
    for sym, ind in [('STOCK_A', 'Banking'), ('STOCK_B', 'Banking'), ('STOCK_C', 'IT')]:
        np.random.seed(42 if sym == 'STOCK_A' else 123)
        prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, size=len(dates))))
        volumes = np.random.uniform(50000, 200000, size=len(dates))
        deliv_qtys = volumes * np.random.uniform(0.4, 0.8, size=len(dates))
        
        for i, d in enumerate(dates):
            p = prices[i]
            records.append({
                'symbol': sym,
                'date': d,
                'open': p * 0.99,
                'high': p * 1.02,
                'low': p * 0.98,
                'close': p,
                'volume': volumes[i],
                'turnover': p * volumes[i],
                'trades': int(volumes[i] / 50),
                'deliv_qty': deliv_qtys[i],
                'deliv_per': (deliv_qtys[i] / volumes[i]) * 100.0,
                'sector': 'Financials' if ind == 'Banking' else 'Technology',
                'industry': ind
            })
            
    df = pd.DataFrame(records)
    return df

def test_point_in_time_validation(sample_cash_data):
    """Verify point-in-time timestamp monotonicity."""
    assert assert_point_in_time(sample_cash_data) is True

def test_returns_and_momentum_factors(sample_cash_data):
    """Verify multi-horizon returns and momentum metrics."""
    df_ret = compute_multi_horizon_returns(sample_cash_data, horizons=[1, 5, 20])
    assert 'ret_1d' in df_ret.columns
    assert 'ret_5d' in df_ret.columns
    assert 'ret_20d' in df_ret.columns
    
    df_mom = compute_momentum_factors(df_ret)
    assert 'risk_adj_mom_20d' in df_mom.columns
    assert 'cs_mom_rank_20d' in df_mom.columns

def test_acceleration_and_curvature(sample_cash_data):
    """Verify first and second derivative calculations."""
    df_ret = compute_multi_horizon_returns(sample_cash_data, horizons=[20])
    df_acc = compute_acceleration_and_curvature(df_ret, signal_col='ret_20d', lookbacks=[5])
    assert 'ret_20d_acc_5d' in df_acc.columns
    assert 'ret_20d_curv_5d' in df_acc.columns

def test_trend_quality_and_rolling_regression(sample_cash_data):
    """Verify TrendQuality formulation and EMA distances."""
    df_trend = compute_trend_quality_factors(sample_cash_data, horizons=[20, 50])
    assert 'dist_ema_20' in df_trend.columns
    assert 'trend_quality_20d' in df_trend.columns
    # Bounded sanity check
    assert not df_trend['trend_quality_20d'].isnull().all()

def test_volatility_surface_estimators(sample_cash_data):
    """Verify Parkinson volatility and compression ratios are strictly non-negative."""
    df_vol = compute_volatility_surface(sample_cash_data, window=20)
    assert (df_vol['vol_parkinson_20d'] >= 0.0).all()
    assert (df_vol['vol_close_20d'] >= 0.0).all()
    assert (df_vol['vol_compression_ratio'] > 0.0).all()

def test_volume_delivery_factors(sample_cash_data):
    """Verify directional delivery intensity and volume Z-scores."""
    df_vd = compute_volume_delivery_factors(sample_cash_data)
    assert 'vol_ratio_20d' in df_vd.columns
    assert 'deliv_directional_intensity' in df_vd.columns

def test_breadth_and_dispersion(sample_cash_data):
    """Verify industry breadth and return dispersion calculations."""
    df_b = compute_industry_breadth_and_dispersion(sample_cash_data)
    assert 'industry_breadth_50' in df_b.columns
    assert 'breadth_impulse_10d' in df_b.columns
    assert 'industry_dispersion' in df_b.columns

def test_mean_reversion_ou_half_life(sample_cash_data):
    """Verify Ornstein-Uhlenbeck half life and price Z-scores."""
    df_mr = compute_mean_reversion_factors(sample_cash_data, window=20)
    assert 'price_zscore_20d' in df_mr.columns
    assert 'ou_half_life_20d' in df_mr.columns
    assert (df_mr['ou_half_life_20d'] > 0).all()

def test_regime_change_point_and_7state_hmm(sample_cash_data):
    """Verify CUSUM filter and 7-state regime probabilities sum to 1.0."""
    series = sample_cash_data[sample_cash_data['symbol'] == 'STOCK_A']['close']
    cp_signals = detect_change_points_cusum(series)
    assert len(cp_signals) == len(series)
    assert set(cp_signals.unique()).issubset({-1, 0, 1})
    
    probs = estimate_7state_regime_probabilities(breadth=65.0, rs_20d=4.5, delivery_intensity=1.8)
    assert len(probs) == 7
    assert pytest.approx(sum(probs.values()), 0.01) == 1.0

def test_lead_lag_and_granger_causality():
    """Verify lead-lag correlation and Granger causality discovery."""
    np.random.seed(42)
    # Feature leads target by 5 steps
    x = np.random.normal(0, 1, 100)
    y = np.roll(x, -5) + np.random.normal(0, 0.2, 100)
    s_x = pd.Series(x)
    s_y = pd.Series(y)
    
    ll_res = compute_lead_lag_correlations(s_x, s_y, horizons=[1, 3, 5, 10])
    assert not ll_res.empty
    assert 'Rank_IC' in ll_res.columns
    
    gc_res = eval_granger_causality(s_x, s_y, max_lag=5)
    assert 'Granger_Causes' in gc_res
    assert 'F_stat' in gc_res

def test_purged_walk_forward_embargo_split(sample_cash_data):
    """Verify purged walk-forward validator creates strictly non-overlapping train/test windows with embargo."""
    validator = PurgedWalkForwardValidator(n_splits=3, embargo_sessions=5)
    splits = list(validator.generate_splits(sample_cash_data))
    assert len(splits) == 3
    
    for split_idx, tr_mask, te_mask, tr_dates, te_dates in splits:
        # Check no overlap between train and test dates
        assert set(tr_dates).isdisjoint(set(te_dates))
        # Check embargo gap >= 5 trading sessions
        max_tr = max(tr_dates)
        min_te = min(te_dates)
        unique_dates = sorted(sample_cash_data['date'].unique())
        tr_idx = unique_dates.index(max_tr)
        te_idx = unique_dates.index(min_te)
        assert (te_idx - tr_idx) >= 5

def test_cost_stress_and_risk_engine():
    """Verify transaction cost stress testing and Value-at-Risk calculations."""
    stress_df = run_transaction_cost_stress_test(gross_cagr=28.0)
    assert len(stress_df) == 7
    assert 'Round_Trip_Cost_bps' in stress_df.columns
    
    returns = np.random.normal(0.001, 0.02, 500)
    var_res = compute_portfolio_var(returns, confidence=0.95)
    assert 'VaR' in var_res
    assert 'CVaR' in var_res
    assert var_res['CVaR'] >= var_res['VaR']
