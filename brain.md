# BRAIN.md

## ROLE

You are the build agent for **an Air-Gapped-first Digital Forensics & Incident Response (DFIR) workbench for email fraud investigation**, built to satisfy all 22 named requirements of the source problem statement. You are not building a spam filter. You are building an investigator's tool: upload one suspicious `.eml`, and the system forensically dissects it, isolates its true origin, runs deterministic anomaly rules, runs a local AI for behavioral/intent classification, correlates it against a campaign graph, and produces a legally-framed evidence report.

Primary users, referenced in all UI copy: police cyber cells, government/university CERT teams, enterprise SOC analysts.

This is a hackathon build with a large feature surface. Optimize for "works end-to-end live on stage." A working MVP beats a broken showcase — when time is short, cut per Section 9, never silently.

---

## STEP 0 — ENVIRONMENT & DEPENDENCY SETUP (do this before writing any application code)

### 0.A System-level software to install

| Software | Needed for | Skip if... |
|---|---|---|
| Python 3.11+ | Backend | Never — always required |
| Node.js 20+ (LTS) + npm | Frontend | Never — always required |
| Git | Version control | Never — always required |
| Ollama | Local LLM | Never — always required |
| Docker Desktop | Neo4j + Redis containers | You've cut Neo4j and Celery per Section 9 — then skip Docker entirely |

### 0.B Accounts / credentials — the ONLY one you need

This entire project needs exactly **one** external account: **MaxMind**, free, at `maxmind.com/en/geolite2/signup`, to generate a license key for downloading GeoLite2. That's it. There is deliberately no OpenAI/Anthropic/Google API key anywhere in this project — the whole pitch depends on zero cloud AI calls. If you ever find yourself typing a cloud LLM API key into this codebase, stop — that violates Non-Negotiable Rule #1/#5.

### 0.C One-time downloads (do this on a working internet connection, before the event, not at the venue)

```bash
# Local LLM
ollama pull qwen2.5:3b

# MaxMind GeoLite2 databases (replace YOUR_LICENSE_KEY after signup)
curl -o GeoLite2-City.tar.gz "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
curl -o GeoLite2-ASN.tar.gz  "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
# extract the .mmdb files from each tarball into /data/geo/

# Spamhaus DROP list (no account needed)
curl -o spamhaus_drop.txt https://www.spamhaus.org/drop/drop.txt

# Tor exit-node list (no account needed)
curl -o tor_exit_nodes.txt https://check.torproject.org/torbulkexitlist

# spaCy model for Presidio — CONFIRMED primary PII method for this build, install always
python -m spacy download en_core_web_lg
```

### 0.D Python dependencies (backend)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install fastapi "uvicorn[standard]" python-multipart pydantic python-dotenv requests
pip install authres Levenshtein maxminddb geoip2
pip install python-whois dnspython              # Live Hunt Mode only — skip if Air-Gapped-only build
pip install presidio-analyzer presidio-anonymizer spacy   # CONFIRMED primary — install always, do not skip
pip install reportlab
pip install neo4j                                # skip if using SQLite per the cut list
pip install celery redis                         # skip if running synchronously per the cut list

pip freeze > requirements.txt
```

### 0.E Node/frontend dependencies

```bash
npx create-next-app@latest dfir-frontend --typescript --tailwind --app
cd dfir-frontend
npm install reactflow                # skip if graph visual is cut
npm install react-leaflet leaflet
npm install -D @types/leaflet
npx shadcn@latest init
npx shadcn@latest add table badge card
```

### 0.F Docker services (skip entirely if Neo4j/Celery are cut per Section 9)

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/yourpassword neo4j:latest
docker run -d --name redis -p 6379:6379 redis:latest
```

### 0.G Environment variables

Create `.env` (never committed — see `.gitignore` below) and a tracked `.env.example` with the same keys, empty:

```
MAXMIND_ACCOUNT_ID=your_account_id
MAXMIND_LICENSE_KEY=your_license_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yourpassword
OLLAMA_HOST=http://localhost:11434
```

### 0.H Git setup — do this before writing a single line of app code

```bash
git init
# create .gitignore FIRST, before your first add
git add .gitignore .env.example
git commit -m "chore: project scaffold, gitignore, env template"
git add .
git commit -m "chore: initial dependency setup"
```

**`.gitignore` — create this file before your first commit:**

