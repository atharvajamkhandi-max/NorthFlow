"""
Intelligent Feature Selection and Collinearity Pruning.
"""
import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_regression

def prune_collinear_features(df_features: pd.DataFrame, max_correlation: float = 0.85) -> list:
    """Removes highly collinear redundant features."""
    corr_matrix = df_features.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > max_correlation)]
    kept = [c for c in df_features.columns if c not in to_drop]
    return kept

def select_features_mutual_info(X: pd.DataFrame, y: pd.Series, top_k: int = 15) -> list:
    """Selects top K features using mutual information with the forward target."""
    valid_idx = X.dropna().index.intersection(y.dropna().index)
    X_clean = X.loc[valid_idx]
    y_clean = y.loc[valid_idx]
    
    if len(X_clean) < 50:
        return list(X.columns[:top_k])
        
    mi = mutual_info_regression(X_clean, y_clean, random_state=42)
    mi_series = pd.Series(mi, index=X.columns).sort_values(ascending=False)
    return mi_series.head(top_k).index.tolist()
