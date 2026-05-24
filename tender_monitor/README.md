# 🔍 AI Tender Monitor — Indian Government Tech Tenders

Fully automated, AI-powered system that monitors Indian Government procurement 
portals twice daily and delivers relevant technology tenders to your inbox or 
Google Sheet.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULER (APScheduler)                   │
│              10:00 AM IST  ·  07:00 PM IST                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ triggers
┌──────────────────────────▼──────────────────────────────────┐
│                    SCRAPER ENGINE                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌──────────┐  │
│  │  CPPP   │  │   GeM   │  │State Portals│  │NIC/PSUs  │  │
│  │eScraper │  │eScraper │  │  (10+ states)│  │  Scraper │  │
│  └────┬────┘  └────┬────┘  └──────┬──────┘  └────┬─────┘  │
└───────┼────────────┼──────────────┼───────────────┼────────┘
        └────────────┴──────────────┴───────────────┘
                           │ raw tenders
┌──────────────────────────▼──────────────────────────────────┐
│                 PROCESSOR PIPELINE                            │
│  ┌──────────────────┐    ┌─────────────────────────────┐   │
│  │  Keyword Filter  │───▶│  Claude AI Summarizer        │   │
│  │  (80+ keywords)  │    │  (structured JSON summaries) │   │
│  └──────────────────┘    └─────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ relevant + summarized
┌──────────────────────────▼──────────────────────────────────┐
│                   STORAGE (SQLite / PostgreSQL)               │
│         Deduplication · History · Stats                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ new tenders only
┌──────────────────────────▼──────────────────────────────────┐
│                    REPORTERS                                  │
│      ┌────────────────┐     ┌─────────────────────┐        │
│      │  Email (HTML)  │     │   Google Sheets      │        │
│      └────────────────┘     └─────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
tender_monitor/
├── main.py                    # Entry point
├── requirements.txt
├── .env.example               # Copy → .env and fill in secrets
├── Dockerfile
├── docker-compose.yml
│
├── config/
│   ├── settings.py            # All configuration
│   └── keywords.py            # Keyword bank (add more here)
│
├── scrapers/
│   ├── base_scraper.py        # Abstract base + HTTP helpers
│   ├── cppp_scraper.py        # Central Public Procurement Portal
│   ├── gem_scraper.py         # GeM (Government e-Marketplace)
│   ├── state_scraper.py       # 10+ state portals
│   └── nic_scraper.py         # NIC, Railways, PSUs, Smart Cities
│
├── processors/
│   ├── filter.py              # Keyword-based relevance filter
│   └── summarizer.py          # Claude AI summarization
│
├── reporters/
│   ├── email_reporter.py      # HTML email reports
│   └── sheets_reporter.py     # Google Sheets appender
│
├── database/
│   └── db.py                  # SQLAlchemy ORM + deduplication
│
├── scheduler/
│   └── scheduler.py           # APScheduler — 10 AM & 7 PM IST
│
├── utils/
│   └── logger.py              # File + console logging
│
├── data/                      # SQLite database (auto-created)
└── logs/                      # Daily log files (auto-created)
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.11 or 3.12
- pip
- (Optional) Docker & Docker Compose

### 2. Clone / Download

```bash
git clone <your-repo>
cd tender_monitor
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Open .env in your editor and fill in:
#   ANTHROPIC_API_KEY = your Claude API key
#   EMAIL_ENABLED = true
#   EMAIL_SENDER = youremail@gmail.com
#   EMAIL_PASSWORD = your-gmail-app-password (16-char App Password)
#   EMAIL_RECIPIENTS = target@email.com
```

### 5. Gmail App Password (Required for Email)

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App Passwords → Generate → Copy the 16-char password
4. Paste into `EMAIL_PASSWORD` in `.env`

### 6. Google Sheets (Optional)

1. Go to https://console.cloud.google.com
2. Create a project → Enable Google Sheets API + Google Drive API
3. Create a Service Account → Download JSON key → save as `credentials.json`
4. Open your Google Sheet → Share → Add service account email as Editor
5. Copy Sheet ID from URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
6. Set `SHEETS_ENABLED=true` and `GOOGLE_SHEET_ID=SHEET_ID` in `.env`

---

## 🚀 Running the System

### Run Once (Manual / Test)

```bash
python main.py --mode run-once
```

### Start Scheduler (Daily Automation)

```bash
python main.py --mode scheduler
```

### Docker Deployment (Recommended for VPS)

```bash
# Build and start
docker-compose up -d

# View live logs
docker logs -f tender_monitor

# Stop
docker-compose down
```

---

## 🖥️ VPS / Cloud Deployment