```
# Python
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
build/
dist/

# Node / Next.js
node_modules/
.next/
out/
npm-debug.log*

# Environment & secrets — never commit real keys
.env
.env.local
.env.*.local

# Downloaded reference data — large or refreshable, don't bloat the repo
*.mmdb
spamhaus_drop.txt
tor_exit_nodes.txt

# Runtime case data — never commit real uploaded/investigated emails
/uploads/
/data/cases/

# Databases
*.db
*.sqlite3
dump.rdb
/neo4j-data/

# Generated legal PDF exports — case-specific, regenerable
/exports/*.pdf

# OS / editor noise
.DS_Store
Thumbs.db
.vscode/
.idea/

# Logs
*.log
```

**One deliberate exception:** do NOT blanket-ignore `*.eml`/`*.msg`. Keep your three test-fixture emails (legitimate, obvious phishing, spoofed-BEC — see Section 11) in a tracked folder like `/test_data/` so they travel with the repo. Only the *runtime* `/uploads/` and `/data/cases/` directories — real investigated evidence — are ignored.

---

## NON-NEGOTIABLE RULES

1. **Air-Gapped Mode is the default.** The system must run fully offline out of the box. Live Hunt Mode (WHOIS/DNS lookups) is an explicit, visibly-labeled opt-in toggle — never silently active.
2. **Never claim certainty on origin tracing.** Received-header chains can be incomplete or spoofed. Every origin-IP result ships with a confidence indicator. Use "estimated" / "most likely" — never "confirmed" or "pinpointed."
3. **Do not re-implement SPF/DKIM/DMARC validation from scratch where the header already has it.** Parse `Authentication-Results` first; use the `authres` library for direct validation only as a fallback, and mark those results lower-confidence.
4. **Never claim the exported PDF is "court-admissible" on its own.** Section 63(4)(c) of the Bharatiya Sakshya Adhiniyam, 2023 requires a certificate signed by BOTH the device custodian and an independent expert, plus the record's hash. Label the export: **"Section 63(4)(c)-compliant certificate template — pending examiner countersignature."** Pre-fill Part A (technical details + hash); leave Part B (expert sign-off) blank.
5. **PII never leaves the process boundary.** Presidio scrubs financial/ID data from the email body before it reaches the LLM. No email content goes anywhere except the local Ollama instance on localhost.
6. **Never fabricate "past case" data as if real.** Seeded demo cases in Neo4j/SQLite must be clearly labeled as demo data in code comments and in the UI.
7. **Never silently drop a planned feature.** If a phase is infeasible in the time available, say so explicitly and move to the next item on the cut list (Section 9).
8. **A retention-policy UI control is not a feature unless it's enforced.** Any "retention timeframe" setting must be backed by an actual scheduled purge job — a dropdown with no logic behind it does not satisfy the requirement.

---

## FEATURE COVERAGE CHECKLIST (all 22 PS requirements → build location)

| # | Requirement | Where it's built |
|---|---|---|
| 1 | NLP urgency/impersonation analysis | AI Engine (Section 6) |
| 2 | Phishing indicators: spoofed sender, deceptive domains, attachments, malicious links, obfuscated URLs | Ingestion IoC Extractor (Section 4.C — **patched in this update**) + Typosquat Radar (Section 5.C) |
| 3 | AI classify legit/suspicious/impersonated/phishing/fraud | AI Engine fraud_taxonomy field |
| 4 | BEC subtypes (4) | AI Engine bec_subtype field |
| 5 | Header deep-parse (Return-Path, Received, Message-ID, Reply-To, SPF/DKIM/DMARC) | Ingestion Engine (Section 4) |
| 6 | Routing anomaly detection (forged fields, relay manipulation) | 4-Point Anomaly Rules (Section 5.B) |
| 7 | Authorized vs suspicious infra validation | SPF CIDR check (Section 5.A) |
| 8 | Origin IP extraction | Reverse-Hop Traversal (Section 5.A) |
| 9 | Geolocation (country/region/city/ISP/hosting/proxy) | MaxMind offline (Section 5.C) |
| 10 | VPN/TOR/botnet/cloud-hosted correlation | Tor list + Spamhaus DROP + ASN hosting flag (Section 5.C) |
| 11 | Domain intelligence (WHOIS/DNS/MX/registrar/hosting fingerprint) | Live Hunt Mode (Section 5.C) |
| 12 | Threat-intel/blacklist/campaign correlation | Spamhaus DROP + Neo4j (Section 7) |
| 13 | Graph-based relationship analysis | Neo4j schema (Section 7) |
| 14 | Confidence-based investigative assessment | technical_justification field + score fields throughout |
| 15 | 4-way infra attribution flag | AI Engine infrastructure_attribution field |
| 16 | Real-time alerts for high-risk emails | WebSocket red-banner trigger (Section 8) |
| 17 | Analyst dashboard (score/spoofing/trace/geo/confidence) | Investigation Terminal + Visual Forensics screens |
| 18 | Structured forensic/legal report | Section 63 BSA PDF (Section 8) |
| 19 | Searchable case management | /cases DataTable (Section 8) |
| 20 | Controlled PII handling | Presidio (Section 6) |
| 21 | Logging/evidence preservation/chain-of-custody | SHA-256 hash + timestamp on ingestion (Section 4) |
| 22 | Configurable retention and masking | Masking dropdown (Section 6) + **enforced purge job — patched in this update, Section 4.D** |

