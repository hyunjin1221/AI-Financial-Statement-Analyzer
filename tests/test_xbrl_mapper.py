from app.services.xbrl_mapper import extract_latest_financials


def test_extract_latest_financials_prefers_latest_and_fallbacks() -> None:
    company_facts = {
        "facts": {
            "us-gaap": {
                "SalesRevenueNet": {
                    "units": {
                        "USD": [
                            {"end": "2023-12-31", "filed": "2024-01-31", "val": 1000},
                            {"end": "2024-12-31", "filed": "2025-01-31", "val": 1200},
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "filed": "2025-01-31", "val": 150},
                        ]
                    }
                },
                "Assets": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 3000}]}},
                "Liabilities": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 1800}]}},
                "StockholdersEquity": {
                    "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 1200}]}
                },
                "AssetsCurrent": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 900}]}},
                "LiabilitiesCurrent": {
                    "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 600}]}
                },
                "OperatingIncomeLoss": {
                    "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 220}]}
                },
                "InterestExpense": {
                    "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 40}]}
                },
            }
        }
    }

    values = extract_latest_financials(company_facts)
    assert values["revenue"] == 1200.0
    assert values["net_income"] == 150.0
    assert values["assets"] == 3000.0
    assert values["liabilities"] == 1800.0
    assert values["equity"] == 1200.0
    assert values["current_assets"] == 900.0
    assert values["current_liabilities"] == 600.0
    assert values["operating_income"] == 220.0
    assert values["interest_expense"] == 40.0
