from typing import Dict, Optional


def _fmt_pct(value: Optional[float]) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value * 100:.2f}%"


def _fmt_num(value: Optional[float]) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:.2f}"


def build_investment_summary(
    company_name: str,
    ticker: str,
    filing_form: str,
    ratios: Dict[str, Dict],
    insights: Optional[Dict] = None,
    peer_comparison: Optional[Dict[str, Dict]] = None,
) -> str:
    lines = [
        f"{company_name} ({ticker}) analysis based on latest {filing_form}.",
        "This output is for research/education and not investment advice.",
    ]

    net_margin = ratios.get("net_margin", {}).get("value")
    debt_to_equity = ratios.get("debt_to_equity", {}).get("value")
    current_ratio = ratios.get("current_ratio", {}).get("value")
    lines.append(
        "Ratio snapshot: "
        f"Net margin {_fmt_pct(net_margin)}, "
        f"Debt-to-equity {_fmt_num(debt_to_equity)}, "
        f"Current ratio {_fmt_num(current_ratio)}."
    )

    if peer_comparison:
        op_margin_cmp = peer_comparison.get("operating_margin", {})
        delta = op_margin_cmp.get("delta_vs_peer")
        if isinstance(delta, (int, float)):
            direction = "above" if delta >= 0 else "below"
            lines.append(f"Operating margin is {abs(delta):.2f} {direction} peer median.")
        else:
            lines.append("Peer comparison is limited due to sparse peer data.")

    if insights:
        red_flags = insights.get("red_flags", [])[:2]
        revenue_trends = insights.get("revenue_trends", [])[:2]
        if revenue_trends:
            lines.append("Revenue trends: " + "; ".join(revenue_trends))
        if red_flags:
            lines.append("Potential red flags: " + "; ".join(red_flags))

    return "\n".join(lines)


def build_markdown_report(
    company_name: str,
    ticker: str,
    filing: Dict,
    ratios: Dict[str, Dict],
    insights: Optional[Dict] = None,
    peer_comparison: Optional[Dict[str, Dict]] = None,
    summary_text: str = "",
) -> str:
    lines = [
        f"# Financial Statement Analysis Report: {company_name} ({ticker})",
        "",
        "## Filing Metadata",
        f"- Form: {filing.get('form', 'n/a')}",
        f"- Filing Date: {filing.get('filing_date', 'n/a')}",
        f"- Accession Number: {filing.get('accession_number', 'n/a')}",
        f"- Filing URL: {filing.get('filing_url', 'n/a')}",
        "",
        "## Ratio Snapshot",
    ]
    for ratio_name, payload in ratios.items():
        lines.append(
            f"- {ratio_name}: value={payload.get('value', 'n/a')} | quality={payload.get('quality', 'n/a')}"
        )

    if peer_comparison:
        lines.extend(["", "## Peer Comparison"])
        for ratio_name, payload in peer_comparison.items():
            lines.append(
                "- "
                f"{ratio_name}: company={payload.get('company_value', 'n/a')} | "
                f"peer_median={payload.get('peer_median', 'n/a')} | "
                f"delta={payload.get('delta_vs_peer', 'n/a')}"
            )

    if insights:
        lines.extend(["", "## AI Insights"])
        for key in [
            "revenue_trends",
            "debt_risk_signals",
            "risk_factor_highlights",
            "red_flags",
            "management_commentary",
            "evidence_quotes",
        ]:
            values = insights.get(key, [])
            lines.append(f"### {key}")
            if not values:
                lines.append("- n/a")
            else:
                for value in values:
                    lines.append(f"- {value}")
        lines.append(f"- confidence: {insights.get('confidence', 'n/a')}")

    lines.extend(["", "## Investment Summary", summary_text or "n/a", ""])
    lines.append("Disclaimer: This report is for educational/research use and is not investment advice.")
    return "\n".join(lines)
