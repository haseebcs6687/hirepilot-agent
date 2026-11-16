"""Unit tests for SQLite database schema, constraints, and models."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hirepilot.db.init_db import init_db
from hirepilot.db.models import (
    Base,
    Blacklist,
    Company,
    Draft,
    EmailFound,
    FollowUp,
    Person,
    Reply,
    Run,
    SentEmail,
    Setting,
)


@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_schema_creation_and_company_crud(db_session):
    """Test creating and querying a company record."""
    company = Company(
        name="Acme AI",
        domain="acme.ai",
        website_url="https://acme.ai",
        description="Autonomous developer tooling",
        industry="Developer Tools",
        stage="Seed",
        team_size=15,
        location="San Francisco, CA",
        source="ycombinator",
    )
    db_session.add(company)
    db_session.commit()

    retrieved = db_session.query(Company).filter_by(domain="acme.ai").first()
    assert retrieved is not None
    assert retrieved.name == "Acme AI"
    assert retrieved.stage == "Seed"
    assert retrieved.status == "discovered"


def test_company_people_and_email_relationships(db_session):
    """Test relational integrity from Company -> Person -> EmailFound."""
    company = Company(name="NeuralWorks", domain="neuralworks.com")
    db_session.add(company)
    db_session.commit()

    person = Person(
        company_id=company.id,
        first_name="Alice",
        last_name="Smith",
        full_name="Alice Smith",
        role="Co-Founder & CTO",
        is_decision_maker=True,
    )
    db_session.add(person)
    db_session.commit()

    email_record = EmailFound(
        person_id=person.id,
        company_id=company.id,
        email="alice@neuralworks.com",
        pattern_used="{first}@{domain}",
        mx_valid=True,
        smtp_valid=True,
        verification_status="valid",
        confidence_score=0.95,
        is_primary=True,
    )
    db_session.add(email_record)
    db_session.commit()

    # Query back
    assert len(company.people) == 1
    assert company.people[0].full_name == "Alice Smith"
    assert len(company.people[0].emails) == 1
    assert company.people[0].emails[0].email == "alice@neuralworks.com"


def test_draft_to_sent_and_followup_flow(db_session):
    """Test draft generation, sent email, and follow-up tracking models."""
    company = Company(name="CloudFast", domain="cloudfast.io")
    db_session.add(company)
    db_session.commit()

    person = Person(company_id=company.id, first_name="Bob", last_name="Lee", full_name="Bob Lee", role="CEO")
    db_session.add(person)
    db_session.commit()

    draft = Draft(
        company_id=company.id,
        person_id=person.id,
        recipient_email="bob@cloudfast.io",
        recipient_name="Bob",
        subject="Scaling CloudFast's core platform",
        body_plain="Hi Bob,\nLoved the recent latency benchmarks...",
        first_line_hook="Loved the recent latency benchmarks",
        proof_point_used="Scaled FastAPI backend to 1.2M DAU",
        fact_check_passed=True,
        status="approved",
    )
    db_session.add(draft)
    db_session.commit()

    sent = SentEmail(
        draft_id=draft.id,
        person_id=person.id,
        company_id=company.id,
        recipient_email="bob@cloudfast.io",
        subject=draft.subject,
        body_plain=draft.body_plain,
        message_id="msg_123456",
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(sent)
    db_session.commit()

    follow_up = FollowUp(
        sent_email_id=sent.id,
        company_id=company.id,
        person_id=person.id,
        subject="Re: Scaling CloudFast's core platform",
        body_plain="Hi Bob,\nFollowing up briefly...",
        status="pending",
    )
    db_session.add(follow_up)
    db_session.commit()

    assert draft.sent_email.message_id == "msg_123456"
    assert sent.follow_up.status == "pending"


def test_blacklist_and_runs_models(db_session):
    """Test blacklist and runs tracking."""
    bl = Blacklist(domain="spammy.com", reason="bounced")
    run = Run(id="run_2026_01", trigger_type="manual", status="completed", companies_discovered=10)
    setting = Setting(key="dry_run", value="true")

    db_session.add_all([bl, run, setting])
    db_session.commit()

    assert db_session.query(Blacklist).filter_by(domain="spammy.com").count() == 1
    assert db_session.query(Run).filter_by(id="run_2026_01").first().companies_discovered == 10
    assert db_session.query(Setting).filter_by(key="dry_run").first().value == "true"


def test_init_db_seeds_default_settings(tmp_path):
    """Test init_db creates all tables and seeds default settings."""
    test_db_file = tmp_path / "test_init.db"
    test_engine = create_engine(f"sqlite:///{test_db_file}")

    init_db(target_engine=test_engine)

    TestingSession = sessionmaker(bind=test_engine)
    with TestingSession() as session:
        settings_count = session.query(Setting).count()
        assert settings_count >= 6
        dry_run = session.query(Setting).filter_by(key="dry_run").first()
        assert dry_run is not None
        assert dry_run.value == "true"

