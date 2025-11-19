import requests
import json
import datetime

API_KEY = "2a6b2813c62043dcc9ec3551dca42c18"

ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/"

PARAMS = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "spreads,totals",
    "oddsFormat": "american",
    "bookmakers": "draftkings",  # ← ONLY DK ODDS
}

print("📡 Fetching DraftKings-only NCAAB odds...")
response = requests.get(ODDS_URL, params=PARAMS)

if response.status_code != 200:
    print("❌ Error:", response.status_code, response.text)
    raise SystemExit()

data = response.json()

date_str = datetime.date.today().strftime("%Y-%m-%d")
filename = f"daily_odds_{date_str}.json"

with open(filename, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Saved DraftKings odds → {filename}")
