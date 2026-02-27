from typing import Dict, Optional


CONCEPT_MAP = {
    "revenue": ["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "operating_income": ["OperatingIncomeLoss"],
    "interest_expense": ["InterestExpense"],
}


def _latest_value_for_concept(us_gaap_facts: Dict, concept: str) -> Optional[float]:
    concept_payload = us_gaap_facts.get(concept)
    if not concept_payload:
        return None

    units = concept_payload.get("units", {})
    usd_points = units.get("USD", [])
    if not usd_points:
        return None

    # Prefer newest by end date and filing date.
    sorted_points = sorted(
        usd_points,
        key=lambda x: (str(x.get("end", "")), str(x.get("filed", ""))),
        reverse=True,
    )
    for point in sorted_points:
        value = point.get("val")
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def extract_latest_financials(company_facts: Dict) -> Dict[str, Optional[float]]:
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    result: Dict[str, Optional[float]] = {}

    for metric, concepts in CONCEPT_MAP.items():
        value: Optional[float] = None
        for concept in concepts:
            value = _latest_value_for_concept(us_gaap, concept)
            if value is not None:
                break
        result[metric] = value

    return result