**Two items above were missing from the source blueprint and are patched into this file (marked above):** #2's obfuscated-URL/attachment IoC extraction had no dedicated step in the last draft; #22's retention control had a UI toggle but no actual enforcement logic. Both are now specified below.

**Known minor gap, not blocking:** the PS also names "aliases" and "reply chains" as graph-correlation entities. The Neo4j schema below only models Email/IP/Domain/ThreatActor. Treat as a stretch enhancement, not a build blocker.

---

## TECH STACK

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11+, FastAPI | Async support for non-blocking uploads + WebSocket streaming |
| Task queue | Celery + Redis | Keeps the UI responsive while the LLM/enrichment runs (3–5s per email) |
| Header forensics | `email` (stdlib), `authres`, `ipaddress` | RFC 822 parsing, auth-results validation, subnet checks |
| Typosquat detection | `Levenshtein` | Domain similarity scoring against a protected brand list |
| Geolocation (offline) | `maxminddb` + local GeoLite2-City/ASN `.mmdb` | Fully offline IP → city/ASN/hosting-provider lookup |
| Domain intel (Live Hunt Mode only) | `python-whois`, `dnspython` | Registration age, MX/TXT records — explicit opt-in only |
| PII scrubbing | Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`) | Local NLP-based redaction, no cloud call |
| Local LLM | Ollama + `qwen2.5:3b` | Runs on modest hardware, strong structured-JSON adherence |
| Schema enforcement | Pydantic | Forces exact taxonomy match (Section 6) |
| Graph database | Neo4j (Cypher) | PS explicitly requires graph-based relationship analysis |
| Relational storage | SQLite (Postgres if you have time) | Case metadata, settings, retention config |
| PDF generation | ReportLab | Programmatic layout control for the legal certificate |
| Frontend | Next.js (React) + TypeScript | App Router, good WebSocket support |
| Styling | Tailwind CSS + Shadcn UI | Dark SOC aesthetic, ready-made DataTable/Badge components |
| Graph visualization | React Flow | Renders the Neo4j campaign web |
| Geo visualization | Leaflet.js (`react-leaflet`) | Animated hop-map |
| Real-time alerts | WebSockets | Red-banner flash on high-risk `bec_subtype` |

Use Context7 (`use context7`) before writing integration code for any library you're not 100% certain of the current API for.

---

## 4. FORENSIC INGESTION & PARSING

**A. Cryptographic Hashing** — compute SHA-256 of the raw `.eml` bytes the instant it's uploaded; store alongside an immutable ingestion timestamp.

**B. Header Dissection** — split RFC 822 into Metadata (Subject, Sender, Date), Headers (Received, Message-ID, Reply-To, Return-Path), Body (HTML stripped to raw text).

**C. IoC Extraction Module (patched — was missing from the last draft)** — a dedicated step, separate from the AI call, that:
- extracts every hyperlink from the body and flags any using a shortener, an IP-literal URL, a mismatched display-text-vs-href, or a suspicious TLD
- lists every attachment filename + extension, flagging executable/script extensions (`.exe`, `.js`, `.scr`, `.html` with embedded forms, macro-enabled Office formats)
- surfaces this as a plain IoC list in the dashboard — deterministic, not AI-judged, since these are objective technical facts

**D. Retention Enforcement (patched — was missing from the last draft)** — the "Data Retention timeframe" UI setting must be backed by a real scheduled job (a simple daily Celery beat task is enough for a hackathon): on each run, delete case records and stored `.eml` files older than the configured window. Log every purge action for audit purposes. A UI dropdown with no backing job does not satisfy this requirement — build the job first, then the dropdown.

---

## 5. FORENSIC LOGIC — DETERMINISTIC RULES (never delegate these to the LLM)

**A. Reverse-Hop Traversal (True Origin IP)**
- Read the `Received` header array bottom (oldest) to top (newest)
- Use `ipaddress` to skip RFC 1918 private ranges (10.x, 172.16–31.x, 192.168.x)
- First remaining public IP = "most likely True Origin IP" + a confidence score reflecting how many hops were clean
- **Authorized Infra Check:** compare that IP against the sender domain's published SPF `ip4`/`ip6` CIDR blocks. Mismatch → flag "Unauthorized Sending Infrastructure."

**B. 4-Point Routing Anomaly Rules**
1. **Envelope Mismatch** — Return-Path domain ≠ From domain
2. **Reply-To Hijack** — Reply-To domain ≠ From domain
3. **Message-ID Forgery** — domain inside `<id@domain.com>` ≠ origin relay domain
4. **Time-Skew** — a later hop claims an earlier timestamp than the hop before it (classic forged-relay signal)

Each rule renders as an individual red/green checklist item in the UI — deterministic and explainable, not AI-judged.

**C. Threat Intel & Deceptive-Domain Radar**
- **Offline (default):** flag origin IP against a local Tor exit-node list and a locally-downloaded Spamhaus DROP list; flag if ASN belongs to a known commercial hosting provider (AWS/DigitalOcean/etc.) rather than a residential ISP
- **Typosquat check:** `Levenshtein` similarity between sender domain and a protected brand list (e.g. `sbi.co.in`, `microsoft.com`) — flag matches between 80–99% similarity as a lookalike domain
- **Live Hunt Mode only (explicit opt-in):** `python-whois` + `dnspython` fetch registration age and MX/TXT records; domains under 30 days old add to the threat score

---

## 6. AI ENGINE — STRICT DATA CONTRACT

Before any text reaches the LLM, run it through Presidio to mask PAN/Aadhaar/bank-account/phone patterns per the configured masking policy. Then enforce this exact schema via Ollama's structured-output `format` parameter (not just prompt instruction — use actual schema-constrained decoding):

```python
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ForensicAIAnalysis(BaseModel):
    fraud_taxonomy: Literal[
        "legitimate", "suspicious", "impersonated", "phishing", "fraud-related"
    ]
    bec_subtype: Literal[
        "payment_diversion", "fake_invoice_request",
        "credential_harvesting", "executive_impersonation", "none"
    ]
    infrastructure_attribution: Literal[
        "compromised_account", "spoofed_domain",
        "anonymized_infrastructure", "direct_malicious_actor"
    ]
    urgency_cues: List[str]          # exact phrases quoted from the email, not paraphrased
    threat_actor_claimed: Optional[str]
    requested_action: Optional[str]
    technical_justification: str = Field(
        description="Strict 2-sentence rationale citing specific evidence for the attribution flag"
    )
