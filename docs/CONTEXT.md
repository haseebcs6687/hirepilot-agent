# HirePilot Context & Comprehensive Specification

## 1. Executive Summary & Product Goal

HirePilot is an autonomous, local job-outreach agent engineered to run on the user's personal workstation. It transforms the job hunt from a manual, exhausting chore into an intelligent, background process.

The system autonomously:
1. **Discovers** startups and high-growth technology companies matching target criteria (stages, tech stack, locations).
2. **Finds** key decision-makers who hold hiring power (Founders, CEO, CTO, VP Engineering, Head of Engineering, Technical Recruiters).
3. **Identifies and Verifies** direct email addresses using open DNS, MX records, and mail exchange validation.
4. **Calculates a Match Score** between candidate profile strengths and company needs.
5. **Crafts Hyper-Personalized Emails** in the candidate's authentic writing style.
6. **Enforces Strict Truth-Grounding** via an automated fact-check guard (never halluncinating credentials or claims).
7. **Dispatches Emails** directly from the candidate's connected Gmail account within strict deliverability constraints.
8. **Tracks Inbound Replies** and automatically halts follow-up sequences.
9. **Provides Full Visibility** through a local Streamlit dashboard and FastAPI backend.

---

## 2. Hard Architectural & Tooling Constraints

| Component | Selected Technology | Constraints & Rationale |
| :--- | :--- | :--- |
| **Primary LLM** | Google Gemini API (Free Tier) | 15 RPM rate-limited, free tier API key. |
| **Fallback LLM** | Groq API (Free Tier) | 30 RPM rate-limited, failover on 429/timeout/outage. |
| **Orchestrator** | LangGraph | State machine persistence across nodes and crashes. |
| **Backend API** | FastAPI + Uvicorn | Async REST endpoints, health checks, control hooks. |
| **Background Runner** | APScheduler | Interval/cron scheduling, timezone-aware execution. |
| **Persistence** | SQLite 3 + SQLAlchemy 2.0 | Zero-setup local relational store with FK cascades. |
| **User Interface** | Streamlit | Lightweight local reactive dashboard. |
| **Email Transport** | Gmail API (OAuth 2.0) | Dispatched from user's personal address; no SMTP relays. |

---

## 3. Strict Legal & Compliance Guardrails

> [!CAUTION]
> **ABSOLUTELY NO LINKEDIN SCRAPING**
> - The agent shall NEVER scrape LinkedIn public or private pages.
> - The agent shall NEVER automate LinkedIn logins, use headless browser sessions against LinkedIn, or interact with unofficial LinkedIn APIs.
> - Sourcing is restricted to legal, public web sources:
>   - Company websites (`/about`, `/team`, `/jobs`, `/careers`).
>   - GitHub public profiles, commits, and organization member lists.
>   - Public startup directories (e.g. Y Combinator public startup lists, Product Hunt RSS).
>   - Public press releases, Hacker News "Who is Hiring" threads, and tech news.
>   - DNS records and MX host lookups.

---

## 4. Email Generation & Voice Guidelines

Outreach emails must read like genuine human notes from a thoughtful engineer, never sounding like automated AI spam or marketing copy.

### Mandatory Email Rules:
1. **Format**: Strictly Plain Text (`text/plain`).
2. **Length**: Maximum 120 words (concise, respectful of time).
3. **Tracking**: Absolutely **zero** tracking pixels, zero web beacons, zero redirect tracking links.
4. **Attachments**: Absolutely **zero** attachments (resumes are linked if requested, not attached).
5. **Links**: At most **one** link (candidate portfolio or GitHub profile).
6. **First Line Hook**: An authentic, specific observation about what the company built or recently announced.
7. **Proof Point**: Exactly one verified, metrics-driven accomplishment from the candidate's profile.
8. **Call to Action (CTA)**: A low-pressure, frictionless small ask (e.g., "Are you looking to expand your core backend team right now? Either way, keep up the great work.").
9. **Style Profile**: The LLM writer adapts vocabulary, sentence rhythm, and closing from the candidate's writing samples in `private/writing_samples/`.

---

## 5. Deliverability & Anti-Spam Safeguards

To protect sender domain reputation and ensure maximum inbox placement:

1. **Daily Send Cap**: Starts at 5 emails/day with a gradual warm-up curve (incrementing by 1-2 emails per week up to a max cap of 20/day).
2. **Random Jitter Delays**: Sends spaced randomly between 180 and 600 seconds apart.
3. **Working Hours Only**: Emails are dispatched strictly during standard business hours (e.g. 09:00 - 17:00) on weekdays (Monday through Friday) in the target's or user's local timezone.
4. **Pre-Send Verification**: Every email address undergoes DNS MX lookup and passive validation prior to drafting or sending. Invalid or risky domains are rejected.
5. **Single Decision Maker per Company**: Exactly one person is contacted per company. Never spam multiple employees at the same organization.
6. **Single Follow-up Rule**: Maximum of one gentle follow-up email, sent 5-7 days after initial outreach if no response has been received.
7. **Immediate Stop Sequence on Inbound Reply**: Inbound email threads are periodically checked. Any inbound reply (positive, negative, or neutral) instantly cancels any scheduled follow-up.
8. **Domain Blacklist & Bounce Guard**: Any hard bounce, unsubscribe request, or manual block immediately blacklists the domain and email address from future outreach.
9. **Fact-Check Guard**: Before any draft is marked ready for dispatch, an independent verification node compares every assertion against the candidate's verified profile facts (`private/profile.yaml`). Any hallucination causes immediate rejection.

---

## 6. Safety Modes & Kill Switch

- **`dry_run = true` (Default)**: In this mode, the entire pipeline executes (discovering companies, finding people, crafting personalized emails), but drafts are stored in the database for user inspection. Nothing is sent.
- **`autopilot = false` (Default)**: Requires explicit user activation via the dashboard or configuration to run unattended.
- **`kill_switch`**: A global circuit breaker. When active, all background workers, schedulers, and network dispatches immediately terminate.

---

## 7. Security Architecture for Public Repositories

Because this repository may be published publicly, sensitive candidate data and credentials must never touch version control:
- `.gitignore` created first, explicitly excluding `.env`, `*.db`, `private/`, `credentials*.json`, `token*.json`, `logs/`, `data/`.
- Candidate CV, writing samples, and profile live strictly in `private/`.
- Public templates live in `private.example/` and `.env.example`.
- Automated security script `scripts/check_secrets.py` and pre-commit git hooks block any commit containing private data, API keys, or secret tokens.
