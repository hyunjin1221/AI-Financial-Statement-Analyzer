from datetime import date

from app.models.schemas import CompanyIdentity, FilingMetadata
from app.services.analyzer_pipeline import run_deterministic_analysis


class FakeSECClient:
    def ticker_to_identity(self, ticker: str):
        if ticker != "FAKE":
            return None
        return CompanyIdentity(ticker="FAKE", cik_10="0000000001", cik_int=1, company_name="Fake Corp")

    def get_latest_filing(self, cik_10: str, preferred_form: str = "10-K"):
        return FilingMetadata(
            form="10-K",
            filing_date=date(2025, 1, 31),
            accession_number="0000000001-25-000001",
            primary_document="fake10k.htm",
            cik_10=cik_10,
            cik_int=1,
            filing_url="https://example.com/fake10k.htm",
        )

    def get_filing_text(self, filing_url: str) -> str:
        return """
        <html><body>
        Item 1 Business Core business detail.
        Item 1A Risk Factors Debt covenants may restrict flexibility.
        Item 7 Management's Discussion and Analysis Revenue increased this year.
        Item 8 Financial Statements
        </body></html>
        """

    def get_company_facts(self, cik_10: str):
        return {
            "facts": {
                "us-gaap": {
                    "Revenues": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 1000}]}},
                    "NetIncomeLoss": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 120}]}},
                    "Assets": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 2000}]}},
                    "Liabilities": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 900}]}},
                    "StockholdersEquity": {
                        "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 1100}]}
                    },
                    "AssetsCurrent": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 700}]}},
                    "LiabilitiesCurrent": {
                        "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 400}]}
                    },
                    "OperatingIncomeLoss": {
                        "units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 180}]}
                    },
                    "InterestExpense": {"units": {"USD": [{"end": "2024-12-31", "filed": "2025-01-31", "val": 30}]}},
                }
            }
        }


def test_run_deterministic_analysis_end_to_end_with_fake_client() -> None:
    result = run_deterministic_analysis(FakeSECClient(), ticker="FAKE", preferred_form="10-K")

    assert result["identity"].ticker == "FAKE"
    assert result["filing"].form == "10-K"
    assert "mda" in result["sections"]
    assert result["ratios"]["net_margin"]["quality"] == "ok"
    assert "not investment advice" in result["summary"]