```

Require `urgency_cues` to be verbatim quotes from the email body — this lets the investigator visually verify the AI's claim against the source text instead of trusting an unfounded label. Use low/zero temperature for consistency across repeated runs of the same email.

---

## 7. GRAPH CORRELATION (Neo4j)

**Nodes:** `Email {hash, subject, fraud_taxonomy, bec_subtype}`, `IPAddress {address, asn, country, is_tor}`, `Domain {name, is_lookalike}`, `ThreatActor {impersonated_entity}`

**Edges:** `(Email)-[:ORIGINATED_FROM]->(IPAddress)`, `(Email)-[:CLAIMED_SENDER]->(Domain)`, `(Email)-[:ATTRIBUTED_TO]->(ThreatActor)`

**Repeat-campaign query, run on every new upload:**
```cypher
MATCH (new_email:Email {hash: $current_hash})-[:ORIGINATED_FROM]->(ip:IPAddress)
MATCH (past_email:Email)-[:ORIGINATED_FROM]->(ip)
WHERE past_email.hash <> new_email.hash
  AND past_email.fraud_taxonomy IN ['phishing', 'fraud-related']
RETURN count(past_email) AS previous_malicious_campaigns, ip.address
```
If `previous_malicious_campaigns > 0`, trigger an "Active Repeat Campaign" alert on the dashboard.

---

## 8. SCREENS & REAL-TIME/EXPORT FEATURES

1. **Ingestion & Global HUD** — drag-and-drop `.eml` upload, Air-Gap/Live-Hunt toggle in the nav bar, masking + retention policy settings, global WebSocket alert bar that flashes red if `bec_subtype != "none"`
2. **Investigation Terminal** — threat score gauge (0–100), taxonomy badges, 4-point anomaly checklist (red/green)
3. **Visual Forensics** — Leaflet hop-map (red = origin, yellow = relay, green = target), React Flow campaign graph
4. **Case Management (/cases)** — searchable DataTable by Case ID, origin IP, domain, or taxonomy; "Download Legal PDF" button per row

**Legal export (ReportLab):** title "Section 63 BSA (2023) Electronic Evidence Certificate," SHA-256 printed directly on the document, Part A (device owner, pre-filled) and Part B (expert, blank signature block), full technical trail (hop path, geolocation, AI summary).

---

## 9. CUT LIST — if time runs short, cut in this order

1. React Flow campaign graph visual → plain text "linked to N cases" list (keep the Neo4j query, drop only the visual)
2. Leaflet animated hop-map → static hop table
3. WebSocket real-time alert → simple on-page banner after processing completes (no live push)
4. Celery + Redis async queue → synchronous processing (accept a few seconds of UI wait)
5. Live Hunt Mode (WHOIS/DNS) → Air-Gapped Mode only, documented as a known limitation
6. Neo4j → SQLite with a manual self-join query for IP/domain matches (biggest single time-save if things are tight)
7. `.msg` file support → `.eml` upload + raw header paste only
8. Presidio → the Section 12.7 regex fallback, ONLY if Presidio/spaCy setup is actively broken and blocking progress for hours. Presidio is the confirmed primary PII method for this build — this is a last-resort fallback, not a default choice.

**Never cut:** header parsing, reverse-hop trace + SPF CIDR check, the 4-point anomaly rules, PII masking, the strict-schema LLM classification, the IoC extractor, the legal PDF export. These are the actual differentiators against the 22-item checklist — everything else is presentation or scale.

---

## 10. FINAL PRE-EVENT CHECKLIST

Everything needed to install, download, and configure is specified in **Step 0** at the top of this file — do all of that first. This section is only the final sanity pass, done the night before the event:

1. Confirm `GeoLite2-City.mmdb` + `GeoLite2-ASN.mmdb` are present on disk and loading correctly
2. Confirm `spamhaus_drop.txt` and `tor_exit_nodes.txt` are present and non-empty
3. Confirm `ollama run qwen2.5:3b` responds with the network disconnected
4. Confirm Presidio is installed, its spaCy model is downloaded, and it's actually redacting a test PII string end to end
5. If using Neo4j/Redis: confirm both Docker containers start without needing to pull an image
6. World map / graph frontend assets are bundled locally, not loaded from a CDN
7. **Final offline check** — disconnect entirely and run the full pipeline once end-to-end (upload → trace → geo → anomaly rules → LLM → graph/list → PDF) with Air-Gapped Mode on, confirming nothing silently depends on a network call

---

## 11. VALIDATION

Before considering any phase done, test it against three inputs: a legitimate email, an obvious phishing email, and a spoofed-domain BEC-style email. If a phase only works on the "obvious phishing" case, it isn't done.

---

## 12. HARDCODED LOGIC — EXACT ALGORITHMS (mandatory, do not substitute your own formula)

Everything in this section is exact and non-negotiable. If a formula below seems suboptimal, implement it exactly as written anyway and leave a comment — do not silently swap in a different threshold, weight, or library default behavior. This section exists specifically so the build has one consistent, defensible answer for every scored number in the UI.

### 12.1 Reverse-Hop Origin Detection

```python
def find_true_origin(received_headers: list[str]) -> dict:
    # received_headers as they appear in the raw file: index 0 = newest hop, last = oldest
    hops = parse_received_chain(received_headers)   # each hop: {ip, claimed_hostname, timestamp}
    hops_oldest_first = list(reversed(hops))

    origin_ip = None
    hops_walked = 0
    for hop in hops_oldest_first:
        hops_walked += 1
        if hop.ip is None:
            continue
        if is_rfc1918_private(hop.ip):   # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
            continue
        origin_ip = hop.ip
        break

    return {
        "origin_ip": origin_ip,
        "hops_before_origin": hops_walked,
        "total_hops": len(hops_oldest_first),
    }
