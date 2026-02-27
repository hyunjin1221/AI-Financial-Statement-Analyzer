from app.services.summary_engine import build_investment_summary, build_markdown_report


def test_build_investment_summary_contains_key_sections() -> None:
    ratios = {
        "net_margin": {"value": 0.14, "quality": "ok"},
        "debt_to_equity": {"value": 1.2, "quality": "ok"},
        "current_ratio": {"value": 1.8, "quality": "ok"},
    }
    insights = {
        "revenue_trends": ["Revenue growth in subscription segment"],
        "red_flags": ["High customer concentration"],
    }
    peer_cmp = {
        "operating_margin": {
            "delta_vs_peer": 0.03,
        }
    }

    summary = build_investment_summary(
        company_name="Example Corp",
        ticker="EXM",
        filing_form="10-K",
        ratios=ratios,
        insights=insights,
        peer_comparison=peer_cmp,
    )

    assert "Example Corp (EXM)" in summary
    assert "Ratio snapshot" in summary
    assert "Operating margin" in summary
    assert "Revenue trends" in summary
    assert "Potential red flags" in summary


def test_build_markdown_report() -> None:
    report = build_markdown_report(
        company_name="Example Corp",
        ticker="EXM",
        filing={
            "form": "10-K",
            "filing_date": "2025-01-31",
            "accession_number": "0000000000-25-000001",
            "filing_url": "https://example.com/filing",
        },
        ratios={"net_margin": {"value": 0.15, "quality": "ok"}},
        insights={"red_flags": ["Example red flag"], "confidence": 0.7},
        peer_comparison={
            "net_margin": {
                "company_value": 0.15,
                "peer_median": 0.12,
                "delta_vs_peer": 0.03,
            }
        },
        summary_text="Test summary body.",
    )
    assert "# Financial Statement Analysis Report: Example Corp (EXM)" in report
    assert "## Filing Metadata" in report
    assert "## Ratio Snapshot" in report
    assert "## Peer Comparison" in report
    assert "## AI Insights" in report
    assert "## Investment Summary" in report
