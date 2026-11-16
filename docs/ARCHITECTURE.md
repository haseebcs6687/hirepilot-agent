# HirePilot System Architecture

```
+-----------------------------------------------------------------------------------------+
|                                        HIREPILOT                                        |
|                         Autonomous Local Job-Outreach Engine                            |
+-----------------------------------------------------------------------------------------+

   [ Candidate Data (private/) ]        [ Config (.env) ]       [ Legal Public Sources ]
     - profile.yaml                       - GEMINI_API_KEY        - YC / ProductHunt
     - cv.md                              - GROQ_API_KEY          - GitHub Public APIs
     - writing_samples/                   - Safeguard Caps        - Company Sites / DNS
           |                                     |                         |
           v                                     v                         v
+---------------------+               +---------------------+   +---------------------+
| Candidate Profiler  |               |  Pydantic Settings  |   | Discovery Engines   |
| & Style Extractor   |               |   & Config Engine   |   | (YC, HN, Web Sinks) |
+---------------------+               +---------------------+   +---------------------+
           |                                     |                         |
           +-----------------+                   |                         |
                             |                   v                         v
                             |        +-----------------------------------------------+
                             |        |             LangGraph Agent Pipeline          |
                             |        |  (Stateful Multi-Step Outreach State Machine) |
                             |        +-----------------------------------------------+
                             |                                 |
                             |         [1] Discover Companies  v
                             |             -> Save to SQLite (status: discovered)
                             |         [2] Enrich Tech & Funding Signals
                             |             -> Tech stack, team size, recent news
                             |         [3] Find Decision Makers
                             |             -> Founders, CTO, VP Eng (No LinkedIn)
                             |         [4] Find & Verify Emails
                             |             -> MX check, pattern generation, SMTP check
                             |         [5] Compute Matching Score
                             |             -> Evaluate candidate fit (0.0 - 1.0)
                             |         [6] Synthesize Outreach in Candidate Voice
                             +---------->  Hook + 1 Proof Point + Frictionless Ask
                                       [7] Fact-Check Verification Guard
                                           -> Zero hallucinations; truth validation
                                       [8] Dispatch via Sender (Gmail API)
                                           -> Respects daily cap, warm-up, delay
                                       [9] Reply Monitoring & Single Follow-Up
                                           -> Stop sequence if reply detected
                                                       |
                                                       v
+-----------------------------------------------------------------------------------------+
|                                    PERSISTENCE LAYER                                    |
|                       SQLite Database (SQLAlchemy 2.0 ORM Models)                       |
|   companies | people | emails_found | drafts | sent_emails | follow_ups | blacklist...  |
+-----------------------------------------------------------------------------------------+
           ^                                                               ^
           |                                                               |
+---------------------+                                         +---------------------+
|   FastAPI Backend   | <-------------------------------------> | Streamlit Dashboard |
| (REST / Job Control)|                                         | (Review & Monitor)  |
+---------------------+                                         +---------------------+
```

---

## 1. Pipeline Stages & Data Flow

The outreach lifecycle is orchestrated by **LangGraph** with checkpointed state stored locally in SQLite:

```
[Discovery Engine]
       |
       v  (New Companies)
[Enrichment Engine] ------> Fetches tech stack, funding, team size from public sites/APIs
       |
       v  (Enriched Company)
[People Finder] ----------> Identifies CTOs/Founders/Eng Leaders from `/about`, GitHub, Press
       |
       v  (Decision Maker)
[Email Verifier] ---------> Generates email patterns ({first}@{domain}), validates MX records
       |
       v  (Verified Email)
[Matching Engine] --------> Evaluates candidate profile alignment against company needs
       |
       v  (Score >= Threshold)
[Voice Writer] -----------> Generates personalized plain-text draft (<120 words)
       |
       v  (Candidate Draft)
[Fact-Check Guard] -------> Audits every claim against `private/profile.yaml` facts
       |
       +--- [Failed Fact Check] ----> Re-draft or Flag for Manual Review
       |
       v  [Passed Fact Check]
[Approval Gate] ----------> If `dry_run=True`: Save to DB Drafts (Await User Review)
       |                    If `dry_run=False` and `autopilot=True`: Enqueue for Dispatch
       v
[Gmail Dispatcher] -------> Delivers via Gmail API respecting daily caps and random delays
       |
       v
[Reply & Follow-up Monitor] Checks inbox; halts sequence on reply, or schedules 1 follow-up
```

