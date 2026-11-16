"""SQLAlchemy declarative models for HirePilot database schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""
    pass


class Company(Base):
    """Startups and target companies discovered by the agent."""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded array
    funding_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded details
    source: Mapped[str] = mapped_column(String(64), default="unknown")
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="discovered", index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    people: Mapped[list["Person"]] = relationship("Person", back_populates="company", cascade="all, delete-orphan")
    drafts: Mapped[list["Draft"]] = relationship("Draft", back_populates="company", cascade="all, delete-orphan")
    sent_emails: Mapped[list["SentEmail"]] = relationship("SentEmail", back_populates="company")


class Person(Base):
    """Decision makers and hiring managers discovered for a company."""
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=True)
    public_profile_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="company_site")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="people")
    emails: Mapped[list["EmailFound"]] = relationship("EmailFound", back_populates="person", cascade="all, delete-orphan")
    drafts: Mapped[list["Draft"]] = relationship("Draft", back_populates="person")


class EmailFound(Base):
    """Discovered candidate email addresses with verification status."""
    __tablename__ = "emails_found"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    pattern_used: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    mx_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    smtp_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    person: Mapped["Person"] = relationship("Person", back_populates="emails")


class Draft(Base):
    """Personalized email drafts generated for human or autopilot review."""
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("emails_found.id"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_plain: Mapped[str] = mapped_column(Text, nullable=False)
    matching_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    proof_point_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_line_hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fact_check_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    fact_check_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_approval", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="drafts")
    person: Mapped["Person"] = relationship("Person", back_populates="drafts")
    sent_email: Mapped[Optional["SentEmail"]] = relationship("SentEmail", back_populates="draft", uselist=False)


class SentEmail(Base):
    """Record of sent emails via Gmail API."""
    __tablename__ = "sent_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("drafts.id"), unique=True, nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_plain: Mapped[str] = mapped_column(Text, nullable=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(32), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    draft: Mapped["Draft"] = relationship("Draft", back_populates="sent_email")
    company: Mapped["Company"] = relationship("Company", back_populates="sent_emails")
    follow_up: Mapped[Optional["FollowUp"]] = relationship("FollowUp", back_populates="sent_email", uselist=False)
    replies: Mapped[list["Reply"]] = relationship("Reply", back_populates="sent_email")


class FollowUp(Base):
    """Single allowed follow-up message per company outreach."""
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sent_email_id: Mapped[int] = mapped_column(Integer, ForeignKey("sent_emails.id"), unique=True, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_plain: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)  # pending, sent, cancelled
    cancelled_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    sent_email: Mapped["SentEmail"] = relationship("SentEmail", back_populates="follow_up")


class Reply(Base):
    """Inbound email responses detected from contacts."""
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sent_email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sent_emails.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id"), nullable=False)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_plain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(32), default="neutral")
    requires_action: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    sent_email: Mapped[Optional["SentEmail"]] = relationship("SentEmail", back_populates="replies")


class Blacklist(Base):
    """Domain and email blacklist (bounces, opt-outs, blocks)."""
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Run(Base):
    """Agent pipeline execution runs with metrics and status."""
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger_type: Mapped[str] = mapped_column(String(32), default="manual")
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    companies_discovered: Mapped[int] = mapped_column(Integer, default=0)
    emails_drafted: Mapped[int] = mapped_column(Integer, default=0)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Setting(Base):
    """Persistent key-value configuration overrides."""
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