```

**If `origin_ip` is None after walking every hop** (fully private/internal chain — the compromised-legitimate-account case): do not error or guess. Set `origin_ip = None` and render the UI label exactly as: **"Origin Undetermined — Likely Compromised Legitimate Infrastructure."** This is a real, expected outcome, not a bug — see Section 5.A / the known-limitation discussion earlier in this file.

### 12.2 Trace Confidence Score (separate from the Threat Score in 12.4)

```python
def trace_confidence(origin_ip, time_skew_detected, multiple_public_candidates) -> int:
    if origin_ip is None:
        return 0   # "Undetermined" — never show a fake confidence number for a null result
    score = 90
    if time_skew_detected:
        score -= 30
    if multiple_public_candidates:
        score -= 20
    return max(10, min(90, score))   # never display 100% — it's a forensic estimate, not a fact
```

### 12.3 4-Point Routing Anomaly Rules (exact comparisons)

1. **Envelope Mismatch:** `domain(Return-Path) != domain(From)` (case-insensitive, strip subdomains only if you compare registrable domain, e.g. `mail.paypal.com` vs `paypal.com` → not a mismatch; `paypal.com` vs `paypal-secure.com` → mismatch)
2. **Reply-To Hijack:** if `Reply-To` header absent → flag = `not_applicable`. If present → `domain(Reply-To) != domain(From)` → flag = `True`
3. **Message-ID Forgery:** extract domain from `<id@domain>` in `Message-ID`. Compare against the HELO/EHLO hostname string claimed in the `Received` header closest to the origin hop. If reverse-DNS/HELO data is unavailable → flag = `undetermined`, never guess
4. **Time-Skew:** walking hops oldest→newest, each hop's timestamp must be ≥ the previous hop's timestamp minus a 5-minute clock-skew tolerance. Any hop earlier than that → flag = `True`

Each of these renders as its own red/green/gray (`undetermined`) badge — never collapse them into a single combined "anomaly" boolean.

### 12.4 Threat Score (0–100 gauge) — exact weight table

| Signal | Points | Condition |
|---|---|---|
| Anomaly rules (12.3) | up to 40 | 10 points per triggered flag (max 4 flags) |
| Unauthorized infra (SPF CIDR mismatch, Section 5.A) | 15 | flat, if triggered |
| Typosquat/lookalike domain (12.5) | 15 | flat, if triggered |
| VPN/Tor/hosting-provider origin | 10 | flat, if triggered |
| Domain age < 30 days (Live Hunt Mode only) | 10 | flat, if triggered — 0 if Air-Gapped Mode (data unavailable) |
| AI `fraud_taxonomy` contribution | 0 / 3 / 6 / 8 / 10 | legitimate=0, suspicious=3, impersonated=6, phishing=8, fraud-related=10 |

`threat_score = min(100, sum of all triggered points)`. Bands: **0–30 Low, 31–60 Medium, 61–100 High.** The real-time red-banner alert (Section 8) fires when `threat_score >= 70 OR bec_subtype != "none"` — use this exact condition, not a vaguer "looks risky" check.

### 12.5 Typosquat / Impersonation Check

```python
PROTECTED_BRANDS = [
    "sbi.co.in", "rbi.org.in", "microsoft.com", "google.com",
    "paypal.com", "amazon.com", "icicibank.com", "hdfcbank.com"
]  # seed list — extend with any brand name detected in the email body/display-name

