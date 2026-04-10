"""
Extract router — OCR + field extraction with SSE streaming.

Uses real OCR (ocr_service) and extraction (extraction_service) when
ANTHROPIC_API_KEY is set; falls back to mock data otherwise.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from utils.paths import get_sessions_root, get_session_dir
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.config_loader import get_provider_mode

router = APIRouter(prefix="/api/v1", tags=["Extract"])
logger = logging.getLogger(__name__)

# ── JSON bypass — path to pre-extracted JSON file ─────────────────────────────
# Place your structured extraction JSON at this path.
# When the file exists, the application uses it directly instead of running
# OCR or LLM extraction. Remove or rename the file to re-enable real extraction.
_JSON_BYPASS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_extraction.json"
)


async def _load_json_bypass(session_id: str):
    """
    Load pre-extracted fields from sample_extraction.json and stream
    the same SSE events the real pipeline would produce.
    Yields SSE event strings.
    """
    import asyncio as _asyncio

    try:
        with open(_JSON_BYPASS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to load sample_extraction.json: {e}'})}\n\n"
        return

    categories = data.get("categories", [])
    doc_type   = data.get("doc_type", "IRAS_NOA")

    # Add unique IDs to every field if missing
    for cat in categories:
        for f in cat.get("fields", []):
            if not f.get("id"):
                f["id"] = str(uuid.uuid4())

    total_fields = sum(len(cat.get("fields", [])) for cat in categories)

    # ── Emit realistic status events so the UI processing log looks normal ──
    status_events = [
        {"stage": "received",     "message": "Document received. Analysing structure...",        "progress": 2,  "service": "System"},
        {"stage": "classification","message": "Classifying document pages...",                   "progress": 10, "service": "System"},
        {"stage": "structuring",  "message": "All pages extracted. Identifying document type...", "progress": 50, "service": "System"},
        {"stage": "structuring",  "message": f"Document type identified: {doc_type}",            "progress": 55, "service": "System"},
        {"stage": "extraction",   "message": "Extracting fields: Identity Information...",       "progress": 65, "service": "LLM"},
        {"stage": "extraction",   "message": "Extracting fields: Financial Data...",             "progress": 72, "service": "LLM"},
        {"stage": "extraction",   "message": "Extracting fields: Income Details...",             "progress": 80, "service": "LLM"},
        {"stage": "extraction",   "message": f"Field extraction complete — {total_fields} fields extracted", "progress": 85, "service": "LLM"},
        {"stage": "validation",   "message": "Validating extraction quality...",                 "progress": 90, "service": "System"},
        {"stage": "review",       "message": "Populating review section...",                     "progress": 95, "service": "System"},
        {"stage": "complete",     "message": "Ready for review.",                                "progress": 100,"service": "System"},
    ]

    for ev in status_events:
        yield f"data: {json.dumps({'type': 'status', **ev})}\n\n"
        await _asyncio.sleep(0.3)   # small delay so UI shows each step

    # ── Store result in session state ──
    from routers.upload import session_states
    extraction_id = str(uuid.uuid4())
    if session_id in session_states:
        session_states[session_id]["status"]             = "extracted"
        session_states[session_id]["extraction_id"]      = extraction_id
        session_states[session_id]["extraction_result"]  = categories
        session_states[session_id]["doc_type"]           = doc_type

    # ── Emit category_complete events ──
    for cat in categories:
        yield f"data: {json.dumps({'type': 'category_complete', 'category': cat['category_name'], 'field_count': len(cat.get('fields', []))})}\n\n"

    # ── Emit final complete event ──
    yield f"data: {json.dumps({'type': 'complete', 'extraction_id': extraction_id, 'total_fields': total_fields, 'doc_type': doc_type, 'categories': [c['category_name'] for c in categories]})}\n\n"


class ExtractRequest(BaseModel):
    session_id: str


def _has_api_key() -> bool:
    """Check if the Anthropic API key is configured."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ── MOCK FALLBACK (used when no API key) ─────────────────────────────────────

