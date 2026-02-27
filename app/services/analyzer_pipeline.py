from typing import Dict

from app.services.filing_parser import extract_sections, filing_to_text
from app.services.ratio_engine import compute_ratios
from app.services.summary_engine import build_investment_summary
from app.services.xbrl_mapper import extract_latest_financials


def run_deterministic_analysis(sec_client, ticker: str, preferred_form: str = "10-K") -> Dict:
    identity = sec_client.ticker_to_identity(ticker)
    if not identity:
        raise ValueError(f"Ticker not found: {ticker}")

    filing = sec_client.get_latest_filing(identity.cik_10, preferred_form=preferred_form)
    if not filing:
        raise ValueError("No filing metadata found")

    raw_filing = sec_client.get_filing_text(filing.filing_url)
    filing_text = filing_to_text(raw_filing)
    sections = extract_sections(filing_text, filing.form)

    company_facts = sec_client.get_company_facts(identity.cik_10)
    financials = extract_latest_financials(company_facts)
    ratios = compute_ratios(financials)

    summary = build_investment_summary(
        company_name=identity.company_name or identity.ticker,
        ticker=identity.ticker,
        filing_form=filing.form,
        ratios=ratios,
        insights=None,
        peer_comparison=None,
    )

    return {
        "identity": identity,
        "filing": filing,
        "sections": sections,
        "financials": financials,
        "ratios": ratios,
        "summary": summary,
    }
