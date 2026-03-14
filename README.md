# REDS — Real Estate AI Domination System
### AgAI_5 | DataWebify Agentic AI Portfolio

**Live System:** [reds.datawebify.com](https://reds.datawebify.com)
**Portfolio:** [datawebify.com/projects/reds_agent](https://datawebify.com/projects/reds_agent)
**Built by:** Muhammad Umair — Agentic AI Specialist & Enterprise Consultant

---

## The Problem

Real estate acquisition teams spend $6,000–$10,000/month on 2–3 agents who manually:
- Browse Craigslist, Zillow, and FSBO sites for motivated sellers
- Copy contact details into a CRM by hand
- Send individual SMS and email follow-ups
- Check for replies and update records manually

The result: slow lead response times, inconsistent follow-up, and high labor costs per deal.

---

## The Solution

REDS is a fully autonomous, closed-loop lead generation and outreach system that:

- Scrapes motivated seller listings from Craigslist FSBO 24/7
- Uses Claude AI to score each lead for distress signals (0–100)
- Stores qualified leads in Supabase with full deduplication
- Creates contacts in GoHighLevel CRM automatically
- Fires SMS and email outreach sequences on contact creation
- Monitors GHL conversations for seller replies
- Exposes a real-time FastAPI dashboard for full pipeline visibility

Zero manual prospecting. Automated follow-up on 500+ leads/day. Sub-5-second CRM updates.

---

## Business Impact

| Metric | Before | After | Change |
|---|---|---|---|
| Lead prospecting | 3 agents, 8hrs/day | Fully automated | -100% labor |
| Cost per lead | $12.00 (human) | $0.08 (AI) | -99% |
| CRM update time | 15–30 minutes | Under 5 seconds | -99% |
| Daily lead capacity | 40–60 leads | 500+ leads | +800% |
| Monthly labor cost | $6,000–$10,000 | ~$50 AI API cost | -99% |
| Follow-up consistency | Inconsistent | 100% automated | Guaranteed |

**Project value: $15,000–$40,000 per engagement**

---

## System Architecture

```
Craigslist FSBO Listings
        |
        v
Playwright Browser Agent
(Scrapes title, price, description, location, contact)
        |
        v
Claude AI Extraction Pipeline
(Structures raw text, scores distress 0-100, extracts signals)
        |
        v
Supabase PostgreSQL
(Deduplication, lead storage, status tracking)
        |
        v
GoHighLevel CRM
(Contact creation, REDS_Lead tag, AI analysis note)
        |
        v
GHL Workflow Engine
(Contact Tag trigger, SMS sequence, Wait, Email sequence)
        |
        v
Reply Monitor
(Polls GHL conversations, detects inbound replies, updates Supabase)
        |
        v
FastAPI Dashboard
(REST API: /leads, /metrics, /health)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Browser Automation | Playwright (Chromium) |
| AI / LLM | Claude claude-sonnet-4-20250514 via Anthropic API |
| CRM | GoHighLevel API v2 |
| Database | Supabase (PostgreSQL) |
| API Layer | FastAPI + Uvicorn |
| Deployment | Docker + Railway |
| Config | pydantic-settings, python-dotenv |
| Logging | structlog (JSON format) |
| HTTP Client | httpx (async) |

---

## Project Structure

```
AgAI_5_REDS/
├── app/
│   ├── agents/
│   │   └── craigslist_scraper.py     # Playwright FSBO scraper
│   ├── pipeline/
│   │   ├── lead_extractor.py         # Claude AI extraction + scoring
│   │   ├── lead_store.py             # Supabase storage + dedup
│   │   └── reply_monitor.py          # GHL conversation polling
│   ├── crm/
│   │   ├── ghl_client.py             # GoHighLevel API v2 client
│   │   └── contact_pusher.py         # Lead to CRM push service
│   ├── api/
│   │   ├── main.py                   # FastAPI app + middleware
│   │   └── routes/
│   │       ├── health.py             # GET /health
│   │       ├── leads.py              # GET /leads, /leads/{id}
│   │       └── metrics.py            # GET /metrics
│   ├── models/
│   │   └── lead.py                   # Pydantic data models
│   └── utils/
│       ├── config.py                 # Centralized settings
│       └── logger.py                 # Structured JSON logging
├── tests/
│   ├── test_ghl_connection.py
│   ├── test_scraper.py
│   ├── test_pipeline.py
│   ├── test_storage.py
│   ├── test_ghl_push.py
│   └── test_reply_monitor.py
├── Dockerfile
├── railway.toml
├── requirements.txt
├── setup.py
├── main.py
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | System health check |
| GET | `/leads` | All leads (optional `?status=` filter) |
| GET | `/leads/{id}` | Single lead by UUID |
| GET | `/metrics` | Full pipeline metrics and business impact |
| GET | `/docs` | Interactive Swagger UI |

### Example: GET /metrics

```json
{
  "summary": {
    "total_leads": 500,
    "leads_last_24h": 47,
    "reply_rate_pct": 8.3,
    "qualification_rate_pct": 34.2
  },
  "pipeline": {
    "raw": 12,
    "qualified": 171,
    "contacted": 298,
    "replied": 14,
    "dead": 5
  },
  "business_impact": {
    "agent_hours_saved_per_week": 125.0,
    "estimated_cost_per_lead_usd": 0.08,
    "human_cost_per_lead_usd": 12.00,
    "cost_reduction_pct": 99
  }
}
```

---

## Distress Scoring System

Claude AI evaluates each listing and assigns a distress score from 0 to 100 based on detected signals:

| Signal | Points |
|---|---|
| "must sell", "motivated seller" | +25 |
| "price reduced", "below appraisal" | +20 |
| "divorce", "estate sale", "probate" | +25 |
| "foreclosure", "pre-foreclosure" | +30 |
| "relocating", "job transfer" | +15 |
| "vacant", "empty property" | +15 |
| "as-is", "needs work", "fixer upper" | +20 |
| "cash only", "no realtor", FSBO | +10 |
| Owner finance | +10 |
| Days on market over 60 | +15 |
| Asking below $150,000 | +10 |

Leads scoring 30+ are qualified and pushed to GHL. Leads below 30 are filtered out.

---

## Local Setup

### Prerequisites
- Python 3.12
- Docker Desktop
- GoHighLevel account
- Supabase account
- Anthropic API key

### Installation

```bash
git clone https://github.com/umair801/reds_agent.git
cd reds_agent

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
pip install -e .
playwright install chromium
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=your_key
GHL_API_KEY=your_key
GHL_LOCATION_ID=your_location_id
GHL_BASE_URL=https://services.leadconnectorhq.com
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
APP_ENV=development
LOG_LEVEL=INFO
PORT=8080
```

### Supabase Schema

Run this in your Supabase SQL Editor:

```sql
CREATE TABLE leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    scraped_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    asking_price INTEGER,
    days_on_market INTEGER,
    distress_score INTEGER DEFAULT 0,
    distress_signals JSONB DEFAULT '[]',
    motivation_summary TEXT,
    status TEXT DEFAULT 'raw',
    ghl_contact_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_leads_source_url ON leads(source_url);
CREATE INDEX idx_leads_status ON leads(status);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_insert" ON leads FOR INSERT WITH CHECK (true);
CREATE POLICY "allow_select" ON leads FOR SELECT USING (true);
CREATE POLICY "allow_update" ON leads FOR UPDATE USING (true);
```

### Run Locally

```bash
uvicorn app.api.main:app --reload --port 8080
```

Visit `http://localhost:8080/docs`

---

## Docker Deployment

```bash
docker build -t reds_agent .
docker run --env-file .env -p 8080:8080 reds_agent
```

---

## Railway Deployment

1. Push to GitHub
2. Connect repo to Railway
3. Add all `.env` variables in Railway Variables tab
4. Railway auto-deploys via Dockerfile
5. Set custom domain: `reds.datawebify.com`

---

## GHL Workflow Configuration

Trigger: **Contact Tag** — fires when `reds_lead` tag is added

Sequence:
1. Send SMS — initial cash offer inquiry
2. Wait 1 day
3. Send Email — follow-up with offer details
4. Wait 2 days
5. Send SMS — second touch

The `reds_lead` tag is automatically applied by the system on every contact created.

---

## Testing

Run each test in order to verify the full pipeline:

```bash
python tests/test_ghl_connection.py    # Verify GHL API
python tests/test_scraper.py           # Verify Playwright scraper
python tests/test_pipeline.py          # Verify AI extraction
python tests/test_storage.py           # Verify Supabase storage
python tests/test_ghl_push.py          # Verify CRM push
python tests/test_reply_monitor.py     # Verify reply detection
```

---

## Portfolio Context

REDS is Project 5 of 50 in the DataWebify Agentic AI portfolio.

| Project | System | Status |
|---|---|---|
| AgAI_1 | Enterprise WhatsApp Automation | Live |
| AgAI_2 | B2B Lead Generation System | Live |
| AgAI_3 | Enterprise AI Support Agent | Live |
| AgAI_4 | RAG Knowledge Base Agent | Live |
| AgAI_5 | REDS — Real Estate AI Domination System | Live |

---

## Contact

**Muhammad Umair**
Agentic AI Specialist and Enterprise Consultant
[datawebify.com](https://datawebify.com)

*Replacing $6,000–$10,000/month acquisition teams with autonomous AI agents.*