sender_domain = extract_domain(from_header)
for brand in PROTECTED_BRANDS:
    similarity = levenshtein_similarity(sender_domain, brand)  # 0-100 scale
    if 80 <= similarity < 100:
        flag_lookalike(sender_domain, brand, similarity)
        break

# Separately: cross-check claimed identity vs technical sender
claimed_brand = extract_display_name_brand(from_header)   # e.g. "State Bank of India"
if claimed_brand and canonical_domain(claimed_brand) != sender_domain:
    flag_impersonation(claimed_brand, sender_domain)
```

Note the two checks are independent: Levenshtein catches spelling lookalikes (`rnicrosoft.com`); the display-name cross-check catches a completely different domain claiming to be a trusted brand outright. Run both — one does not substitute for the other.

### 12.6 IoC Extraction — exact reference lists

- **URL shorteners (flag any link domain matching):** `bit.ly, tinyurl.com, goo.gl, t.co, ow.ly, is.gd, buff.ly`
- **IP-literal URLs:** regex `https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` → flag
- **Display-text/href mismatch:** anchor text visually resembling a URL/domain that differs from the actual `href` domain → flag
- **Suspicious attachment extensions:** `.exe, .scr, .js, .vbs, .bat, .cmd, .jar, .docm, .xlsm, .pptm`, plus any `.html` attachment containing an embedded `<form>` tag
- **Elevated-risk TLDs (soft signal, not an automatic flag):** `.zip, .xyz, .top, .club, .work`

### 12.7 PII Redaction — deterministic fallback (EMERGENCY USE ONLY — Presidio is the confirmed primary method, see Section 9 item 8)

- Aadhaar: `\b\d{4}\s?\d{4}\s?\d{4}\b`
- PAN: `\b[A-Z]{5}[0-9]{4}[A-Z]\b`
- Indian mobile number: `\b[6-9]\d{9}\b`
- Generic bank account: `\b\d{9,18}\b` — label this one explicitly as "possible account number" in the UI, since it has a real false-positive rate against order IDs and reference numbers (already disclosed as a known weakness — do not oversell this pattern's accuracy)

**Rule for this whole section:** Presidio is CONFIRMED as the primary and required PII method for this build — install it in Step 0, do not skip it. 12.7 exists only as an explicit, disclosed emergency fallback per Section 9 item 8, to be used only if Presidio/spaCy setup is actively broken and blocking progress for hours. Never mix partial Presidio + partial regex silently; if you do fall back, note clearly in a code comment which path is active.

---

## 13. UI/UX DESIGN SYSTEM — exact and mandatory (do not invent your own visual language)

**This section is authored by the project owner, not by Antigravity.** Every value below is a locked decision, the same way Section 12's scoring formulas are locked. If a value is marked `TODO — awaiting input`, that piece is not yet decided — do not fill the gap with your own default (a generic Tailwind slate/zinc palette, a default shadcn theme, stock Inter-everywhere typography, etc.). Stop and flag it as missing rather than guessing.

### 13.A Color Palette
```
Background (primary):     TODO — awaiting input
Background (elevated/card): TODO — awaiting input
Primary accent:           TODO — awaiting input
Danger / high-risk:       TODO — awaiting input
Warning / medium-risk:    TODO — awaiting input
Success / low-risk / clean: TODO — awaiting input
Text (primary):           TODO — awaiting input
Text (muted/secondary):   TODO — awaiting input
Border / divider:         TODO — awaiting input
```

### 13.B Typography
```
Heading font:    TODO — awaiting input
Body font:       TODO — awaiting input
Monospace (for hashes, IPs, headers): TODO — awaiting input
Type scale (H1/H2/H3/body/caption sizes): TODO — awaiting input
```

### 13.C Spacing & Layout Tokens
```
Base spacing unit: TODO — awaiting input
Card border-radius: TODO — awaiting input
Grid/layout structure per screen: TODO — awaiting input
```

### 13.D Component-Level Specs (reference exact components/screenshots provided)
- **Threat Score Gauge (0–100):** TODO — awaiting reference component/image
- **Taxonomy badges** (fraud_taxonomy, bec_subtype, infrastructure_attribution): TODO — awaiting reference
- **Anomaly checklist item (red/green/gray states, Section 12.3):** TODO — awaiting reference
- **Hop-map / Leaflet styling:** TODO — awaiting reference
- **Campaign graph node/edge styling (React Flow):** TODO — awaiting reference
- **Case management DataTable:** TODO — awaiting reference
- **Global WebSocket alert banner (red-flash state, Section 12.4 trigger):** TODO — awaiting reference

### 13.E How to feed design input into this section
When you provide components/references, the most usable formats are:
- Exact hex codes (not color names) for the palette in 13.A
- Font family names exactly as they appear on Google Fonts / the type foundry
- Screenshots or Figma links of any component you want matched, with a note on which of the 7 components in 13.D it maps to
- If you're reusing an existing shadcn/ui theme or component library preset, name it exactly (e.g. "shadcn 'zinc' base, overridden with the palette in 13.A")

Once each `TODO` above is replaced with a real value, this section becomes as binding as Section 12 — Antigravity builds to it exactly, no creative substitution.

**Rule for Antigravity:** if you reach this section during a build and any value is still `TODO`, do not proceed with that component using an invented default. Flag it back to the project owner and move to a different task until the input arrives.