import streamlit as st

from app.services.sec_client import SECClient


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_identity_cached(ticker: str):
    client = SECClient()
    return client.ticker_to_identity(ticker)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_latest_filing_cached(cik_10: str, preferred_form: str):
    client = SECClient()
    return client.get_latest_filing(cik_10, preferred_form=preferred_form)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_filing_text_cached(filing_url: str) -> str:
    client = SECClient()
    return client.get_filing_text(filing_url)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_company_facts_cached(cik_10: str):
    client = SECClient()
    return client.get_company_facts(cik_10)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_submissions_cached(cik_10: str):
    client = SECClient()
    return client.get_submissions(cik_10)
