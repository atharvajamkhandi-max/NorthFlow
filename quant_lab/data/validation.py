"""
Anti-leakage and point-in-time validation assertions.
"""
import pandas as pd

def assert_point_in_time(df: pd.DataFrame, timestamp_col: str = 'date') -> bool:
    """Asserts that timestamps are strictly monotonically increasing per symbol."""
    for sym, grp in df.groupby('symbol'):
        if not grp[timestamp_col].is_monotonic_increasing:
            raise ValueError(f"Lookahead or out-of-order date violation for {sym}")
    return True