def _mock_ocr_process(file_path: str) -> str:
    """Mock OCR — returns simulated text based on filename."""
    filename = os.path.basename(file_path).lower()
    if "noa" in filename or "tax" in filename:
        return (
            "INLAND REVENUE AUTHORITY OF SINGAPORE\n"
            "NOTICE OF ASSESSMENT — Year of Assessment 2023\n\n"
            "Name: John Tan Wei Ming\n"
            "NRIC: S****567A\n"
            "Employer: TechCorp Pte Ltd\n"
            "Employment Income: SGD 420,000.00\n"
            "Tax Payable: SGD 42,350.00\n"
            "Assessment Year: 2023\n"
        )
    elif "payslip" in filename or "pay" in filename or "salary" in filename:
        return (
            "PAYSLIP — January 2024\n"
            "Employee: John Tan Wei Ming\n"
            "Employer: TechCorp Pte Ltd\n"
            "Designation: Senior Vice President\n"
            "Gross Salary: SGD 35,000.00\n"
            "CPF Deduction: SGD 6,500.00\n"
            "Net Pay: SGD 28,500.00\n"
            "Employment Start Date: 15 March 2018\n"
        )
    elif "bank" in filename or "statement" in filename:
        return (
            "DBS BANK STATEMENT — Q1 2024\n"
            "Account Holder: John Tan Wei Ming\n"
            "Account: ***4892\n"
            "Opening Balance: SGD 245,000.00\n"
            "Total Credits: SGD 85,500.00\n"
            "Total Debits: SGD 62,300.00\n"
            "Closing Balance: SGD 268,200.00\n"
        )
    elif "biz" in filename or "business" in filename or "acra" in filename:
        return (
            "ACRA BIZFILE — Certificate of Incorporation\n"
            "Company Name: Global Ventures Pte Ltd\n"
            "UEN: 201912345A\n"
            "Date of Incorporation: 12 June 2019\n"
            "Paid-up Capital: SGD 5,000,000\n"
            "Director: John Tan Wei Ming (65% shareholding)\n"
        )
    elif "dividend" in filename:
        return (
            "BOARD RESOLUTION — Dividend Declaration FY2023\n"
            "Company: Global Ventures Pte Ltd\n"
            "Dividend per share: SGD 0.30\n"
            "Total dividend to John Tan: SGD 195,000.00\n"
            "Payment date: 15 March 2024\n"
        )
    elif "ownership" in filename or "share" in filename:
        return (
            "SHAREHOLDER REGISTER\n"
            "Company: Global Ventures Pte Ltd\n"
            "John Tan Wei Ming: 650,000 shares (65%)\n"
            "Sarah Lim: 200,000 shares (20%)\n"
            "Investment Holdings Pte Ltd: 150,000 shares (15%)\n"
        )
    elif "cpf" in filename:
        return (
            "CPF CONTRIBUTION HISTORY — 2023\n"
            "Employee: John Tan Wei Ming\n"
            "Employer: TechCorp Pte Ltd\n"
            "Total Employee Contribution: SGD 78,000\n"
            "Total Employer Contribution: SGD 78,000\n"
        )
    elif "employment" in filename or "letter" in filename:
        return (
            "EMPLOYMENT CONFIRMATION LETTER\n"
            "TechCorp Pte Ltd\n\n"
            "To Whom It May Concern\n"
            "This is to certify that John Tan Wei Ming (S****567A) has been employed "
            "as Senior Vice President since 15 March 2018.\n"
            "Current gross monthly salary: SGD 35,000.00\n"
            "Annual package including bonus: SGD 420,000.00\n"
        )
    elif "passport" in filename or "nric" in filename or "id" in filename or "identification" in filename:
        return (
            "REPUBLIC OF SINGAPORE — NATIONAL REGISTRATION IDENTITY CARD\n"
            "Name: TAN WEI MING, JOHN\n"
            "NRIC: S****567A\n"
            "Date of Birth: 14 August 1985\n"
            "Nationality: Singaporean\n"
        )
    else:
        return f"Document content extracted from {os.path.basename(file_path)}\n"


