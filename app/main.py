import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure `app.*` imports resolve when Streamlit executes this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.filing_parser import extract_sections_with_spans, filing_to_text
from app.services.llm_engine import FilingInsightEngine
from app.services.peer_engine import PeerBenchmarkEngine, compare_company_to_peer
from app.services.ratio_engine import compute_ratios
from app.services.report_store import list_recent_reports, save_markdown_report
from app.services.sec_client import SECClient
from app.services.summary_engine import build_investment_summary, build_markdown_report
from app.services.xbrl_mapper import extract_latest_financials
from app.utils.caching import (
    get_company_facts_cached,
    get_filing_text_cached,
    get_identity_cached,
    get_latest_filing_cached,
    get_submissions_cached,
)


st.set_page_config(page_title="AI Financial Statement Analyzer", layout="wide")

st.title("AI Financial Statement Analyzer")
st.caption("Free-only build: SEC EDGAR + local LLM (Ollama) + Streamlit")

with st.sidebar:
    st.header("Input")
    ticker = st.text_input("Ticker", value="AAPL").strip().upper()
    preferred_form = st.selectbox("Preferred filing", options=["10-K", "10-Q"])
    run_ai = st.checkbox("Run local AI extraction (Ollama)", value=True)
    run_peer = st.checkbox("Run peer benchmark (slower)", value=False)
    save_report = st.checkbox("Save report to local history", value=False)
    run = st.button("Fetch latest filing")

st.markdown("---")

