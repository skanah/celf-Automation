# CELF Automation

Automated reporting tool for the **CELF (Christian Evangelical Lutheran Fellowship)** online reporting portal. Built with **Flask + Flask-SocketIO** for the web interface and **Playwright** for browser automation, it lets you upload accounts and report data (CSV/Excel), then submit church and cell reports in parallel across multiple accounts with real-time progress logging.

---

## ✨ Features

- 🌐 **Web UI** — single-page interface (Tailwind CSS) for uploading files and triggering runs
- 📁 **File upload** — accounts (CSV) and church/cell reports (CSV or Excel)
- 👥 **Multi-account support** — run reports concurrently across many CELF accounts (configurable concurrency)
- 🕒 **Real-time logs** — live SocketIO stream of login, submission, success/failure per account
- 📊 **Two report types** — Church reports (Sunday 1/2, midweek, virtual) and Cell reports (meeting stats, conversions, testimony)
- ⚙️ **Configurable** — concurrency, timeouts, headless mode, endpoints all in `config.py`

---

## 📂 Project Structure

```
celf-automation/
├── app.py                  # Flask app + routes + async runner
├── config.py               # Configuration (CELF endpoints, timeouts, concurrency)
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore (excludes .venv, data/, secrets)
├── README.md               # This file
├── automation/             # Browser automation package
│   ├── __init__.py
│   ├── browser.py          # Playwright browser pool
│   ├── session.py          # Per-account login session
│   ├── church_report.py    # Church report form filler
│   ├── cell_report.py      # Cell report form filler
│   └── validators.py       # (reserved for future validation helpers)
├── templates/
│   └── index.html          # Frontend UI (Tailwind + SocketIO)
└── data/                   # Runtime data (gitignored — contains credentials)
    ├── accounts.csv
    ├── church_reports.xlsx
    └── cell_reports.xlsx
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/skanah/celf-Automation.git
cd celf-Automation
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Playwright also needs its browser binaries:

```bash
playwright install chromium
```

### 3. Configure

Copy and edit configuration if needed. `config.py` reads from environment variables where available:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me-in-prod` | Flask secret key |
| `BASE_URL` | `https://celfonline.org` | CELF portal domain |
| `HEADLESS` | `True` | Run browser headless |
| `MAX_CONCURRENT_ACCOUNTS` | `5` | Parallel account runs |
| `NAVIGATION_TIMEOUT` | `30000` | Page navigation timeout (ms) |
| `ACTION_TIMEOUT` | `15000` | Element action timeout (ms) |

Create a `.env` file in the project root to override defaults:

```env
SECRET_KEY=your-secret-key
HEADLESS=False
MAX_CONCURRENT_ACCOUNTS=3
```

> ⚠️ **Security:** `.env` and `data/` are gitignored. Never commit account credentials.

### 4. Prepare your data files

Place your input files in `data/` (or upload them via the UI):

**`data/accounts.csv`** — required columns: `account_id, username, password`

```csv
account_id,username,password
Bekee,user@example.com,pass123
Voke,another@example.com,pass456
```

**Church reports** (CSV or Excel) — must include `event_date`. Common columns:

```csv
event_date,name,sun1_adult,sun1_children,sun1_childrenchurch,sun1_first_timers,
sun1_born_again,sun1_total,sun1_testimonies,sun2_adult,sun2_children,
sun2_childrenchurch,sun2_first_timers,sun2_born_again,sun2_total,sun2_testimonies,
wed_adult,wed_children,wed_childrenchurch,wed_first_timers,wed_born_again,wed_total,
wed_testimonies,virtual_platform,virtual_link,virtual_service_pic,
virtual_counter_pic,virtual_attendance,virtual_testimony,virtual_total
```

**Cell reports** (CSV or Excel) — must include `date_of_meeting`. Common columns:

```csv
date_of_meeting,type_of_meeting,time_meeting_started,time_meeting_ended,
total_no_at_cell_meeting,total_no_at_bible_study,no_of_first_timers,
no_of_new_converts,no_of_infilling,no_of_members_at_wed_service,
no_of_members_at_sun_service,testimony
```

### 5. Run the application

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

1. Upload **Accounts CSV**
2. Upload **Church Reports** and/or **Cell Reports**
3. Click **Execute** — reports run in parallel across all accounts
4. Watch live logs and per-account results in the UI

---

## 🔧 How It Works

1. **Browser pool** (`automation/browser.py`) — launches a single Chromium instance via Playwright and creates an isolated browser context per account.
2. **Account session** (`automation/session.py`) — logs into the CELF portal with a given `account_id`/`username`/`password`.
3. **Report fillers** (`church_report.py`, `cell_report.py`) — navigate to the appropriate report form, fill fields from the uploaded row, attach virtual-church screenshots when provided, and submit.
4. **Runner** (`app.py`) — orchestrates concurrent workers (limited by `MAX_CONCURRENT_ACCOUNTS`) and streams results back to the frontend over SocketIO.

---

## ⚠️ Important Notes

### Browser selectors
The Playwright selectors in `automation/session.py`, `church_report.py`, and `cell_report.py` are written against the current CELF form markup. If the portal changes its field names/IDs, update the selectors in those files to match.

### Credentials
- `data/accounts.csv` contains real usernames/passwords and is **gitignored** — do not add it to version control.
- Use a dedicated/test CELF account where possible, and rotate credentials regularly.

### Headless mode
Set `HEADLESS=False` in `.env` to watch the browser run (useful for debugging selector issues).

---

## 📜 License

MIT License. Feel free to adapt for your own reporting needs.

---

## 🙌 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.