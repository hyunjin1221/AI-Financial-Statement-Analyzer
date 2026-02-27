from app.services.ratio_engine import compute_ratios


def test_compute_ratios_basic() -> None:
    financials = {
        "current_assets": 200.0,
        "current_liabilities": 100.0,
        "liabilities": 300.0,
        "equity": 150.0,
        "net_income": 50.0,
        "revenue": 500.0,
        "assets": 400.0,
        "operating_income": 80.0,
        "interest_expense": 20.0,
    }
    ratios = compute_ratios(financials)
    assert ratios["current_ratio"]["value"] == 2.0
    assert ratios["debt_to_equity"]["value"] == 2.0
    assert ratios["net_margin"]["value"] == 0.1
    assert ratios["roa"]["value"] == 0.125
    assert ratios["roe"]["value"] == 1 / 3
    assert ratios["operating_margin"]["value"] == 0.16
    assert ratios["interest_coverage"]["value"] == 4.0
    assert all(v["quality"] == "ok" for v in ratios.values())


def test_compute_ratios_missing_and_unstable() -> None:
    financials = {
        "current_assets": None,
        "current_liabilities": 100.0,
        "liabilities": 100.0,
        "equity": 0.0,
        "net_income": 10.0,
        "revenue": None,
        "assets": 0.0,
        "operating_income": 5.0,
        "interest_expense": None,
    }
    ratios = compute_ratios(financials)
    assert ratios["current_ratio"]["quality"] == "missing_data"
    assert ratios["debt_to_equity"]["quality"] == "unstable_denominator"
    assert ratios["net_margin"]["quality"] == "missing_data"
    assert ratios["roa"]["quality"] == "unstable_denominator"
    assert ratios["interest_coverage"]["quality"] == "missing_data"