if run:
    client = SECClient()
    with st.spinner("Fetching SEC data..."):
        identity = get_identity_cached(ticker)
        if not identity:
            st.error(f"Ticker '{ticker}' not found in SEC mapping.")
            st.stop()

        filing = get_latest_filing_cached(identity.cik_10, preferred_form=preferred_form)

    st.subheader("Company")
    st.write(
        {
            "ticker": identity.ticker,
            "company_name": identity.company_name,
            "cik_10": identity.cik_10,
            "cik_int": identity.cik_int,
        }
    )

    st.subheader("Latest Filing Metadata")
    if not filing:
        st.warning("No recent 10-K/10-Q filing metadata found.")
    else:
        st.write(filing.model_dump())
        st.markdown(f"[Open filing document]({filing.filing_url})")

        with st.spinner("Downloading filing text and extracting sections..."):
            raw_filing = get_filing_text_cached(filing.filing_url)
            filing_text = filing_to_text(raw_filing)
            section_records = extract_sections_with_spans(filing_text, filing.form)

        with st.spinner("Loading company facts and computing ratios..."):
            company_facts = get_company_facts_cached(identity.cik_10)
            financials = extract_latest_financials(company_facts)
            ratios = compute_ratios(financials)

        st.subheader("Section Extraction (Sprint 1)")
        if not section_records:
            st.warning("No target sections detected yet for this filing.")
        else:
            st.success(f"Extracted {len(section_records)} sections.")
            for section_name, section_payload in section_records.items():
                with st.expander(f"{section_name}"):
                    st.caption(
                        f"Source span: start={section_payload.get('start')} end={section_payload.get('end')}"
                    )
                    st.write(section_payload.get("text", "")[:5000])

        st.subheader("Financial Ratios (Sprint 2)")
        st.caption("Computed from latest SEC companyfacts values (free EDGAR XBRL data).")
        ratio_rows = []
        for ratio_name, payload in ratios.items():
            value = payload.get("value")
            ratio_rows.append(
                {
                    "ratio": ratio_name,
                    "value": float(value) if isinstance(value, (int, float)) else None,
                    "quality": payload.get("quality"),
                }
            )
        ratio_df = pd.DataFrame(ratio_rows)
        st.dataframe(ratio_df, use_container_width=True, hide_index=True)
        ratio_chart_df = ratio_df[ratio_df["value"].notna()]
        if not ratio_chart_df.empty:
            fig = px.bar(ratio_chart_df, x="ratio", y="value", color="quality", title="Company Ratios")
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("Underlying mapped financial values"):
            st.write(financials)

        st.subheader("AI Insights (Sprint 3)")
        insights = None
        if not run_ai:
            st.info("Enable 'Run local AI extraction (Ollama)' from the sidebar to generate narrative insights.")
        elif not section_records:
            st.warning("AI extraction skipped because no filing sections were detected.")
        else:
            try:
                with st.spinner("Running local AI extraction with Ollama..."):
                    insight_engine = FilingInsightEngine()
                    insights = insight_engine.extract_from_section_records(
                        form_type=filing.form,
                        section_records=section_records,
                    )
                st.write(insights)
            except Exception as exc:  # noqa: BLE001
                st.warning(
                    "Local AI extraction failed. Check Ollama is running and your model is available. "
                    f"Details: {exc}"
                )

        st.subheader("Peer Benchmark (Sprint 4)")
        peer_comparison = None
        if not run_peer:
            st.info("Enable 'Run peer benchmark (slower)' from the sidebar to compare against SIC peers.")
        else:
            with st.spinner("Building peer benchmark from SEC data..."):
                submissions = get_submissions_cached(identity.cik_10)
                target_sic = str(submissions.get("sic", ""))

                if not target_sic:
                    st.warning("SIC not found for this company; peer benchmark skipped.")
                else:
                    peer_engine = PeerBenchmarkEngine(client)
                    peers = peer_engine.find_same_sic_peers(
                        target_sic=target_sic,
                        target_cik_int=identity.cik_int,
                        max_peers=8,
                        max_scan=100,
                    )
                    benchmark = peer_engine.build_peer_benchmark(peers)
                    peer_comparison = compare_company_to_peer(ratios, benchmark["peer_medians"])
                    st.write({"target_sic": target_sic, "peer_count_found": len(peers), "peer_count_used": benchmark["peer_count_used"]})
                    peer_rows = []
                    for ratio_name, payload in peer_comparison.items():
                        peer_rows.append(
                            {
                                "ratio": ratio_name,
                                "company_value": payload.get("company_value"),
                                "peer_median": payload.get("peer_median"),
                                "delta_vs_peer": payload.get("delta_vs_peer"),
                                "quality": payload.get("company_quality"),
                            }
                        )
                    peer_df = pd.DataFrame(peer_rows)
                    st.dataframe(peer_df, use_container_width=True, hide_index=True)
                    peer_chart_df = peer_df[peer_df["delta_vs_peer"].notna()]
                    if not peer_chart_df.empty:
                        fig_peer = px.bar(
                            peer_chart_df,
                            x="ratio",
                            y="delta_vs_peer",
                            color="quality",
                            title="Ratio Delta vs Peer Median",
                        )
                        st.plotly_chart(fig_peer, use_container_width=True)

        st.subheader("Investment Summary (Sprint 4)")
        summary_text = build_investment_summary(
            company_name=identity.company_name or identity.ticker,
            ticker=identity.ticker,
            filing_form=filing.form,
            ratios=ratios,
            insights=insights,
            peer_comparison=peer_comparison,
        )
        st.text(summary_text)

        report_md = build_markdown_report(
            company_name=identity.company_name or identity.ticker,
            ticker=identity.ticker,
            filing=filing.model_dump(),
            ratios=ratios,
            insights=insights,
            peer_comparison=peer_comparison,
            summary_text=summary_text,
        )
        st.download_button(
            "Download Markdown Report",
            data=report_md,
            file_name=f"{identity.ticker}_{filing.form}_analysis_report.md",
            mime="text/markdown",
        )
        if save_report:
            saved_path = save_markdown_report(report_md, identity.ticker, filing.form)
            st.success(f"Saved report: {saved_path}")
        with st.expander("Recent saved reports"):
            for report_path in list_recent_reports(limit=8):
                st.write(str(report_path))

else:
    st.info("Enter a ticker and click 'Fetch latest filing' to begin.")
