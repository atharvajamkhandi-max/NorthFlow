"""
Probability Calibration and Brier Scoring.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

def calibrate_probabilities_platt(raw_scores: np.ndarray, binary_targets: np.ndarray) -> np.ndarray:
    """Applies Platt Scaling (Logistic Sigmoid Calibration)."""
    lr = LogisticRegression()
    lr.fit(raw_scores.reshape(-1, 1), binary_targets)
    calibrated_probs = lr.predict_proba(raw_scores.reshape(-1, 1))[:, 1]
    return calibrated_probs

def compute_brier_score(probabilities: np.ndarray, binary_targets: np.ndarray) -> float:
    """Computes Brier Calibration Score (lower is better, 0 is perfect)."""
    return float(brier_score_loss(binary_targets, probabilities))
