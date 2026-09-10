<p align="center">
  <img src="https://img.shields.io/badge/SIH-2024-orange?style=for-the-badge" alt="SIH 2024" />
  <img src="https://img.shields.io/badge/Team-Rookie--Staff-blueviolet?style=for-the-badge" alt="Team Rookie Staff" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status" />
</p>

<h1 align="center">🛡️ PRATIKRIYA — Air-Gapped DFIR Workbench</h1>

<p align="center">
  <strong>Digital Forensics & Incident Response platform for email fraud investigation</strong><br/>
  Built for police cyber cells, government/university CERT teams, and enterprise SOC analysts.
</p>

---

## 🔍 What is PRATIKRIYA?

PRATIKRIYA is a fully **air-gapped-first** forensic workbench. Upload a suspicious `.eml` file, and the system:

1. **Parses** — Deep header extraction (Return-Path, Received chain, Message-ID, Reply-To, SPF/DKIM/DMARC via `Authentication-Results`)
2. **Traces** — Reverse-hop IP traversal to estimate true origin, with MaxMind offline geolocation (country/region/city/ISP)
3. **Detects** — Deterministic anomaly rules: forged headers, relay manipulation, typosquat domains, SPF CIDR mismatches
4. **Classifies** — Local AI engine (Qwen 2.5 via Ollama) for NLP-based urgency/impersonation scoring, BEC subtype classification, and fraud taxonomy — **zero cloud AI calls**
5. **Correlates** — Campaign graph analysis via Neo4j, cross-case TTP linking, Spamhaus DROP & Tor exit-node checks
6. **Reports** — Section 63(4)(c) BSA-compliant forensic PDF certificate (template pending examiner countersignature)

> **No internet required at runtime.** Live Hunt Mode (WHOIS/DNS) is an explicit opt-in toggle.

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS 4, Framer Motion |
| **Backend** | FastAPI (Python), Uvicorn, WebSockets |
| **AI Engine** | Ollama + Qwen 2.5:3b (fully local) |
| **Geolocation** | MaxMind GeoLite2 (offline `.mmdb`) |
| **PII Scrubbing** | Presidio + spaCy `en_core_web_lg` |
| **Graph DB** | Neo4j (campaign correlation) |
| **Maps** | React-Leaflet, CARTO basemaps |
| **PDF Export** | ReportLab |
| **Threat Intel** | Spamhaus DROP, Tor exit-node list |

---

## 📁 Project Structure

```
SIH/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/routes/         # REST endpoints (ingestion, cases)
│   │   ├── core/               # Config, WebSocket manager, Celery
│   │   ├── models/             # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   │   ├── ai_engine.py    # Ollama LLM integration
│   │   │   ├── forensics.py    # Header analysis, anomaly rules
│   │   │   ├── graph.py        # Neo4j campaign correlation
│   │   │   ├── ingestion.py    # .eml parsing pipeline
│   │   │   ├── live_hunt.py    # WHOIS/DNS (opt-in, online only)
│   │   │   └── pdf_export.py   # BSA Section 63 PDF generation
│   │   └── utils/
│   │       └── geoip.py        # MaxMind offline geolocation
│   ├── requirements.txt
│   └── test_data/              # Fixture .eml files for testing
│
├── dfir-frontend/              # Next.js 15 frontend
│   ├── app/                    # App router pages
│   │   └── dashboard/          # Main investigation dashboard
│   ├── components/
│   │   ├── certificate/        # BSA PDF certificate UI
│   │   ├── dashboard/          # Dashboard widgets
│   │   ├── forensics/          # Forensic analysis panels
│   │   ├── intelligence/       # Threat intelligence views
│   │   ├── landing/            # Landing page
│   │   ├── layout/             # Dashboard shell, nav
│   │   └── ui/                 # Shared UI primitives
│   ├── services/               # API client layer
│   ├── types/                  # TypeScript type definitions
│   └── package.json
│
├── .env.example                # Environment variable template
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend |
| Node.js | 20+ LTS | Frontend |
| Ollama | Latest | Local AI |
| Docker | Latest | Neo4j + Redis (optional) |
| Git | Latest | Version control |

### 1. Clone the Repository

```bash
git clone https://github.com/advaitjha111-spec/Rookie-Staff--SIH.git
cd Rookie-Staff--SIH
```

### 2. Environment Setup

```bash
# Copy environment templates and fill in your values
cp .env.example .env
cp dfir-frontend/.env.example dfir-frontend/.env.local
```

**Required variables** (see `.env.example`):
- `MAXMIND_ACCOUNT_ID` / `MAXMIND_LICENSE_KEY` — [Free signup at MaxMind](https://www.maxmind.com/en/geolite2/signup)
- `NEO4J_PASSWORD` — Your Neo4j instance password
- `NEXT_PUBLIC_CARTO_API_KEY` — CARTO basemap key for map tiles

### 3. One-Time Downloads (requires internet — do before going air-gapped)

```bash
# Pull the local LLM model
ollama pull qwen2.5:3b