---

## 2. Component Descriptions

### 2.1 LLM Abstraction Layer (`hirepilot.llm`)
- **`LLMProvider`**: Common abstract base class exposing `complete()` and `complete_async()`.
- **`GeminiProvider`**: Primary provider using Google Gemini free tier API. Built-in sliding-window rate limiter (15 RPM).
- **`GroqProvider`**: Fallback provider using Groq free tier API (30 RPM).
- **`FallbackLLMProvider`**: Manages seamless failover. If Gemini returns 429 (ResourceExhausted), 5xx server errors, or network timeouts, requests automatically route to Groq without interrupting the pipeline.
- **`SlidingWindowRateLimiter`**: Thread-safe and async-safe request tracker enforcing provider RPM limits.

### 2.2 Discovery Engine (`hirepilot.discovery`)
- Scrapes structured startup directories (e.g. Y Combinator public company API/directories, Product Hunt public feeds, Hacker News "Who is Hiring" threads).
- Extracts legal company metadata without requiring browser logins or paywalled databases.

### 2.3 Enrichment Engine (`hirepilot.enrichment`)
- Analyzes company landing pages and public repositories to determine:
  - Engineering tech stack (e.g. Python, FastAPI, React, PostgreSQL).
  - Business stage (Seed, Series A, Series B).
  - Estimated team size.
  - Recent milestone or public launch announcement.

### 2.4 People Finder (`hirepilot.people`)
- Focuses on discovering high-leverage hiring decision makers:
  - Technical: Co-Founder, CTO, VP of Engineering, Head of Engineering.
  - Sourcing: Company team page, GitHub organization contributors, press releases.
  - **Zero interaction with LinkedIn.**

### 2.5 Email Finder & Verifier (`hirepilot.emailfinder`)
- Generates standard professional email permutations:
  - `{first}@{domain}`, `{first}.{last}@{domain}`, `{f}{last}@{domain}`.
- Performs DNS query for MX records to verify active mail exchanges.
- Connects to SMTP socket (without dispatching mail) to check deliverability and catch-all status where supported.

### 2.6 Personalization Writer & Fact-Check Guard (`hirepilot.writer`)
- Reads user writing samples from `private/writing_samples/` to adopt the user's authentic voice, tone, and brevity.
- Selects the single best proof point from `private/profile.yaml` that matches the company's tech stack or challenges.
- **Fact-Check Guard**: Audits the draft. If the draft contains numbers or claims not present in `private/profile.yaml`, it fails the check and prevents dispatch.

### 2.7 Sender & Deliverability Safeguards (`hirepilot.sender`)
- Interacts with Gmail REST API using OAuth 2.0 refresh tokens.
- Enforces:
  - Strict daily volume caps (warm-up starting at 5/day).
  - Random jitter delays (180s - 600s).
  - Working hours schedule (09:00 - 17:00, Mon-Fri).
  - Deduplication: exactly one email per company domain.

### 2.8 Database Layer (`hirepilot.db`)
- Relational SQLite database using SQLAlchemy 2.0 ORM.
- Tables: `companies`, `people`, `emails_found`, `drafts`, `sent_emails`, `follow_ups`, `replies`, `blacklist`, `runs`, `settings`.
- Enforces foreign key constraints with `PRAGMA foreign_keys=ON;`.

### 2.9 Dashboard & Control Interface (`hirepilot.dashboard` & `hirepilot.api`)
- **FastAPI**: REST endpoints for trigger management, kill switch toggle, draft updates, and status checks.
- **Streamlit**: Visual interface showing company discovery metrics, pending drafts review queue, sent email logs, and deliverability stats.
