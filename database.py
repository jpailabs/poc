"""
Database layer — SQLAlchemy 2.0 + PostgreSQL

Table: document_sessions
  id            SERIAL PRIMARY KEY
  session_id    UUID   — groups all edits for one client onboarding case
  subsession_id UUID   — one subsession = one round of user edits
  doc_type      TEXT   — 'noa' | 'payslip' | 'summary' | custom
  status        TEXT   — 'extracted' | 'reviewing' | 'verified'
  extracted_data  JSONB — raw output from extraction pipeline
  verified_data   JSONB — user-curated / corrected version (NULL until verified)
  diff_summary    JSONB — fields that changed between extracted and verified
  created_at    TIMESTAMPTZ
  updated_at    TIMESTAMPTZ
"""

import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Index, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import uuid

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://findoc:findoc_secret@localhost:5432/findoc_db"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class DocumentSession(Base):
    __tablename__ = "document_sessions"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, index=True)
    subsession_id  = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, index=True)
    doc_type       = Column(String(64), nullable=False)          # noa | payslip | summary | …
    status         = Column(String(32), nullable=False, default="extracted")
    extracted_data = Column(JSONB, nullable=False)
    verified_data  = Column(JSONB, nullable=True)
    diff_summary   = Column(JSONB, nullable=True)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_session_doctype", "session_id", "doc_type"),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
