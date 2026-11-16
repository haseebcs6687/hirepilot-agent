# HirePilot Project Progress & Phase Checklist

*Last Updated: Phase 0 Completion*

---

## Roadmap Overview

```
[Phase 0: Foundations & Safety]  -> COMPLETED
      |
      v
[Phase 1: Profile & Company Discovery]
      |
      v
[Phase 2: Company Enrichment & People Finder]
      |
      v
[Phase 3: Email Finding & MX/SMTP Verification]
      |
      v
[Phase 4: Personalized Outreach Writer & Fact Checker]
      |
      v
[Phase 5: Gmail Dispatcher & Deliverability Engine]
      |
      v
[Phase 6: Reply Detection & Follow-up Scheduler]
      |
      v
[Phase 7: LangGraph Orchestration & APScheduler Automation]
      |
      v
[Phase 8: FastAPI API & Streamlit Dashboard]
```

---

## Detailed Phase Status

### Phase 0: Foundations, Architecture & Security (COMPLETED)
- [x] Create `.gitignore` first (excluding `.env`, `*.db`, `private/`, `credentials*.json`, `token*.json`, `logs/`, `data/`, etc.).
- [x] Configure git repository with remote origin `https://github.com/haseebcs6687/hirepilot-agent.git`.
- [x] Build modular project directory structure in `src/hirepilot/`.
- [x] Implement pre-commit security script `scripts/check_secrets.py` and hook installer `scripts/setup_hooks.py`.
- [x] Create `.env.example` with placeholders for all configuration keys.
- [x] Create `private.example/` template structure (`profile.yaml`, `cv.md`, `writing_samples/`).
- [x] Set up `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt`.
- [x] Implement configuration loading via `pydantic-settings` (`hirepilot.config`).
- [x] Implement central structured logging (`hirepilot.logger`).
- [x] Implement LLM provider abstraction with rate limiting and fallback:
  - [x] `LLMProvider` contract and base classes.
  - [x] `SlidingWindowRateLimiter` (thread-safe and async-safe).
  - [x] `GeminiProvider` (primary, Google AI Studio free tier).
  - [x] `GroqProvider` (fallback, Groq free tier).
  - [x] `FallbackLLMProvider` (automatic retry and failover).
  - [x] `MockLLMProvider` for testing and offline development.
  - [x] Provider factory (`hirepilot.llm.factory`).
- [x] Define full relational SQLite schema using SQLAlchemy 2.0 (`hirepilot.db.models`):
  - [x] `companies`
  - [x] `people`
  - [x] `emails_found`
  - [x] `drafts`
  - [x] `sent_emails`
  - [x] `follow_ups`
  - [x] `replies`
  - [x] `blacklist`
  - [x] `runs`
  - [x] `settings`
- [x] Build database session manager and schema initialization script (`hirepilot.db.init_db`).
- [x] Write comprehensive unit test suite:
  - [x] `tests/test_config.py` (configuration and overrides)
  - [x] `tests/test_db.py` (models, relations, foreign keys, schema initialization)
  - [x] `tests/test_llm.py` (rate limiting, mock provider, sync & async fallback)
  - [x] 15/15 tests passing.
- [x] Author core documentation and agent context files:
  - [x] `AGENTS.md`
  - [x] `docs/CONTEXT.md`
  - [x] `docs/ARCHITECTURE.md`
  - [x] `docs/DECISIONS.md`
  - [x] `docs/PROGRESS.md`
  - [x] `README.md`

---

### Phase 1: Candidate Profiler & Company Discovery Engine (Upcoming)
- [ ] Implement candidate profile loader (`hirepilot.profile`):
  - [ ] Parse `private/profile.yaml` and `private/cv.md`.
  - [ ] Extract and index candidate proof points and core skills.
  - [ ] Analyze writing samples in `private/writing_samples/` to build candidate style profile.
- [ ] Implement startup discovery engines (`hirepilot.discovery`):
  - [ ] Y Combinator public startup directory scraper/API connector.
  - [ ] Product Hunt daily launch scraper/feed parser.
  - [ ] Hacker News "Who is Hiring" monthly thread parser.
  - [ ] General startup search and RSS feed collector.
- [ ] Implement deduplication and filtering against existing database records.
- [ ] Unit tests for profiler and discovery parsers with recorded/mock HTML/JSON feeds.

---

### Phase 2: Company Enrichment & Decision-Maker Discovery
- [ ] Build company enrichment module (`hirepilot.enrichment`):
  - [ ] Extract tech stack from public site assets and job postings.
  - [ ] Extract team size and stage indicators.
  - [ ] Extract recent product announcements or company missions.
