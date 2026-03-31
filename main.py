"""
FinDoc Extraction API  — FastAPI + PostgreSQL

Endpoints:
  POST   /sessions/extract            Extract docs → new session (accepts multipart form + PDF upload)
  GET    /sessions                    List all sessions (summary)
  GET    /sessions/{session_id}       All records for a session
  GET    /sessions/{session_id}/history  Subsession edit history for a session
  GET    /records/{id}                Get single record
  PUT    /records/{id}                Update (CRUD) a record — saves verified_data + diff
  DELETE /records/{id}                Delete a record
  POST   /records/{id}/summarize      LLM summarization of verified/extracted data
  GET    /schema                      JSON Schema for all models
  POST   /seed                        Re-seed sample data (dev utility)
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_db, DocumentSession
from schemas import (
    CreateSessionRequest, UpdateDocRequest,
    DocumentSessionOut, SessionSummaryOut,
    SummarizeResponse,
    DOCUMENT_REGISTRY,
    NOAData, PaySlipData, SummaryData,
)


# ── Startup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="FinDoc API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    # Auto-seed on first run
    from seed import seed
    seed()


# ── Mock extraction ───────────────────────────────────────────────────────────

def _mock_extract(doc_type: str) -> Dict[str, Any]:
    if doc_type == "noa":
        return NOAData(noa_data=[
            {"year": 2023, "employment_income": 85000.0, "tax_payable": 5200.0, "currency": "SGD"},
            {"year": 2022, "employment_income": 78000.0, "tax_payable": 4650.0, "currency": "SGD"},
        ]).model_dump()
    elif doc_type == "payslip":
        return PaySlipData(payslip=[
            {"payment_year": 2024, "payment_month": "January",  "net_pay": 6200.50, "currency": "SGD"},
            {"payment_year": 2024, "payment_month": "February", "net_pay": 6200.50, "currency": "SGD"},
            {"payment_year": 2024, "payment_month": "March",    "net_pay": 6350.00, "currency": "SGD"},
        ]).model_dump()
    elif doc_type == "summary":
        return SummaryData(
            total_source_of_wealth_coming_from_all_the_employment=163000.0,
            total_sow_generated_from_client_business=12000.0,
            total_gain_of_the_property=45000.0,
        ).model_dump()
    else:
        model_cls = DOCUMENT_REGISTRY.get(doc_type)
        return model_cls().model_dump() if model_cls else {}


def _compute_diff(extracted: Dict, verified: Dict, prefix: str = "") -> List[str]:
    """Recursively find changed leaf fields."""
    changed = []
    all_keys = set(extracted.keys()) | set(verified.keys())
    for k in all_keys:
        full_key = f"{prefix}{k}"
        ev, vv = extracted.get(k), verified.get(k)
        if isinstance(ev, dict) and isinstance(vv, dict):
            changed.extend(_compute_diff(ev, vv, prefix=f"{full_key}."))
        elif isinstance(ev, list) and isinstance(vv, list):
            for i, (ei, vi) in enumerate(zip(ev, vv)):
                if isinstance(ei, dict) and isinstance(vi, dict):
                    changed.extend(_compute_diff(ei, vi, prefix=f"{full_key}[{i}]."))
                elif ei != vi:
                    changed.append(f"{full_key}[{i}]")
        elif ev != vv:
            changed.append(full_key)
    return changed


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/sessions/extract", response_model=List[DocumentSessionOut], tags=["Sessions"])
async def extract(
    doc_types: str = Form(..., description="Comma-separated document types, e.g. 'noa,payslip'"),
    session_id: Optional[str] = Form(None, description="Existing session ID, or omit to create new."),
    file: Optional[UploadFile] = File(None, description="Optional PDF document to upload."),
    db: Session = Depends(get_db),
):
    """
    Run mock extraction for one or more document types.
    Accepts multipart/form-data so a PDF file can be uploaded alongside the request.
    - Omit session_id to create a brand-new session.
    - Supply an existing session_id to add more doc types to it (new subsession).
    """
    doc_type_list = [t.strip() for t in doc_types.split(",") if t.strip()]
    if not doc_type_list:
        raise HTTPException(400, "doc_types must contain at least one entry.")

    unknown = [t for t in doc_type_list if t not in DOCUMENT_REGISTRY]
    if unknown:
        raise HTTPException(400, f"Unknown doc types: {unknown}. Known: {list(DOCUMENT_REGISTRY.keys())}")

    # If a file was uploaded, read its bytes (passed to a real OCR/LLM in production)
    file_bytes: Optional[bytes] = None
    if file:
        file_bytes = await file.read()

    sid = uuid.UUID(session_id) if session_id else uuid.uuid4()
    subsession_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    records = []

    for doc_type in doc_type_list:
        rec = DocumentSession(
            session_id=sid,
            subsession_id=subsession_id,
            doc_type=doc_type,
            status="extracted",
            extracted_data=_mock_extract(doc_type),
            verified_data=None,
            diff_summary=None,
            created_at=now,
            updated_at=now,
        )
        db.add(rec)
        records.append(rec)

    db.commit()
    for r in records:
        db.refresh(r)
    return records


@app.get("/sessions", response_model=List[SessionSummaryOut], tags=["Sessions"])
def list_sessions(db: Session = Depends(get_db)):
    """List all sessions with summary stats."""
    from sqlalchemy import func
    rows = db.query(DocumentSession).all()
    # Group by session_id
    grouped: Dict[uuid.UUID, list] = {}
    for r in rows:
        grouped.setdefault(r.session_id, []).append(r)

    out = []
    for sid, recs in grouped.items():
        out.append(SessionSummaryOut(
            session_id=sid,
            doc_types=list({r.doc_type for r in recs}),
            total_records=len(recs),
            verified_count=sum(1 for r in recs if r.status == "verified"),
            latest_updated=max(r.updated_at for r in recs),
        ))
    out.sort(key=lambda x: x.latest_updated or datetime.min, reverse=True)
    return out


@app.get("/sessions/{session_id}", response_model=List[DocumentSessionOut], tags=["Sessions"])
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """All records for a session (latest subsession per doc_type)."""
    rows = (
        db.query(DocumentSession)
        .filter(DocumentSession.session_id == session_id)
        .order_by(DocumentSession.updated_at.desc())
        .all()
    )
    if not rows:
        raise HTTPException(404, f"Session {session_id} not found.")
    # Return latest record per doc_type
    seen = set()
    result = []
    for r in rows:
        if r.doc_type not in seen:
            seen.add(r.doc_type)
            result.append(r)
    return result


@app.get("/sessions/{session_id}/history", response_model=List[DocumentSessionOut], tags=["Sessions"])
def session_history(session_id: uuid.UUID, doc_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Full subsession edit history for a session, optionally filtered by doc_type."""
    q = db.query(DocumentSession).filter(DocumentSession.session_id == session_id)
    if doc_type:
        q = q.filter(DocumentSession.doc_type == doc_type)
    rows = q.order_by(DocumentSession.updated_at.desc()).all()
    if not rows:
        raise HTTPException(404, "No history found.")
    return rows


