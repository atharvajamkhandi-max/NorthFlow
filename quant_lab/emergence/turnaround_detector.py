"""
Early Turnaround & Accumulation Detection Radar.
"""
import pandas as pd
import numpy as np

def detect_industry_turnarounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scans for industries in early accumulation:
    - Oversold on 60D return (< -5%)
    - Breadth expanding (Breadth_20 > Breadth_50)
    - High directional delivery intensity
    - Volatility compression (< 0.85)
    """
    candidates = []
    for (ind, d), grp in df.groupby(['industry', 'date']):
        b20 = grp['industry_breadth_20'].iloc[0] if 'industry_breadth_20' in grp.columns else 50.0
        b50 = grp['industry_breadth_50'].iloc[0] if 'industry_breadth_50' in grp.columns else 50.0
        deliv = grp['deliv_directional_intensity'].mean() if 'deliv_directional_intensity' in grp.columns else 0.0
        vol_ratio = grp['vol_compression_ratio'].mean() if 'vol_compression_ratio' in grp.columns else 1.0
        
        # Turnaround score
        if b20 > b50 and deliv > 0 and vol_ratio < 1.0:
            turnaround_strength = (b20 - b50) * 0.5 + deliv * 10.0 + (1.0 - vol_ratio) * 20.0
            candidates.append({
                "industry": ind,
                "date": d,
                "turnaround_score": round(float(turnaround_strength), 2),
                "breadth_20": round(b20, 1),
                "breadth_50": round(b50, 1),
                "delivery_intensity": round(deliv, 2),
                "compression_ratio": round(vol_ratio, 2)
            })
            
    return pd.DataFrame(candidates)
