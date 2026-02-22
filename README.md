# Absentee list to CEO WhatsApp

Fetches the daily absent employees list from [etimeoffice.com](https://www.etimeoffice.com) and sends it to the CEO's WhatsApp via Twilio at 3 PM (IST).

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure environment**  
   Copy `.env.example` to `.env` and set:
   - **Etimeoffice**: `ETIME_COMPANY_ID`, `ETIME_USER`, `ETIME_PASSWORD` (login form: Company ID, Username, Password)
   - **Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` (e.g. `whatsapp:+14155238886`), `CEO_WHATSAPP_TO` (e.g. `whatsapp:+919876543210`)

3. **GitHub Actions (3 PM daily)**  
   In the repo: **Settings → Secrets and variables → Actions**, add the same variables as repository secrets. The workflow runs at 3 PM IST and needs all of the above.

## Run locally

```bash
# Headless (default)
python -m src.run_daily

# With browser visible (debug)
HEADLESS=false python -m src.run_daily
```

## Project layout

- `src/fetch_absent_list.py` – Playwright: login → TotalAbsentEmpList → Show All → scrape table
- `src/format_message.py` – Format list for WhatsApp; split if long
- `src/send_whatsapp.py` – Twilio WhatsApp send
- `src/run_daily.py` – Entrypoint: fetch → format → send (exit 0/1)
- `.github/workflows/absent-daily.yml` – Scheduled at 3 PM IST

`whatsapp.py` is a separate Web WhatsApp (Selenium) script and is not used by this pipeline.
