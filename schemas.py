from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


# ── Domain models ────────────────────────────────────────────────────────────

class NOADetails(BaseModel):
    year: int = Field(0, description="Year of assessment. Use 0 if not available.")
    employment_income: float = Field(0, description="Employment income for the year.")
    tax_payable: float = Field(0, description="Tax payable for the year.")
    currency: str = Field("SGD", description="ISO 4217 currency code.")

class NOAData(BaseModel):
    noa_data: Optional[List[NOADetails]] = Field(default_factory=list)

class PaySlipDetails(BaseModel):
    payment_year: Optional[int] = Field(None, description="Payment year.")
    payment_month: str = Field("", description="Payment month name.")
    net_pay: Optional[float] = Field(None, description="Net pay received.")
    currency: str = Field("", description="ISO 4217 currency code.")

class PaySlipData(BaseModel):
    payslip: List[PaySlipDetails] = Field(default_factory=list)

class SummaryData(BaseModel):
    total_source_of_wealth_coming_from_all_the_employment: Optional[float] = Field(None)
    total_sow_generated_from_client_business: Optional[float] = Field(None)
    total_gain_of_the_property: Optional[float] = Field(None)

class OtherDocData(BaseModel):
    notes: Optional[str] = Field(None, description="Optional notes for other document types")

DOCUMENT_REGISTRY: Dict[str, type] = {
    "noa":     NOAData,
    "payslip": PaySlipData,
    "summary": SummaryData,
    "income_tax": NOAData,
    "tax_returns_biz": NOAData,
    "payslips": PaySlipData,
    "employment_letter": OtherDocData,
    "bank_statements": OtherDocData,
    "cpf_statement": OtherDocData,
    "bonus_letter": OtherDocData,
    "identification": OtherDocData,
    "biz_reg": OtherDocData,
    "ownership_structure": OtherDocData,
    "biz_financials": OtherDocData,
    "bank_statements_biz": OtherDocData,
    "personal_bank_statements": OtherDocData,
    "dividend_record": OtherDocData,
    "director_fee": OtherDocData,
    "biz_contracts": OtherDocData,
    "asset_documents": OtherDocData,
    "ubo_declaration": OtherDocData,
    "identification_biz": OtherDocData,
}

# ── API request/response schemas ─────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    session_id: Optional[uuid.UUID] = Field(None, description="Provide to add to existing session, or omit to create new.")
    doc_types: List[str] = Field(..., description="Document types to extract.")

class UpdateDocRequest(BaseModel):
    verified_data: Dict[str, Any] = Field(..., description="User-curated data payload.")
    status: str = Field("reviewing", description="New status: reviewing | verified")

class DocumentSessionOut(BaseModel):
    id: int
    session_id: uuid.UUID
    subsession_id: uuid.UUID
    doc_type: str
    status: str
    extracted_data: Dict[str, Any]
    verified_data: Optional[Dict[str, Any]]
    diff_summary: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionSummaryOut(BaseModel):
    session_id: uuid.UUID
    doc_types: List[str]
    total_records: int
    verified_count: int
    latest_updated: Optional[datetime]

class SummarizeResponse(BaseModel):
    record_id: int
    doc_type: str
    summary: str
    key_figures: Dict[str, Any]
