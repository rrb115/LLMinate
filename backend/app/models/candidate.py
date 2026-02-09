from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), index=True)
    file: Mapped[str] = mapped_column(String(1000), nullable=False)
    line_start: Mapped[int] = mapped_column(Integer)
    line_end: Mapped[int] = mapped_column(Integer)
    call_snippet: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(100))
    inferred_intent: Mapped[str] = mapped_column(String(200))
    rule_solvability_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    estimated_api_calls_saved: Mapped[int] = mapped_column(Integer, default=0)
    latency_improvement_ms: Mapped[int] = mapped_column(Integer, default=0)
    fallback_behavior: Mapped[str] = mapped_column(Text, default="")
    patch_diff: Mapped[str] = mapped_column(Text, default="")
    patch_explanation: Mapped[str] = mapped_column(Text, default="")
    tests_to_add: Mapped[str] = mapped_column(Text, default="")
    auto_refactor_safe: Mapped[bool] = mapped_column(Boolean, default=False)

    scan = relationship("Scan", back_populates="candidates")
