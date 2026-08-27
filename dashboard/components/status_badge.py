"""
Status Badge and Score Helper.
"""

def format_status_badge(status: str) -> str:
    """
    Returns styled HTML badge for a rotation status.
    """
    s_upper = str(status).strip().upper()
    css_class = "status-weak"
    if s_upper == "EMERGING":
        css_class = "status-emerging"
    elif s_upper == "STRONG":
        css_class = "status-strong"
    elif s_upper == "STRENGTHENING":
        css_class = "status-strengthening"
    elif s_upper in ("COOLING", "WEAKENING"):
        css_class = "status-cooling"
    elif s_upper == "EXHAUSTION":
        css_class = "status-exhaustion"
    elif s_upper == "WEAK":
        css_class = "status-weak"

    return f'<span class="status-pill {css_class}">{s_upper}</span>'

def format_strength_bar(score: float) -> str:
    """
    Returns compact ASCII strength indicator.
    """
    if score is None or score < 0:
        return "N/A"
    filled = int(round(score / 10.0))
    filled = max(0, min(10, filled))
    empty = 10 - filled
    return f"{'█' * filled}{'░' * empty} {score:.1f}"
