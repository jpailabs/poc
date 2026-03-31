"""
Financial Document Extraction API v1.2

Key design decisions:
- Document sections are open-ended: NOA, Payslip, Summary are built-in,
  but new document types can be added by registering a new Pydantic model.
- On POST /documents/update the user MUST submit ALL sections that were
  originally extracted. Omitting any extracted section is rejected with HTTP 422.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Type

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class NOADetails(BaseModel):
    year: int = Field(0, description="Year of assessment. Use 0 if not available.")
    employment_income: float = Field(0, description="Employment income for the year. Use 0 if not available.")
    tax_payable: float = Field(0, description="Tax payable for the year. Use 0 if not available.")
    currency: str = Field("SGD", description="ISO 4217 currency code. Default SGD.")


class NOAData(BaseModel):
    noa_data: Optional[List[NOADetails]] = Field(
        default_factory=lambda: [NOADetails()],
        description="List of NOA entries.",
    )


class PaySlipDetails(BaseModel):
    payment_year: Optional[int] = Field(None, description="Payment year. None if unknown.")
    payment_month: str = Field("", description="Payment month. Empty string if unknown.")
    net_pay: Optional[float] = Field(None, description="Net pay. None if unknown.")
    currency: str = Field("", description="ISO 4217 currency code. Empty string if unknown.")


class PaySlipData(BaseModel):
    payslip: List[PaySlipDetails] = Field(..., description="List of payslip entries.")


class SummaryData(BaseModel):
    total_source_of_wealth_coming_from_all_the_employment: Optional[float] = Field(
        None, description="Total source of wealth from all employment.")
    total_sow_generated_from_client_business: Optional[float] = Field(
        None, description="Total source of wealth from client business.")
    total_gain_of_the_property: Optional[float] = Field(
        None, description="Total gain from property.")


# ---------------------------------------------------------------------------
# Document registry — add new document types here without touching any
# other code. Each entry: key → (Pydantic model class, human label)
# ---------------------------------------------------------------------------

DOCUMENT_REGISTRY: Dict[str, tuple[Type[BaseModel], str]] = {
    "noa":     (NOAData,      "Notice of Assessment"),
    "payslip": (PaySlipData,  "Payslip"),
    "summary": (SummaryData,  "Source of Wealth Summary"),
    # Future additions:
    # "bank_statement": (BankStatementData, "Bank Statement"),
    # "cpf":            (CPFData,           "CPF Statement"),
}


# ---------------------------------------------------------------------------
# Generic document container
# ---------------------------------------------------------------------------

class ExtractedDocument(BaseModel):
    """
    Holds extracted data for any combination of document types.
    `sections` is a free-form dict: { document_key: extracted_model_dict }
    Only sections that were actually extracted will be present.
    """
    doc_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique document identifier.",
    )
    sections: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Map of document type key → extracted data. "
            "Only populated sections are included. "
            "Keys match DOCUMENT_REGISTRY (e.g. 'noa', 'payslip', 'summary')."
        ),
    )

    @property
    def available_sections(self) -> List[str]:
        return list(self.sections.keys())


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ExtractionRequest(BaseModel):
    """
    Declare which document types the user has uploaded.
    `document_keys` must be valid keys from the document registry.
    """
    document_keys: List[str] = Field(
        ...,
        description=(
            "List of document type keys to extract. "
            f"Known types: {list(DOCUMENT_REGISTRY.keys())}. "
            "Must contain at least one entry."
        ),
    )
    raw_text: Optional[str] = Field(
        None,
        description="Raw document text (passed to real extraction logic in production).",
    )

    @model_validator(mode="after")
    def validate_keys(self) -> "ExtractionRequest":
        if not self.document_keys:
            raise ValueError("document_keys must contain at least one entry.")
        unknown = [k for k in self.document_keys if k not in DOCUMENT_REGISTRY]
        if unknown:
            raise ValueError(
                f"Unknown document type(s): {unknown}. "
                f"Registered types: {list(DOCUMENT_REGISTRY.keys())}"
            )
        return self


class UpdateRequest(BaseModel):
    """
    User submits the full document back after CRUD.
    ALL sections that were originally extracted MUST be present.
    Submitting fewer sections than were extracted will be rejected.
    """
    doc_id: str = Field(..., description="ID of the document being updated.")
    sections: Dict[str, Any] = Field(
        ...,
        description=(
            "Updated section data. Must include every section that was originally extracted. "
            "Each value will be validated against the registered Pydantic model for that key."
        ),
    )


class DocumentMetadata(BaseModel):
    doc_id: str
    available_sections: List[str]


class SchemaResponse(BaseModel):
    """
    Exposes JSON Schema for every registered document type.
    The UI uses this to render forms, labels, tooltips, and client-side validation.
    """
    registered_types: List[str] = Field(description="All known document type keys.")
    models: Dict[str, Any] = Field(description="key → JSON Schema for that model.")


# ---------------------------------------------------------------------------
# In-memory store  (swap for DB in production)
# ---------------------------------------------------------------------------

_store: Dict[str, ExtractedDocument] = {}


# ---------------------------------------------------------------------------
# Mock extraction helpers  (replace with real OCR / LLM calls)
# ---------------------------------------------------------------------------

def _mock_extract_noa() -> Dict[str, Any]:
    return NOAData(noa_data=[
        NOADetails(year=2023, employment_income=85_000.0, tax_payable=5_200.0, currency="SGD"),
        NOADetails(year=2022, employment_income=78_000.0, tax_payable=4_650.0, currency="SGD"),
    ]).model_dump()


def _mock_extract_payslip() -> Dict[str, Any]:
    return PaySlipData(payslip=[
        PaySlipDetails(payment_year=2024, payment_month="January",  net_pay=6_200.50, currency="SGD"),
        PaySlipDetails(payment_year=2024, payment_month="February", net_pay=6_200.50, currency="SGD"),
        PaySlipDetails(payment_year=2024, payment_month="March",    net_pay=6_350.00, currency="SGD"),
    ]).model_dump()


def _mock_extract_summary() -> Dict[str, Any]:
    return SummaryData(
        total_source_of_wealth_coming_from_all_the_employment=163_000.0,
        total_sow_generated_from_client_business=12_000.0,
        total_gain_of_the_property=45_000.0,
    ).model_dump()


# Generic fallback for any future registered type without a bespoke mock
def _mock_extract_generic(key: str) -> Dict[str, Any]:
    model_cls, _ = DOCUMENT_REGISTRY[key]
    return model_cls().model_dump()


_MOCK_EXTRACTORS: Dict[str, Any] = {
    "noa":     _mock_extract_noa,
    "payslip": _mock_extract_payslip,
    "summary": _mock_extract_summary,
}


def _mock_extract(request: ExtractionRequest) -> ExtractedDocument:
    sections: Dict[str, Any] = {}
    for key in request.document_keys:
        extractor = _MOCK_EXTRACTORS.get(key, lambda: _mock_extract_generic(key))
        sections[key] = extractor()
    return ExtractedDocument(sections=sections)


# ---------------------------------------------------------------------------
# Validation helper — deserialise + re-validate each section payload
# ---------------------------------------------------------------------------

def _validate_sections(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates each section dict against its registered Pydantic model.
    Raises HTTPException 422 with field-level detail on failure.
    Raises HTTPException 400 for unknown document type keys.
    Returns the validated, serialised sections dict.
    """
    validated: Dict[str, Any] = {}
    errors: Dict[str, Any] = {}

    for key, data in sections.items():
        if key not in DOCUMENT_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown document type '{key}'. Registered: {list(DOCUMENT_REGISTRY.keys())}",
            )
        model_cls, _ = DOCUMENT_REGISTRY[key]
        try:
            validated[key] = model_cls.model_validate(data).model_dump()
        except Exception as exc:
            errors[key] = str(exc)

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Section validation failed.", "errors": errors},
        )

    return validated


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Financial Document Extraction API",
    description=(
        "Extracts structured financial data from any combination of uploaded documents. "
        "Document types are open-ended — not limited to NOA, Payslip, and Summary."
    ),
    version="1.2.0",
)