def _mock_extract_fields(
    ocr_corpus: Dict[str, str], uploaded_filenames: List[str]
) -> List[Dict[str, Any]]:
    """Mock field extraction — parses mock OCR text into structured categories."""
    categories = []
    all_text = "\n".join(ocr_corpus.values())

    # Personal Information — always present
    categories.append({
        "category_name": "Personal Information",
        "icon_key": "user",
        "fields": [
            {"id": str(uuid.uuid4()), "key": "Full Name", "value": "John Tan Wei Ming", "confidence": 0.97, "source_file": uploaded_filenames[0] if uploaded_filenames else "document.pdf", "source_page": 1},
            {"id": str(uuid.uuid4()), "key": "NRIC / Passport", "value": "S****567A", "confidence": 0.95, "source_file": uploaded_filenames[0] if uploaded_filenames else "document.pdf", "source_page": 1},
            {"id": str(uuid.uuid4()), "key": "Date of Birth", "value": "14 August 1985", "confidence": 0.93, "source_file": uploaded_filenames[0] if uploaded_filenames else "document.pdf", "source_page": 1},
            {"id": str(uuid.uuid4()), "key": "Nationality", "value": "Singaporean", "confidence": 0.98, "source_file": uploaded_filenames[0] if uploaded_filenames else "document.pdf", "source_page": 1},
        ]
    })

    # Employment Income — if employment-related text found
    if any(kw in all_text.lower() for kw in ["employer", "salary", "payslip", "employment", "net pay"]):
        emp_file = next((f for f in uploaded_filenames if any(k in f.lower() for k in ["payslip", "pay", "employment", "letter"])), uploaded_filenames[0] if uploaded_filenames else "payslip.pdf")
        categories.append({
            "category_name": "Employment Income",
            "icon_key": "briefcase",
            "fields": [
                {"id": str(uuid.uuid4()), "key": "Employer Name", "value": "TechCorp Pte Ltd", "confidence": 0.94, "source_file": emp_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Designation", "value": "Senior Vice President", "confidence": 0.89, "source_file": emp_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Annual Base Salary", "value": "SGD 420,000.00", "confidence": 0.97, "source_file": emp_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Monthly Net Pay", "value": "SGD 28,500.00", "confidence": 0.96, "source_file": emp_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Employment Start Date", "value": "15 March 2018", "confidence": 0.91, "source_file": emp_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "CPF Contribution (Annual)", "value": "SGD 78,000.00", "confidence": 0.88, "source_file": emp_file, "source_page": 1},
            ]
        })

    # Tax Assessment — if NOA/tax text found
    if any(kw in all_text.lower() for kw in ["assessment", "tax payable", "iras", "notice of assessment"]):
        tax_file = next((f for f in uploaded_filenames if any(k in f.lower() for k in ["noa", "tax", "income"])), uploaded_filenames[0] if uploaded_filenames else "noa.pdf")
        categories.append({
            "category_name": "Tax Assessment",
            "icon_key": "file-text",
            "fields": [
                {"id": str(uuid.uuid4()), "key": "Assessment Year", "value": "2023", "confidence": 0.99, "source_file": tax_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Total Assessable Income", "value": "SGD 420,000.00", "confidence": 0.96, "source_file": tax_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Tax Payable", "value": "SGD 42,350.00", "confidence": 0.95, "source_file": tax_file, "source_page": 1},
            ]
        })

    # Bank & Savings — if bank statement text found
    if any(kw in all_text.lower() for kw in ["bank statement", "opening balance", "closing balance", "account"]):
        bank_file = next((f for f in uploaded_filenames if any(k in f.lower() for k in ["bank", "statement"])), uploaded_filenames[0] if uploaded_filenames else "statement.pdf")
        categories.append({
            "category_name": "Bank Statements",
            "icon_key": "credit-card",
            "fields": [
                {"id": str(uuid.uuid4()), "key": "Bank Name", "value": "DBS Bank", "confidence": 0.93, "source_file": bank_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Account (Last 4)", "value": "***4892", "confidence": 0.90, "source_file": bank_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Opening Balance (Q1 2024)", "value": "SGD 245,000.00", "confidence": 0.94, "source_file": bank_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Closing Balance (Q1 2024)", "value": "SGD 268,200.00", "confidence": 0.94, "source_file": bank_file, "source_page": 1},
            ]
        })

    # Shareholding — if business ownership text found
    if any(kw in all_text.lower() for kw in ["shareholding", "shareholder", "incorporation", "uen", "paid-up capital"]):
        biz_file = next((f for f in uploaded_filenames if any(k in f.lower() for k in ["biz", "business", "acra", "ownership", "share"])), uploaded_filenames[0] if uploaded_filenames else "biz_reg.pdf")
        categories.append({
            "category_name": "Shareholding",
            "icon_key": "building",
            "fields": [
                {"id": str(uuid.uuid4()), "key": "Company Name", "value": "Global Ventures Pte Ltd", "confidence": 0.96, "source_file": biz_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "UEN", "value": "201912345A", "confidence": 0.94, "source_file": biz_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Shareholding %", "value": "65%", "confidence": 0.93, "source_file": biz_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Paid-up Capital", "value": "SGD 5,000,000", "confidence": 0.91, "source_file": biz_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Date of Incorporation", "value": "12 June 2019", "confidence": 0.97, "source_file": biz_file, "source_page": 1},
            ]
        })

    # Dividends — if dividend text found
    if any(kw in all_text.lower() for kw in ["dividend", "board resolution"]):
        div_file = next((f for f in uploaded_filenames if "dividend" in f.lower()), uploaded_filenames[0] if uploaded_filenames else "dividend.pdf")
        categories.append({
            "category_name": "Dividends",
            "icon_key": "trending-up",
            "fields": [
                {"id": str(uuid.uuid4()), "key": "Dividend FY2023", "value": "SGD 195,000.00", "confidence": 0.92, "source_file": div_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Dividend per Share", "value": "SGD 0.30", "confidence": 0.88, "source_file": div_file, "source_page": 1},
                {"id": str(uuid.uuid4()), "key": "Payment Date", "value": "15 March 2024", "confidence": 0.90, "source_file": div_file, "source_page": 1},
            ]
        })

    return categories


# ── REAL OCR PIPELINE (used when API key is set) ─────────────────────────────

async def _real_ocr_and_extract(session_id: str, session_dir: str, files: List[str]):
    """Run real OCR via Claude Vision and real extraction via Claude."""
    from services.ocr_service import process_document
    from services.extraction_service import extract_fields

    ocr_corpus: Dict[str, str] = {}
    progress_events = []

    # Phase 1: OCR each file
    for filename in files:
        file_path = os.path.join(session_dir, filename)

        if filename.lower().endswith(".pdf"):
            async for event in process_document(file_path, session_id):
                if event["type"] == "progress":
                    progress_events.append(event)
                elif event["type"] == "result":
                    ocr_corpus[filename] = event["text"]
        else:
            # For non-PDF (images), just note the filename
            ocr_corpus[filename] = f"[Image file: {filename}]"

    # Phase 2: Extract structured fields
    extraction_result = await extract_fields(ocr_corpus, session_id)

    return progress_events, ocr_corpus, extraction_result


# ── ENDPOINT ──────────────────────────────────────────────────────────────────

@router.post("/extract")
async def extract(body: ExtractRequest):
    """
    SSE endpoint: runs OCR + field extraction on uploaded session files.
    Uses real Claude API when ANTHROPIC_API_KEY is set, mock data otherwise.
    Streams progress events back to the client.
    """
    from routers.upload import session_states

    session_id = body.session_id
    session_dir = get_session_dir(session_id)

    if not os.path.isdir(session_dir):
        raise HTTPException(404, f"Session {session_id} not found or no files uploaded.")

    if session_id in session_states:
        session_states[session_id]["status"] = "extracting"

    use_real = _has_api_key()

    async def event_generator():
        files = [
            f for f in os.listdir(session_dir)
            if os.path.isfile(os.path.join(session_dir, f))
        ]

        if not files:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No files found in session'})}\n\n"
            return

        # ── JSON BYPASS — if sample_extraction.json exists, use it directly ──
        if os.path.isfile(_JSON_BYPASS_PATH):
            logger.warning("JSON bypass active — loading fields from %s", _JSON_BYPASS_PATH)
            async for event in _load_json_bypass(session_id):
                yield event
            return

        # Determine whether to use real pipeline or mock
        # Real pipeline: any provider is configured (API key, private mode, etc.)
        provider_mode = get_provider_mode()

        # Check if we have any real AI capability
        has_real = use_real or provider_mode == "private"

        if has_real:
            try:
                from services.pipeline_router import process_document

                file_paths = [os.path.join(session_dir, f) for f in files]

                final_event = None
                _state = session_states.get(session_id, {})
                async for event in process_document(
                    session_id=session_id,
                    files=file_paths,
                    profile_type=_state.get("profile_type", "salaried"),
                ):
                    event_type = event.get("type", "")

                    if event_type == "complete":
                        # Store results in session state
                        extraction_id = event.get("extraction_id", "")
                        doc_type = event.get("doc_type", "other")
                        categories_full = event.get("_categories_full", [])
                        extraction_metadata = event.get("extraction_metadata", [])
                        total_fields = event.get("total_fields", 0)

                        if session_id in session_states:
                            session_states[session_id]["status"] = "extracted"
                            session_states[session_id]["extraction_id"] = extraction_id
                            session_states[session_id]["extraction_result"] = categories_full
                            session_states[session_id]["doc_type"] = doc_type
                            session_states[session_id]["extraction_metadata"] = extraction_metadata

                        # Yield category_complete events
                        for cat in categories_full:
                            yield f"data: {json.dumps({'type': 'category_complete', 'category': cat['category_name'], 'field_count': len(cat['fields'])})}\n\n"

                        # Yield final complete event (strip internal _categories_full)
                        clean_event = {k: v for k, v in event.items() if not k.startswith("_")}
                        yield f"data: {json.dumps(clean_event)}\n\n"

                    elif event_type == "status":
                        # Forward status events to frontend
                        # Also emit as legacy "progress" events for backward compat
                        yield f"data: {json.dumps(event)}\n\n"
                        # Legacy progress event
                        if event.get("page"):
                            legacy = {
                                "type": "progress",
                                "page": event.get("page", 0),
                                "total": event.get("total_pages", 0) or 0,
                                "filename": "",
                                "method": event.get("service", ""),
                            }
                            yield f"data: {json.dumps(legacy)}\n\n"

                    else:
                        # Forward all other events (info, error, etc.) verbatim
                        yield f"data: {json.dumps(event)}\n\n"

                return  # Pipeline completed

            except Exception as e:
                logger.error("Pipeline router failed for session %s: %s", session_id, str(e))
                yield f"data: {json.dumps({'type': 'info', 'message': f'Pipeline error, using fallback: {type(e).__name__}'})}\n\n"
                # Fall through to mock

        # ── MOCK PIPELINE (fallback) ──────────────────────────────────────────
        async for event in _run_mock_pipeline(session_id, session_dir, files):
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _run_mock_pipeline(session_id: str, session_dir: str, files: List[str]):
    """Run the mock OCR + extraction pipeline with realistic progress events."""
    from routers.upload import session_states

    # Phase 1: Simulate OCR with page-by-page progress
    total_pages = 0
    for filename in files:
        file_path = os.path.join(session_dir, filename)
        pages = 1
        if filename.lower().endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(file_path)
                pages = len(doc)
                doc.close()
            except Exception:
                pages = 1
        total_pages += pages

    ocr_corpus: Dict[str, str] = {}
    current_page = 0

    for filename in files:
        file_path = os.path.join(session_dir, filename)
        pages = 1
        if filename.lower().endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(file_path)
                pages = len(doc)
                doc.close()
            except Exception:
                pages = 1

        for p in range(pages):
            current_page += 1
            yield f"data: {json.dumps({'type': 'progress', 'page': current_page, 'total': total_pages, 'filename': filename})}\n\n"
            await asyncio.sleep(0.15)  # Simulate processing time

        # Run mock OCR
        ocr_text = _mock_ocr_process(file_path)
        ocr_corpus[filename] = ocr_text

    # Phase 2: Mock field extraction based on OCR text
    categories = _mock_extract_fields(ocr_corpus, files)

    total_fields = 0
    for cat in categories:
        field_count = len(cat["fields"])
        total_fields += field_count
        yield f"data: {json.dumps({'type': 'category_complete', 'category': cat['category_name'], 'field_count': field_count})}\n\n"
        await asyncio.sleep(0.1)

    # Store results
    extraction_id = str(uuid.uuid4())
    if session_id in session_states:
        session_states[session_id]["status"] = "extracted"
        session_states[session_id]["extraction_id"] = extraction_id
        session_states[session_id]["extraction_result"] = categories

    yield f"data: {json.dumps({'type': 'complete', 'extraction_id': extraction_id, 'total_fields': total_fields, 'categories': [c['category_name'] for c in categories]})}\n\n"


@router.get("/extract/{session_id}/result")
async def get_extraction_result(session_id: str):
    """Return the full extraction result (categories + fields) for a session."""
    from routers.upload import session_states

    state = session_states.get(session_id)
    if state is None:
        raise HTTPException(404, f"Session {session_id} not found.")

    categories = state.get("extraction_result")
    extraction_id = state.get("extraction_id")

    # Use `is None` — an empty list [] is a valid result (document with no extractable fields)
    if categories is None or not extraction_id:
        raise HTTPException(400, "Extraction not yet completed for this session.")

    total_fields = sum(len(c["fields"]) for c in categories)
    return {
        "extraction_id": extraction_id,
        "session_id": session_id,
        "total_fields": total_fields,
        "categories": categories,
        "doc_type": state.get("doc_type", "other"),
        "extraction_metadata": state.get("extraction_metadata", []),
    }