# Download MaxMind GeoLite2 databases (replace YOUR_LICENSE_KEY)
curl -o GeoLite2-City.tar.gz \
  "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
curl -o GeoLite2-ASN.tar.gz \
  "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
# Extract .mmdb files into the project

# Threat intel lists (no account needed)
curl -o spamhaus_drop.txt https://www.spamhaus.org/drop/drop.txt
curl -o tor_exit_nodes.txt https://check.torproject.org/torbulkexitlist

# spaCy model for PII detection
python -m spacy download en_core_web_lg
```

### 4. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Frontend Setup

```bash
cd dfir-frontend
npm install
```

### 6. Start Services

```bash
# Terminal 1 — Start Ollama
ollama serve

# Terminal 2 — (Optional) Start Neo4j & Redis via Docker
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword neo4j:latest
docker run -d --name redis -p 6379:6379 redis:latest

# Terminal 3 — Start Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 4 — Start Frontend
cd dfir-frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest` | Upload `.eml` file for forensic analysis |
| `GET` | `/api/v1/cases` | List all investigated cases |
| `GET` | `/api/v1/cases/{hash}` | Get case details by content hash |
| `GET` | `/api/v1/cases/{hash}/export` | Download BSA Section 63 PDF |
| `WS` | `/api/v1/ws/alerts` | Real-time high-risk email alerts |
| `GET` | `/health` | Health check |

---

## 🔐 Security

- **Air-gapped by default** — no outbound network calls in standard mode
- **PII scrubbing** — Presidio + spaCy strips financial/ID data before LLM processing
- **No cloud AI** — all inference runs on local Ollama; zero data exfiltration risk
- **Environment secrets** — all credentials in `.env` (gitignored), never hardcoded
- **BSA compliance** — PDF exports follow Section 63(4)(c) certificate template format

---

## 📋 Feature Coverage (SIH Problem Statement)

| # | Requirement | Status |
|---|------------|--------|
| 1 | NLP urgency/impersonation analysis | ✅ |
| 2 | Phishing indicators detection | ✅ |
| 3 | AI classification (legit/suspicious/phishing/fraud) | ✅ |
| 4 | BEC subtype identification (4 types) | ✅ |
| 5 | Deep header parsing | ✅ |
| 6 | Routing anomaly detection | ✅ |
| 7 | Authorized vs suspicious infra validation | ✅ |
| 8 | Origin IP extraction | ✅ |
| 9 | Geolocation (country/region/city/ISP) | ✅ |
| 10 | VPN/TOR/botnet correlation | ✅ |
| 11 | Domain intelligence (Live Hunt Mode) | ✅ |
| 12 | Threat-intel/campaign correlation | ✅ |
| 13 | Graph-based relationship analysis | ✅ |
| 14 | Confidence-based assessment | ✅ |
| 15 | 4-way infrastructure attribution | ✅ |
| 16 | Real-time high-risk alerts | ✅ |
| 17 | Analyst dashboard | ✅ |
| 18 | Structured forensic/legal report | ✅ |
| 19 | Searchable case management | ✅ |

---

## 🏗️ Deployment

### Frontend (Vercel)

The Next.js frontend can be deployed to Vercel:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from the frontend directory
cd dfir-frontend
vercel --prod
```

Set these environment variables in Vercel Dashboard → Settings → Environment Variables:
- `NEXT_PUBLIC_API_URL` — your backend URL
- `NEXT_PUBLIC_CARTO_API_KEY` — your CARTO basemap API key

### Backend

The FastAPI backend requires a server with Python 3.11+ and Ollama. Deploy via:
- **Docker** (recommended for production)
- **Any VPS** with `uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## 👥 Team Rookie Staff

Built for **Smart India Hackathon (SIH) 2024**.

---

## 📄 License

This project is developed as part of SIH 2024. All rights reserved by Team Rookie Staff.