@app.get("/records/{record_id}", response_model=DocumentSessionOut, tags=["Records"])
def get_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.query(DocumentSession).filter(DocumentSession.id == record_id).first()
    if not rec:
        raise HTTPException(404, f"Record {record_id} not found.")
    return rec


@app.put("/records/{record_id}", response_model=DocumentSessionOut, tags=["Records"])
def update_record(record_id: int, body: UpdateDocRequest, db: Session = Depends(get_db)):
    """
    CRUD update: saves verified_data, computes diff vs extracted_data,
    creates a new subsession row to preserve full edit history.
    """
    rec = db.query(DocumentSession).filter(DocumentSession.id == record_id).first()
    if not rec:
        raise HTTPException(404, f"Record {record_id} not found.")

    # Validate against Pydantic model
    model_cls = DOCUMENT_REGISTRY.get(rec.doc_type)
    if model_cls:
        try:
            model_cls.model_validate(body.verified_data)
        except Exception as e:
            raise HTTPException(422, {"message": "Validation failed", "detail": str(e)})

    # Compute diff
    diff_fields = _compute_diff(rec.extracted_data, body.verified_data)

    # Create new subsession record (history preserved)
    now = datetime.now(timezone.utc)
    new_rec = DocumentSession(
        session_id=rec.session_id,
        subsession_id=uuid.uuid4(),
        doc_type=rec.doc_type,
        status=body.status,
        extracted_data=rec.extracted_data,   # original extraction always preserved
        verified_data=body.verified_data,
        diff_summary={"changed_fields": diff_fields, "change_count": len(diff_fields)},
        created_at=now,
        updated_at=now,
    )
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    return new_rec


