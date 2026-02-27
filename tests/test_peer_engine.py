from app.services.peer_engine import aggregate_peer_ratio_medians, compare_company_to_peer


def test_aggregate_peer_ratio_medians() -> None:
    peer_ratios = [
        {
            "current_ratio": {"value": 2.0, "quality": "ok"},
            "debt_to_equity": {"value": 1.5, "quality": "ok"},
            "net_margin": {"value": 0.10, "quality": "ok"},
            "roa": {"value": 0.05, "quality": "ok"},
            "roe": {"value": 0.12, "quality": "ok"},
            "operating_margin": {"value": 0.15, "quality": "ok"},
            "interest_coverage": {"value": 6.0, "quality": "ok"},
        },
        {
            "current_ratio": {"value": 1.0, "quality": "ok"},
            "debt_to_equity": {"value": 2.5, "quality": "ok"},
            "net_margin": {"value": 0.06, "quality": "ok"},
            "roa": {"value": 0.03, "quality": "ok"},
            "roe": {"value": 0.08, "quality": "ok"},
            "operating_margin": {"value": 0.10, "quality": "ok"},
            "interest_coverage": {"value": 4.0, "quality": "ok"},
        },
    ]
    medians = aggregate_peer_ratio_medians(peer_ratios)
    assert medians["current_ratio"] == 1.5
    assert medians["debt_to_equity"] == 2.0
    assert medians["net_margin"] == 0.08


def test_compare_company_to_peer() -> None:
    company = {
        "current_ratio": {"value": 2.0, "quality": "ok"},
        "debt_to_equity": {"value": 1.0, "quality": "ok"},
        "net_margin": {"value": 0.12, "quality": "ok"},
        "roa": {"value": 0.05, "quality": "ok"},
        "roe": {"value": 0.2, "quality": "ok"},
        "operating_margin": {"value": 0.18, "quality": "ok"},
        "interest_coverage": {"value": 8.0, "quality": "ok"},
    }
    peer = {
        "current_ratio": 1.5,
        "debt_to_equity": 2.0,
        "net_margin": 0.08,
        "roa": 0.04,
        "roe": 0.1,
        "operating_margin": 0.11,
        "interest_coverage": 5.0,
    }
    comparison = compare_company_to_peer(company, peer)
    assert comparison["current_ratio"]["delta_vs_peer"] == 0.5
    assert comparison["debt_to_equity"]["delta_vs_peer"] == -1.0
