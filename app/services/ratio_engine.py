from typing import Dict, Optional


def _safe_ratio(numerator: Optional[float], denominator: Optional[float], near_zero: float = 1e-9) -> Dict:
    if numerator is None or denominator is None:
        return {"value": None, "quality": "missing_data"}
    if abs(denominator) <= near_zero:
        return {"value": None, "quality": "unstable_denominator"}
    return {"value": numerator / denominator, "quality": "ok"}


def compute_ratios(financials: Dict[str, Optional[float]]) -> Dict[str, Dict]:
    ratios = {
        "current_ratio": _safe_ratio(
            financials.get("current_assets"),
            financials.get("current_liabilities"),
        ),
        "debt_to_equity": _safe_ratio(
            financials.get("liabilities"),
            financials.get("equity"),
        ),
        "net_margin": _safe_ratio(
            financials.get("net_income"),
            financials.get("revenue"),
        ),
        "roa": _safe_ratio(
            financials.get("net_income"),
            financials.get("assets"),
        ),
        "roe": _safe_ratio(
            financials.get("net_income"),
            financials.get("equity"),
        ),
        "operating_margin": _safe_ratio(
            financials.get("operating_income"),
            financials.get("revenue"),
        ),
        # Interest coverage is commonly EBIT/interest expense; operating income is a reasonable free-data proxy.
        "interest_coverage": _safe_ratio(
            financials.get("operating_income"),
            financials.get("interest_expense"),
        ),
    }
    return ratios