# ── 1. Extract ──────────────────────────────────────────────────────────────

@app.post(
    "/extract",
    response_model=ExtractedDocument,
    summary="Extract data from one or more document types",
    tags=["Extraction"],
)
def extract_document(request: ExtractionRequest) -> ExtractedDocument:
    """
    Pass the list of document keys you have. Only those sections will be extracted.

    **Example — user only has payslips:**
    ```json
    { "document_keys": ["payslip"] }
    ```
    **Example — user has NOA and summary:**
    ```json
    { "document_keys": ["noa", "summary"] }
    ```
    """
    extracted = _mock_extract(request)
    _store[extracted.doc_id] = extracted
    return extracted


# ── 2. Schema ───────────────────────────────────────────────────────────────

@app.get(
    "/schema",
    response_model=SchemaResponse,
    summary="Get JSON Schema for all registered document models",
    tags=["Schema"],
)
def get_schema() -> SchemaResponse:
    """
    Returns JSON Schema for every registered document type.

    UI usage:
    - `registered_types` → which document type keys are valid
    - `models[key]` → field types, descriptions, and constraints for rendering forms
    """
    return SchemaResponse(
        registered_types=list(DOCUMENT_REGISTRY.keys()),
        models={
            key: model_cls.model_json_schema()
            for key, (model_cls, _) in DOCUMENT_REGISTRY.items()
        },
    )