@app.delete("/records/{record_id}", tags=["Records"])
def delete_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.query(DocumentSession).filter(DocumentSession.id == record_id).first()
    if not rec:
        raise HTTPException(404, f"Record {record_id} not found.")
    db.delete(rec)
    db.commit()
    return {"detail": f"Record {record_id} deleted."}


@app.post("/records/{record_id}/summarize", response_model=SummarizeResponse, tags=["Records"])
def summarize_record(record_id: int, db: Session = Depends(get_db)):
    """
    Generate a human-readable LLM summary from the record's verified (or extracted) data.
    Currently uses a mock summarizer; replace the body of _llm_summarize() with a real
    LLM call (e.g. OpenAI / Gemini) in production.
    """
    rec = db.query(DocumentSession).filter(DocumentSession.id == record_id).first()
    if not rec:
        raise HTTPException(404, f"Record {record_id} not found.")

    data = rec.verified_data or rec.extracted_data or {}
    summary_text, key_figures = _llm_summarize(rec.doc_type, data)

    return SummarizeResponse(
        record_id=rec.id,
        doc_type=rec.doc_type,
        summary=summary_text,
        key_figures=key_figures,
    )


# ── Mock LLM Summarizer ────────────────────────────────────────────────────────

def _llm_summarize(doc_type: str, data: Dict[str, Any]):
    """
    Mock LLM summary generator.  Replace with a real LLM call in production.
    Returns (summary_text: str, key_figures: dict).
    """
    if doc_type == "noa":
        entries = data.get("noa_data", [])
        lines = []
        total_income = 0.0
        total_tax = 0.0
        for e in entries:
            yr = e.get("year", "N/A")
            inc = e.get("employment_income", 0)
            tax = e.get("tax_payable", 0)
            cur = e.get("currency", "SGD")
            total_income += inc
            total_tax += tax
            lines.append(f"  • {yr}: Employment Income {cur} {inc:,.2f}, Tax Payable {cur} {tax:,.2f}")
        body = "\n".join(lines)
        currency = entries[0].get("currency", "SGD") if entries else "SGD"
        summary = (
            f"Notice of Assessment Summary:\n{body}\n"
            f"Total Employment Income: {currency} {total_income:,.2f}\n"
            f"Total Tax Payable: {currency} {total_tax:,.2f}"
        )
        key_figures = {"total_employment_income": total_income, "total_tax_payable": total_tax, "currency": currency}

    elif doc_type == "payslip":
        slips = data.get("payslip", [])
        lines = []
        total_net = 0.0
        for s in slips:
            yr = s.get("payment_year", "N/A")
            mo = s.get("payment_month", "N/A")
            net = s.get("net_pay") or 0
            cur = s.get("currency", "SGD")
            total_net += net
            lines.append(f"  • {mo} {yr}: Net Pay {cur} {net:,.2f}")
        body = "\n".join(lines)
        currency = slips[0].get("currency", "SGD") if slips else "SGD"
        summary = (
            f"Payslip Summary ({len(slips)} month(s)):\n{body}\n"
            f"Total Net Pay: {currency} {total_net:,.2f}\n"
            f"Average Monthly Net Pay: {currency} {(total_net / max(len(slips), 1)):,.2f}"
        )
        key_figures = {"total_net_pay": total_net, "months": len(slips), "currency": currency}

    elif doc_type == "summary":
        emp = data.get("total_source_of_wealth_coming_from_all_the_employment") or 0
        biz = data.get("total_sow_generated_from_client_business") or 0
        prop = data.get("total_gain_of_the_property") or 0
        total = emp + biz + prop
        summary = (
            f"Source of Wealth Summary:\n"
            f"  • Employment: SGD {emp:,.2f}\n"
            f"  • Client Business: SGD {biz:,.2f}\n"
            f"  • Property Gain: SGD {prop:,.2f}\n"
            f"Total Source of Wealth: SGD {total:,.2f}"
        )
        key_figures = {"total_employment": emp, "total_business": biz, "total_property": prop, "grand_total": total}

    else:
        summary = f"Summary for document type '{doc_type}':\n" + str(data)
        key_figures = data

    return summary, key_figures


@app.get("/schema", tags=["Schema"])
def get_schema():
    return {
        "registered_types": list(DOCUMENT_REGISTRY.keys()),
        "models": {k: v.model_json_schema() for k, v in DOCUMENT_REGISTRY.items()},
        "statuses": ["extracted", "reviewing", "verified"],
    }
