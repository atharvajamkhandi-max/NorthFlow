"""
Transaction Cost Stress Lab (0 to 100 bps).
"""
import pandas as pd
import numpy as np

def run_transaction_cost_stress_test(gross_cagr: float, 
                                     rebalance_horizon_days: int = 20, 
                                     costs_bps: list = [0, 10, 20, 30, 50, 75, 100]) -> pd.DataFrame:
    """Evaluates strategy CAGR and Sharpe net of transaction friction."""
    results = []
    turnover_factor = 252.0 / rebalance_horizon_days
    
    for cost in costs_bps:
        cost_drag = (cost / 10000.0) * turnover_factor * 100.0
        net_cagr = gross_cagr - cost_drag
        net_sharpe = round(net_cagr / 22.0, 2)
        
        results.append({
            "Round_Trip_Cost_bps": cost,
            "Gross_CAGR": f"{gross_cagr:+.1f}%",
            "Annual_Cost_Drag": f"-{cost_drag:.2f}%",
            "Net_CAGR": f"{net_cagr:+.1f}%",
            "Net_Sharpe": net_sharpe,
            "Viable": "YES" if net_cagr > 15.0 else "NO"
        })
        
    return pd.DataFrame(results)
