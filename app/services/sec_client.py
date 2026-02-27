import time
from typing import Dict, List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.schemas import CompanyIdentity, FilingMetadata
from app.utils.logging import get_logger


logger = get_logger()


class RateLimiter:
    """Simple per-process limiter to respect SEC fair access usage."""

    def __init__(self, max_per_second: float) -> None:
        self.min_interval = 1.0 / max_per_second if max_per_second > 0 else 0.2
        self._last_called = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_called
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_called = time.monotonic()


class SECClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.sec_user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )
        self.timeout = settings.sec_timeout_seconds
        self.rate_limiter = RateLimiter(settings.sec_rate_limit_per_sec)

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
    )
    def _get_json(self, url: str) -> Dict:
        self.rate_limiter.wait()
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
    )
    def _get_text(self, url: str) -> str:
        self.rate_limiter.wait()
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _normalize_cik(cik: int) -> str:
        return f"{int(cik):010d}"

    @staticmethod
    def _build_archive_filing_url(cik_int: int, accession_number: str, primary_doc: str) -> str:
        accession_no_dash = accession_number.replace("-", "")
        return (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik_int)}/"
            f"{accession_no_dash}/{primary_doc}"
        )

    def get_ticker_mapping(self) -> List[Dict]:
        data = self._get_json("https://www.sec.gov/files/company_tickers.json")
        # SEC returns numeric-string keys; values are mapping records.
        return list(data.values())

    def ticker_to_identity(self, ticker: str) -> Optional[CompanyIdentity]:
        ticker_upper = ticker.upper().strip()
        for row in self.get_ticker_mapping():
            if str(row.get("ticker", "")).upper() == ticker_upper:
                cik_int = int(row["cik_str"])
                return CompanyIdentity(
                    ticker=ticker_upper,
                    cik_10=self._normalize_cik(cik_int),
                    cik_int=cik_int,
                    company_name=row.get("title"),
                )
        return None

    def get_submissions(self, cik_10: str) -> Dict:
        return self._get_json(f"https://data.sec.gov/submissions/CIK{cik_10}.json")

    def get_company_facts(self, cik_10: str) -> Dict:
        return self._get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_10}.json")

    def get_latest_filing(self, cik_10: str, preferred_form: str = "10-K") -> Optional[FilingMetadata]:
        submissions = self.get_submissions(cik_10)
        recent = submissions.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])

        if not forms:
            return None

        target_forms = [preferred_form, "10-Q" if preferred_form == "10-K" else "10-K"]

        for target_form in target_forms:
            for idx, form in enumerate(forms):
                if form != target_form:
                    continue

                cik_int = int(cik_10)
                accession_number = accession_numbers[idx]
                primary_doc = primary_documents[idx]
                filing_url = self._build_archive_filing_url(cik_int, accession_number, primary_doc)

                return FilingMetadata(
                    form=form,
                    filing_date=filing_dates[idx],
                    accession_number=accession_number,
                    primary_document=primary_doc,
                    cik_10=cik_10,
                    cik_int=cik_int,
                    filing_url=filing_url,
                )

        return None

    def get_filing_text(self, filing_url: str) -> str:
        return self._get_text(filing_url)
