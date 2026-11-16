# Architecture & Engineering Decision Records (ADR)

This document logs all fundamental technical decisions, design choices, trade-offs, and rationale for HirePilot.

---

### ADR-001: Python 3.10+ with Strict Type Hinting & Pydantic 2
- **Status**: Accepted
- **Context**: HirePilot needs a modern, robust, and extensible backend for multi-agent workflows, schema validation, and background job scheduling.
- **Decision**: Target Python `>= 3.10` with mandatory type hints (`from __future__ import annotations`), Pydantic 2.x for data schemas and configuration management, and SQLAlchemy 2.0 with type annotations (`Mapped[...]`).
- **Consequences**: Ensures compile-time and runtime type safety, fast serialization, and clean integrations with FastAPI and LangGraph.

---

### ADR-002: Zero-Cost LLM Strategy with Gemini (Primary) and Groq (Fallback)
- **Status**: Accepted
- **Context**: The product must run exclusively on free tools without paid API subscriptions. Free tier APIs have strict rate limits (e.g. Gemini AI Studio allows 15 requests per minute; Groq allows 30 requests per minute) and occasional outages.
- **Decision**:
  - Implement a provider-agnostic `LLMProvider` interface.
  - Primary provider: Google Gemini (`gemini-1.5-flash`).
  - Fallback provider: Groq (`llama-3.3-70b-versatile`).
  - Implement a `SlidingWindowRateLimiter` to proactively pace requests within RPM limits.
  - Wrap both in `FallbackLLMProvider` which handles retries on transient errors and automatically fails over from Gemini to Groq on 429 quota exhaustion or service unavailability.
- **Consequences**: Completely free operation with high resilience and reliability. Zero downtime when one provider exhausts rate limits.

---

### ADR-003: Direct HTTP Client (`httpx`) for LLM Providers
- **Status**: Accepted
- **Context**: Third-party vendor SDKs can introduce conflicting dependencies, bloated install footprints, and slower startup times.
- **Decision**: Implement Gemini and Groq providers using `httpx` directly against their official REST endpoints with standardized request/response translation.
- **Consequences**: Lightweight codebase, explicit control over HTTP timeouts and connection pooling, transparent error handling for HTTP status codes (401, 429, 5xx), and trivial mocking in unit tests.

---

### ADR-004: SQLite with SQLAlchemy 2.0 for Local Relational Storage
- **Status**: Accepted
- **Context**: HirePilot runs locally on the user's PC. It requires zero configuration, zero cloud database dependencies, and persistent state across crashes.
- **Decision**: Use local SQLite database (`hirepilot.db`) with SQLAlchemy 2.0 Declarative Models. Explicitly enforce SQLite foreign key constraints via `PRAGMA foreign_keys=ON;`.
- **Consequences**: Zero setup friction for end users. Full ACID compliance, foreign key cascades, and single-file portability. Easy migration to PostgreSQL in the future if multi-user support is needed.

---

### ADR-005: Strict Prohibition of LinkedIn Automation
- **Status**: Accepted
- **Context**: Automating LinkedIn web sessions or scraping violates LinkedIn terms of service, leads to account bans, and breaks frequently due to anti-bot measures (Cloudflare, reCAPTCHA).
- **Decision**: Strictly prohibit all LinkedIn scraping, automation, and session cookies. Source decision-makers exclusively through legal, public web sources: company career pages, GitHub repositories, press releases, and startup directory indices.
- **Consequences**: Eliminates account ban risks, avoids fragile scraping hacks, and maintains ethical and legal compliance.

---

### ADR-006: Personal Data and Secret Isolation (`private/` & Git Hooks)
- **Status**: Accepted
- **Context**: The repository is planned to be published publicly on GitHub, but contains candidate resumes, writing samples, email credentials, and API keys.
- **Decision**:
  - Store all candidate data strictly in `private/`, which is permanently git-ignored.
  - Provide complete dummy templates in `private.example/` and `.env.example`.
  - Create a pre-commit security check script (`scripts/check_secrets.py`) that scans staged files for forbidden paths (`private/`, `.env`, `*.db`, `token*.json`) and secret key regexes.
  - Provide an automatic hook installer (`scripts/setup_hooks.py`).
- **Consequences**: Zero risk of leaking candidate identity, personal email tokens, or API credentials to public repositories.

---

### ADR-007: Safe-by-Default Execution (`dry_run=True`, `kill_switch`)
- **Status**: Accepted
- **Context**: Autonomous email dispatching can inadvertently spam contacts if misconfigured.
- **Decision**:
  - `dry_run = True` is the hardcoded default setting. All drafts are stored in the database for manual review; no outbound network call is made to Gmail.
  - A single configuration switch (`DRY_RUN=false` or UI button) is required to enable live sending.
  - Implement a master `kill_switch` that halts all background runners and outbound dispatches immediately upon activation.
- **Consequences**: End users have complete control and safety. Unintended email dispatches are physically blocked by default.

---

### ADR-008: Deliverability Standards & Anti-Spam Email Philosophy
- **Status**: Accepted
- **Context**: Cold outreach often gets flagged as spam if emails look automated, contain tracking pixels, or are sent in bulk bursts.
- **Decision**:
  - Plain text emails only (`text/plain`).
  - No tracking pixels, open beacons, or URL tracking redirects.
  - No attachments; maximum 1 clean link.
  - Maximum 120 words.
  - First line must be a specific observation about the company.
  - Exactly one verified proof point from the candidate's profile.
  - Low-pressure, frictionless small ask.
  - Enforce daily caps (starts at 5/day), random send delays (180-600s), and working hours only.
  - Deduplication: exactly one person contacted per company.
  - Exactly one follow-up max, immediately cancelled if a reply is detected.
- **Consequences**: Maximum inbox deliverability, human-like appearance, and high response rates without damaging sender domain reputation.