# ── 3. List documents ────────────────────────────────────────────────────────

@app.get(
    "/documents",
    response_model=List[DocumentMetadata],
    summary="List all stored documents",
    tags=["Documents"],
)
def list_documents() -> List[DocumentMetadata]:
    return [
        DocumentMetadata(doc_id=doc_id, available_sections=doc.available_sections)
        for doc_id, doc in _store.items()
    ]


# ── 4. Retrieve ──────────────────────────────────────────────────────────────

@app.get(
    "/documents/{doc_id}",
    response_model=ExtractedDocument,
    summary="Retrieve a stored document",
    tags=["Documents"],
)
def get_document(doc_id: str) -> ExtractedDocument:
    doc = _store.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return doc


# ── 5. Update ────────────────────────────────────────────────────────────────

@app.post(
    "/documents/update",
    response_model=ExtractedDocument,
    summary="Submit full updated document (all extracted sections required)",
    tags=["Documents"],
)
def update_document(request: UpdateRequest) -> ExtractedDocument:
    """
    The user must submit **all** sections that were originally extracted.
    Submitting a partial set is rejected — this prevents accidental data loss.

    Validation flow:
    1. Check all originally-extracted sections are present in the payload → HTTP 400 if missing
    2. Check no extra unknown sections are included → HTTP 400
    3. Validate every section payload against its Pydantic model → HTTP 422 with field errors
    4. Persist and return the updated document
    """
    doc = _store.get(request.doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.doc_id}' not found. Call /extract first.",
        )

    # Rule 1: All originally extracted sections must be re-submitted
    missing = [s for s in doc.available_sections if s not in request.sections]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Update rejected: missing sections that were originally extracted.",
                "missing_sections": missing,
                "required_sections": doc.available_sections,
                "hint": "Submit all extracted sections together, even if unchanged.",
            },
        )

    # Rule 2: No unknown extra sections
    extra = [s for s in request.sections if s not in DOCUMENT_REGISTRY]
    if extra:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown document type(s) in update: {extra}.",
        )

    # Rule 3: Validate each section against its Pydantic model
    validated_sections = _validate_sections(request.sections)

    # Persist
    updated_doc = doc.model_copy(update={"sections": validated_sections})
    _store[request.doc_id] = updated_doc
    return updated_doc


# ── 6. Delete ────────────────────────────────────────────────────────────────

@app.delete(
    "/documents/{doc_id}",
    summary="Delete a stored document",
    tags=["Documents"],
)
def delete_document(doc_id: str) -> JSONResponse:
    if doc_id not in _store:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    del _store[doc_id]
    return JSONResponse(content={"detail": f"Document '{doc_id}' deleted."})


# ---------------------------------------------------------------------------
# Run:  uvicorn main:app --reload
# Docs: http://127.0.0.1:8000/docs
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)