- [ ] Build decision-maker discovery engine (`hirepilot.people`):
  - [ ] Parse company `/about`, `/team`, and leadership sections.
  - [ ] Inspect GitHub organization public member lists and recent repository committers.
  - [ ] Extract public press mentions and founders.
  - [ ] **Strict zero-interaction policy with LinkedIn.**
- [ ] Unit tests with fixture data.

---

### Phase 3: Email Finding, Verification & Matching Engine
- [ ] Build email pattern generator (`hirepilot.emailfinder`):
  - [ ] Generate standard corporate email variations (`first@domain`, `first.last@domain`, etc.).
- [ ] Build email verification engine:
  - [ ] DNS MX record lookup and validity checking.
  - [ ] Passive SMTP handshake validation (without message dispatch).
  - [ ] Catch-all domain detection and scoring.
- [ ] Build candidate-company matching engine:
  - [ ] Semantic matching between company tech stack/needs and candidate strengths.
  - [ ] Assign matching score (0.0 - 1.0) and qualification threshold.
- [ ] Unit tests for DNS/MX mocking and email pattern validation.

---

### Phase 4: Personalized Outreach Writer & Fact-Check Guard
- [ ] Implement personalized email drafting node (`hirepilot.writer`):
  - [ ] Generate hook from company's recent news/product.
  - [ ] Select exact matching proof point from candidate's verified profile.
  - [ ] Synthesize plain-text email under 120 words matching user style profile.
  - [ ] Frame low-pressure frictionless call to action.
- [ ] Implement Fact-Check Guard:
  - [ ] Verify every metric and claim in the draft against `private/profile.yaml`.
  - [ ] Reject any draft with unverified assertions.
- [ ] Unit tests for prompt crafting, length enforcement, and fact checking.

---

### Phase 5: Gmail Dispatcher & Deliverability Safeguards
- [ ] Implement Gmail API client (`hirepilot.sender`):
  - [ ] OAuth 2.0 flow using `private/credentials.json` and `private/token.json`.
  - [ ] Plain-text MIME message composition (`text/plain`, no HTML, no tracking).
- [ ] Implement deliverability safeguards:
  - [ ] Daily send cap enforcement with gradual warm-up schedule.
  - [ ] Jitter delay generator (180s - 600s).
  - [ ] Working-hours-only dispatcher (09:00 - 17:00, Mon-Fri).
  - [ ] Single decision maker per company enforcement.
  - [ ] Blacklist checking prior to sending.
- [ ] Unit tests with mocked Gmail API service.

---

### Phase 6: Reply Detection, Follow-up Scheduler & Bounce Handler
- [ ] Implement inbound email monitoring:
  - [ ] Periodic polling of Gmail threads for replies.
  - [ ] Inbound sentiment analysis (positive, neutral, negative, not interested).
- [ ] Implement sequence control:
  - [ ] Immediate cancellation of follow-up upon receiving any reply.
  - [ ] Single follow-up scheduler (5-7 days after initial outreach if no response).
- [ ] Bounce and blacklist handler:
  - [ ] Parse delivery failure notifications (Mailer-Daemon).
  - [ ] Automatically blacklist bounced domains and email addresses.
- [ ] Unit tests for thread matching and reply parsing.

---

### Phase 7: LangGraph Pipeline Orchestration & APScheduler Background Runner
- [ ] Define LangGraph state schema and execution graph (`hirepilot.agents`):
  - [ ] Nodes: Discovery -> Enrichment -> People -> EmailFinder -> Matching -> Writer -> FactCheck -> Gate -> Sender.
  - [ ] State persistence in SQLite for pause/resume across crashes.
- [ ] Implement APScheduler background service (`hirepilot.scheduler`):
  - [ ] Configurable cadence, active working hours execution, and graceful shutdown.
  - [ ] Kill-switch integration to immediately abort active jobs.
- [ ] Unit & end-to-end pipeline simulation tests with mock providers.

---

### Phase 8: FastAPI Backend & Streamlit Dashboard
- [ ] Build FastAPI REST API (`hirepilot.api`):
  - [ ] Endpoints for pipeline status, run triggers, draft approval/rejection, settings overrides, kill switch.
- [ ] Build Streamlit Dashboard (`hirepilot.dashboard`):
  - [ ] Overview tab (stats, runs, companies discovered, deliverability metrics).
  - [ ] Review Queue tab (inspect and edit drafts before sending).
  - [ ] Companies & People directory.
  - [ ] Outreach logs & thread timeline.
  - [ ] Configuration and kill switch controls.
- [ ] Integration tests and end-to-end manual verification.
