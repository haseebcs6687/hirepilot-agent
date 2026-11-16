# HirePilot ✈️

**Autonomous local job-outreach agent running on your PC.**

HirePilot is an intelligent, privacy-first desktop agent that autonomously discovers early-stage startups and high-growth companies, identifies the people with hiring authority, and crafts hyper-personalized cold outreach emails in your authentic voice—dispatched safely through your connected Gmail.

---

## Key Features

- **Autonomous Discovery**: Finds startups from public, legal sources (Y Combinator, GitHub, Product Hunt, RSS feeds).
- **Zero LinkedIn Scraping**: Operates completely without LinkedIn scraping, logins, or automation. 100% legal, public web sources only.
- **Decision-Maker Targeting**: Identifies founders, CEOs, CTOs, and heads of engineering directly from public company pages, commits, and press releases.
- **Deep Personalization in Your Voice**: Adapts to your writing style samples to craft punchy, authentic notes (<120 words) with specific hooks, single verified proof points, and low-pressure small asks.
- **Strict Fact-Check Guard**: Zero tolerance for hallucinations. The agent cannot invent past jobs, numbers, or achievements—every claim is strictly verified against your profile.
- **Enterprise-Grade Deliverability**:
  - Plain text emails only (no tracking pixels, no attachments, max 1 link).
  - Daily send volume caps with gradual warm-up curves.
  - Random delays between sends (180s - 600s).
  - Working-hours-only dispatch window.
  - Single contact per company rule.
  - Maximum 1 follow-up, stopped immediately if any reply is detected.
- **Zero-Cost LLM Strategy**: Uses Google Gemini 1.5 Flash (Primary) and Groq Llama 3.3 70B (Fallback) on free tier APIs with built-in sliding-window rate limiters and automatic failover.
- **Safe by Default**: `dry_run = true` ensures emails are drafted for your approval and never sent without explicit permission. Includes an instant kill-switch.
- **Local & Private**: All data is stored locally in an SQLite database on your computer. Your resume and credentials live in a git-ignored folder (`private/`) and never leave your machine.

---

## Architecture Overview

```
[Public Startup Sources] ---> [Company Discovery] ---> [Company Enrichment]
                                                             |
                                                             v
                                                   [People Finder (No LinkedIn)]
                                                             |
                                                             v
                                                   [Email Finder & MX/SMTP Check]
                                                             |
                                                             v
[Your CV & Style Profile] ---> [Voice-Matched Writer] ---> [Matching Score]
                                     |
                                     v
                           [Fact-Check Guard]
                                     |
                                     v
                              [Drafts Queue] (dry_run=true)
                                     |
                                     v
                        [Gmail Dispatcher (OAuth 2.0)]
                                     |
                                     v
                        [Reply Detection & Follow-up]
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11 - 3.13)
- Git
- Google Gemini API key (Free tier: [Google AI Studio](https://aistudio.google.com/))
- Groq API key (Free tier: [Groq Console](https://console.groq.com/))

### 2. Clone the Repository
```bash
git clone https://github.com/haseebcs6687/hirepilot-agent.git
cd hirepilot-agent
```

### 3. Create and Activate Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### 5. Install Git Pre-Commit Security Hook
Installs the automated pre-commit scanner that prevents accidental staging of secrets or files in `private/`:
```bash
python scripts/setup_hooks.py
```

### 6. Configure Environment & Profile
```bash
# Copy template configuration
cp .env.example .env

# Copy template private assets
cp -r private.example private
# On Windows PowerShell:
Copy-Item -Recurse private.example private
```

Edit `.env` to add your free Gemini and Groq API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
DRY_RUN=true
```

Edit the files inside `private/` with your genuine information:
- `private/profile.yaml`: Your verified metrics, target roles, and target companies.
- `private/cv.md`: Your markdown resume.
- `private/writing_samples/`: 1-3 short email samples representing your natural voice.

### 7. Initialize Database
```bash
python -m hirepilot.db.init_db
```

### 8. Run Test Suite
```bash
pytest -v
```

---

## Security & Privacy Architecture

This repository is designed to be public-safe:
- **`private/` is git-ignored**: Your resume, portfolio, personal credentials, and writing samples will never be committed to Git.
- **`.env` is git-ignored**: API keys and environment overrides stay strictly local.
- **Pre-commit security checker**: Scans staged changes for secret key patterns and blocked file paths prior to any commit.

---

## Documentation

- [AGENTS.md](AGENTS.md): Guide for autonomous agents and contributing engineers.
- [docs/CONTEXT.md](docs/CONTEXT.md): Detailed product requirements, deliverability rules, and compliance guardrails.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Component diagrams, data flow, and module contracts.
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural decision records (ADRs).
- [docs/PROGRESS.md](docs/PROGRESS.md): Phase checklist and implementation status.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
