from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FilingMetadata(BaseModel):
    form: str
    filing_date: date
    accession_number: str
    primary_document: str
    cik_10: str = Field(description="CIK as 10-digit zero-padded string")
    cik_int: int = Field(description="CIK integer, used in EDGAR archive paths")
    filing_url: str


class CompanyIdentity(BaseModel):
    ticker: str
    cik_10: str
    cik_int: int
    company_name: Optional[str] = None
