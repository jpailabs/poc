"""
Seed the database with realistic sample financial document extractions.
Run:  python seed.py
"""
import uuid
from datetime import datetime, timezone, timedelta
from database import SessionLocal, init_db, DocumentSession

SESSIONS = [
    {
        "session_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        "client": "Tan Wei Ming",
        "docs": [
            {
                "doc_type": "noa",
                "status": "verified",
                "extracted_data": {
                    "noa_data": [
                        {"year": 2023, "employment_income": 95000.0, "tax_payable": 6200.0, "currency": "SGD"},
                        {"year": 2022, "employment_income": 88000.0, "tax_payable": 5600.0, "currency": "SGD"},
                        {"year": 2021, "employment_income": 82000.0, "tax_payable": 5100.0, "currency": "SGD"},
                    ]
                },
                "verified_data": {
                    "noa_data": [
                        {"year": 2023, "employment_income": 95000.0, "tax_payable": 6200.0, "currency": "SGD"},
                        {"year": 2022, "employment_income": 88500.0, "tax_payable": 5650.0, "currency": "SGD"},
                        {"year": 2021, "employment_income": 82000.0, "tax_payable": 5100.0, "currency": "SGD"},
                    ]
                },
                "diff_summary": {"changed_fields": ["noa_data[1].employment_income", "noa_data[1].tax_payable"]}
            },
            {
                "doc_type": "payslip",
                "status": "verified",
                "extracted_data": {
                    "payslip": [
                        {"payment_year": 2024, "payment_month": "January",  "net_pay": 7200.50, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "February", "net_pay": 7200.50, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "March",    "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "April",    "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "May",      "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "June",     "net_pay": 7800.00, "currency": "SGD"},
                    ]
                },
                "verified_data": {
                    "payslip": [
                        {"payment_year": 2024, "payment_month": "January",  "net_pay": 7200.50, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "February", "net_pay": 7200.50, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "March",    "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "April",    "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "May",      "net_pay": 7350.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "June",     "net_pay": 7800.00, "currency": "SGD"},
                    ]
                },
                "diff_summary": {"changed_fields": []}
            },
            {
                "doc_type": "summary",
                "status": "reviewing",
                "extracted_data": {
                    "total_source_of_wealth_coming_from_all_the_employment": 265000.0,
                    "total_sow_generated_from_client_business": None,
                    "total_gain_of_the_property": 120000.0
                },
                "verified_data": None,
                "diff_summary": None
            }
        ]
    },
    {
        "session_id": uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002"),
        "client": "Priya Nair",
        "docs": [
            {
                "doc_type": "payslip",
                "status": "reviewing",
                "extracted_data": {
                    "payslip": [
                        {"payment_year": 2024, "payment_month": "March",    "net_pay": 5500.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "April",    "net_pay": 5500.00, "currency": "SGD"},
                        {"payment_year": 2024, "payment_month": "May",      "net_pay": 5750.00, "currency": "SGD"},
                    ]
                },
                "verified_data": None,
                "diff_summary": None
            },
            {
                "doc_type": "summary",
                "status": "extracted",
                "extracted_data": {
                    "total_source_of_wealth_coming_from_all_the_employment": 66000.0,
                    "total_sow_generated_from_client_business": 22000.0,
                    "total_gain_of_the_property": None
                },
                "verified_data": None,
                "diff_summary": None
            }
        ]
    },
    {
        "session_id": uuid.UUID("cccccccc-0000-0000-0000-000000000003"),
        "client": "Ahmad Fauzi",
        "docs": [
            {
                "doc_type": "noa",
                "status": "extracted",
                "extracted_data": {
                    "noa_data": [
                        {"year": 2023, "employment_income": 145000.0, "tax_payable": 14800.0, "currency": "SGD"},
                        {"year": 2022, "employment_income": 130000.0, "tax_payable": 12600.0, "currency": "SGD"},
                    ]
                },
                "verified_data": None,
                "diff_summary": None
            }
        ]
    }
]

def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(DocumentSession).count()
        if existing > 0:
            print(f"DB already has {existing} records. Skipping seed.")
            return

        now = datetime.now(timezone.utc)
        for i, session in enumerate(SESSIONS):
            delta = timedelta(days=i * 3)
            for j, doc in enumerate(session["docs"]):
                record = DocumentSession(
                    session_id=session["session_id"],
                    subsession_id=uuid.uuid4(),
                    doc_type=doc["doc_type"],
                    status=doc["status"],
                    extracted_data=doc["extracted_data"],
                    verified_data=doc.get("verified_data"),
                    diff_summary=doc.get("diff_summary"),
                    created_at=now - delta - timedelta(hours=j),
                    updated_at=now - delta - timedelta(hours=j) + timedelta(minutes=30),
                )
                db.add(record)
        db.commit()
        print(f"✓ Seeded {sum(len(s['docs']) for s in SESSIONS)} records across {len(SESSIONS)} sessions.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