### On Ubuntu VPS (e.g., DigitalOcean, AWS EC2, Hetzner)

```bash
# 1. Upload files via SCP or git clone
scp -r tender_monitor/ user@your-vps:/home/user/

# 2. SSH in and install
ssh user@your-vps
cd tender_monitor
pip install -r requirements.txt

# 3. Run as a background service with systemd
sudo nano /etc/systemd/system/tender_monitor.service
```

**systemd service file:**
```ini
[Unit]
Description=AI Tender Monitor
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/tender_monitor
ExecStart=/usr/bin/python3 main.py --mode scheduler
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tender_monitor
sudo systemctl start tender_monitor
sudo systemctl status tender_monitor
```

### Or use Docker (easiest):

```bash
docker-compose up -d
```

---

## 🗄️ Database Schema

### tenders table

| Column           | Type      | Description                        |
|------------------|-----------|------------------------------------|
| unique_key       | VARCHAR   | Primary key (portal:tender_id)     |
| tender_id        | VARCHAR   | Portal's tender ID                 |
| title            | TEXT      | Tender title                       |
| organization     | VARCHAR   | Issuing department/org             |
| portal_source    | VARCHAR   | e.g., "CPPP", "GeM"                |
| govt_type        | VARCHAR   | "Central" or "State"               |
| state            | VARCHAR   | State name (NULL for central)      |
| url              | TEXT      | Official tender URL                |
| publish_date     | DATE      | Date published                     |
| deadline         | DATE      | Submission deadline                |
| tender_value     | VARCHAR   | Budget/value if disclosed          |
| category         | VARCHAR   | Product/service category           |
| raw_description  | TEXT      | Original scraped description       |
| ai_summary       | TEXT      | Claude AI summary                  |
| matched_keywords | TEXT      | JSON array of matched keywords     |
| reported         | BOOLEAN   | Whether sent in a report           |
| created_at       | DATETIME  | When record was created            |

---

## ➕ Adding New Tender Websites

### Option 1: Add to State Portals

Edit `scrapers/state_scraper.py` → add entry to `STATE_PORTALS` list:

```python
{
    "name": "New State eProcurement",
    "state": "New State",
    "url": "https://newtender.state.gov.in",
    "tender_list_path": "/tenders",
    "row_selector": "table tr",       # CSS selector for tender rows
    "cols": {"title": 0, "org": 1, "pub_date": 2, "deadline": 3},
},
```

### Option 2: Add to NIC Portals

Edit `scrapers/nic_scraper.py` → add to `NIC_PORTALS`:

```python
{
    "name": "New PSU Tenders",
    "org": "New Organisation Name",
    "url": "https://www.newpsu.com/tenders",
    "row_selector": "table.tenders tr",
    "govt_type": "Central",
    "state": None,
},
```

### Option 3: Create a Custom Scraper

```python
# scrapers/my_custom_scraper.py
from scrapers.base_scraper import BaseScraper, RawTender

class MyCustomScraper(BaseScraper):
    name = "My Custom Portal"
    base_url = "https://example.gov.in"

    async def fetch_tenders(self) -> list[RawTender]:
        html = await self._fetch(self.base_url + "/tenders")
        soup = self._parse_html(html)
        # ... parse and return RawTender objects
```

Then register it in `main.py`:

```python
from scrapers.my_custom_scraper import MyCustomScraper

def _init_scrapers(self):
    return [
        CPPPScraper(self.settings),
        GeMScraper(self.settings),
        MyCustomScraper(self.settings),   # ← add here
        ...
    ]
```

---

## 🔑 Required APIs & Keys

| Service       | Purpose                  | Cost        | Link                                    |
|---------------|--------------------------|-------------|-----------------------------------------|
| Anthropic     | AI summarization         | Pay-per-use | https://console.anthropic.com           |
| Gmail         | Email reports            | Free        | Google App Password                     |
| Google Sheets | Spreadsheet reports      | Free        | Google Cloud Console                    |

---

## 🐛 Troubleshooting

| Issue                        | Fix                                              |
|------------------------------|--------------------------------------------------|
| No tenders found             | Run `--mode run-once` and check logs             |
| Email not sending            | Verify App Password, check SMTP settings         |
| Sheets error                 | Check credentials.json path and sheet sharing    |
| Portal blocked (403/429)     | Increase RETRY_DELAY in .env                     |
| Database locked (SQLite)     | Upgrade to PostgreSQL for concurrent access      |
| Playwright not found         | Run: `playwright install chromium`               |

---

## 📜 Disclaimer

This system is for **monitoring and information purposes only**.
It does NOT apply for tenders, fill forms, or submit bids.
Always verify tender details on the official government portal before acting.
