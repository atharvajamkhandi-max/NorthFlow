"""
7-State Transition Probability Engine.
States: Lagging, Stabilizing, Emerging, Accelerating, Leading, Weakening, Distributing.
"""
import pandas as pd
import numpy as np

def estimate_7state_regime_probabilities(breadth: float, rs_20d: float, delivery_intensity: float) -> dict:
    """
    Estimates continuous probabilities across 7 market/sector lifecycle states.
    All probabilities sum to 1.0.
    """
    # Softmax scores based on orthogonal economic dimensions
    scores = {
        "Lagging": max(0.01, (100.0 - breadth) * 0.4 - rs_20d * 0.3),
        "Stabilizing": max(0.01, (50.0 - abs(breadth - 40.0)) * 0.3 + delivery_intensity * 0.2),
        "Emerging": max(0.01, (breadth - 40.0) * 0.3 + rs_20d * 0.4 + delivery_intensity * 0.5),
        "Accelerating": max(0.01, (breadth - 60.0) * 0.4 + rs_20d * 0.5 + delivery_intensity * 0.3),
        "Leading": max(0.01, (breadth - 75.0) * 0.5 + rs_20d * 0.5),
        "Weakening": max(0.01, (75.0 - breadth) * 0.3 - delivery_intensity * 0.4),
        "Distributing": max(0.01, (100.0 - breadth) * 0.5 - rs_20d * 0.4 - delivery_intensity * 0.5)
    }
    
    exp_scores = {k: np.exp(min(v / 10.0, 5.0)) for k, v in scores.items()}
    total = sum(exp_scores.values())
    probs = {k: round(v / total, 4) for k, v in exp_scores.items()}
    return probs
