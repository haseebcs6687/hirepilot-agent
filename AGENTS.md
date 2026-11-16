# AGENTS.md — Agent & Developer Handbook for HirePilot

Welcome to **HirePilot**. This document defines the engineering charter, architecture, guardrails, conventions, and operational workflows for all AI agents and human developers contributing to this codebase.

---

## 1. Project Mission & Purpose

**HirePilot** is a local, privacy-first, autonomous job-outreach engine running on the candidate's personal computer. It eliminates tedious manual job hunting by autonomously:
1. **Discovering** emerging startups, high-growth companies, and stealth teams from legal public sources (Y Combinator, GitHub, Product Hunt, RSS/news feeds).
2. **Enriching** company profiles (tech stack, stage, recent launches, team size, challenges).
3. **Identifying** key hiring decision makers (Founders, CEO, CTO, VPE, Head of Engineering, Technical Recruiters).
4. **Discovering & Verifying** work emails via pattern inference, DNS/MX validation, and passive verification.
5. **Evaluating Match Scores** between company requirements and the candidate's verified profile.
6. **Generating Hyper-Personalized Outreach** in the candidate's authentic voice (<120 words, authentic hook, verified proof point, frictionless low-pressure call to action).
7. **Fact-Checking Drafts** with zero tolerance for hallucinations (every metric and accomplishment must exist in `private/profile.yaml` or `private/cv.md`).
8. **Safely Sending & Tracking** outreach via the candidate's connected Gmail API with strict deliverability safeguards (daily caps, random delays, working hours, bounce handling, deduplication, max 1 follow-up, instant sequence stop on reply).
9. **Supervising via Dashboard** with real-time Streamlit UI, manual approval queues, and kill switches.

---

## 2. Inviolable Guardrails & Rules

### Rule 1: Zero Paid Tool Dependencies
- Primary LLM: **Google Gemini API (Free Tier)**.
- Fallback LLM: **Groq API (Free Tier)**.
- Rate limiting and retry policies must strictly respect provider free tier constraints (e.g. 15 RPM for Gemini, 30 RPM for Groq).

### Rule 2: Strict Legal & Ethical Sourcing (NO LinkedIn Scraping)
- **NEVER** scrape LinkedIn, automate LinkedIn logins, use headless browsers on LinkedIn, or interact with LinkedIn APIs.
- Sourcing must use public, open, and compliant web sources: company career sites, GitHub public repositories/profiles, press releases, startup directories (Y Combinator, Product Hunt), and DNS records.

### Rule 3: Zero Hallucinations / Strict Truth Grounding
- **NEVER** invent facts, metrics, past titles, years of experience, or claims about the candidate.
- The outreach writer and fact-checker must strictly ground all claims in `private/profile.yaml` and `private/cv.md`. If a claim cannot be verified against the candidate's profile, the draft must be rejected or rewritten.

### Rule 4: Public Repository Safety & Secret Isolation
- The repository is open-source and public-facing.
- Candidate personal data lives **only** in `private/`, which is git-ignored.
- Environment variables and secrets live **only** in `.env`, which is git-ignored.
- Template files live in `private.example/` and `.env.example`.
- Pre-commit check (`python scripts/check_secrets.py`) must pass before any commit.

### Rule 5: Fail-Safe Deliverability & Defaults
- `dry_run = True` is the hardcoded default. Emails are saved to `drafts` and never sent unless explicitly confirmed or configured.
- `autopilot = False` is the default. Background automation requires explicit user toggle.
- `kill_switch = False` by default; when toggled to `True`, all background jobs, outbound calls, and dispatch routines halt immediately.
- Strict daily send caps (default: 5/day for fresh accounts; gradual warm-up).
- Working hours only (e.g. 09:00 - 17:00 in candidate's chosen timezone, Monday-Friday).
- Random jittered delays between sends (180s - 600s).
- Exactly **one** decision maker emailed per company.
- Exactly **one** follow-up email allowed per contact, cancelled immediately if any inbound reply is detected.

### Rule 6: Anti-Spam Email Crafting
- Plain text only (MIME `text/plain`).
- No tracking pixels, web beacons, open trackers, or click-tracking URL wrappers.
- No attachments.
- Maximum 1 hyper-relevant link (e.g. candidate portfolio or GitHub).
- Under 120 words.
- Specific observation in the very first sentence.

---

## 3. Architecture & Code Structure

```
hirepilot/
├── src/hirepilot/
│   ├── config.py           # Pydantic Settings (.env loader)
│   ├── logger.py           # Structured logging
│   ├── llm/                # LLM abstraction (Gemini, Groq, fallback, rate limiting)
│   ├── db/                 # SQLAlchemy 2.0 models, session management, init script
│   ├── agents/             # LangGraph state machine & orchestration nodes
│   ├── discovery/          # Public startup sourcing engines
│   ├── enrichment/         # Tech stack & company signals extractor
│   ├── people/             # Decision maker finder
│   ├── emailfinder/        # Pattern generator, MX & SMTP verifier
│   ├── writer/             # Style-matching email generator & fact checker
│   ├── sender/             # Gmail API client, daily cap tracker, warm-up logic
│   ├── scheduler/          # APScheduler background automation
│   ├── api/                # FastAPI backend endpoints
│   └── dashboard/          # Streamlit UI dashboard
├── tests/                  # Pytest test suite (unit & integration tests)
├── scripts/                # Utility & security verification scripts
├── docs/                   # Architectural blueprints, decisions, progress
├── private.example/        # Templates for user profile, CV, and writing samples
├── pyproject.toml          # Build configuration & dependencies
└── requirements.txt        # Frozen dependencies
```

---

## 4. Coding Conventions & Standards

- **Python Version**: `>= 3.10` (tested on Python 3.11 - 3.13).
- **Type Annotations**: Mandatory type hints for all function signatures and class definitions (`from __future__ import annotations`).
- **Data Validation**: Use `pydantic.BaseModel` for payloads and `pydantic-settings` for environment configuration.
- **ORM & Database**: SQLAlchemy 2.0 with type-annotated `Mapped[...]` and `mapped_column(...)`. SQLite with `PRAGMA foreign_keys=ON;`.
- **Formatting & Linting**: Ruff for linting and code formatting (`ruff check .`, `ruff format .`).
- **Async vs Sync**: Use async for network I/O (httpx, LangGraph nodes) and standard sync where suitable (database transactions, local disk operations).
- **Git Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

---

## 5. Development Workflows

### Virtual Environment Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### Running Tests
```powershell
.venv\Scripts\pytest -v
```

### Running Security Pre-Commit Check
```powershell
python scripts/check_secrets.py
```

### Installing Git Hooks
```powershell
python scripts/setup_hooks.py
```

---

## 6. How Future Agent Sessions Should Continue Work

1. Read `docs/PROGRESS.md` to see the current phase and remaining checklist items.
2. Read `docs/DECISIONS.md` for architectural rationale and design choices.
3. Keep code modular, strictly typed, and backed by automated tests.
4. Run tests and `python scripts/check_secrets.py` before committing.
5. Record new architectural choices in `docs/DECISIONS.md` and mark checklist items in `docs/PROGRESS.md`.
