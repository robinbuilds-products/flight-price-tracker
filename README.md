# Flight Price Tracker (STL to STT)

Checks round-trip flight prices once a day, logs them, builds an Excel workbook, and emails an alert when a price drops. It runs free on GitHub Actions.

## What it tracks
- Route: St. Louis (STL) to St. Thomas (STT), round trip, 2 adults
- Date windows: Apr 13-20, 2027 and Apr 18-25, 2027 (edit `config.json` to change)
- Airlines: United and American. Cabins: Premium Economy and Business
- Rules: no overnight layovers; Kayak and Hopper are never used (data comes from Google Flights through SerpApi)

## Setup (about 15 minutes)
1. **Create a private GitHub repository** and upload these files. Keep it private if it holds client data.
2. **Get a SerpApi key** at serpapi.com (the free plan includes monthly searches; this tracker uses 8 per day, about 240 per month).
3. **Create a Gmail app password** (Google Account > Security > 2-Step Verification > App passwords). Never use your normal password.
4. In the repo go to **Settings > Secrets and variables > Actions** and add four secrets:
   - `SERPAPI_KEY`: your SerpApi key
   - `SMTP_USER`: the Gmail address that sends the alerts
   - `SMTP_PASSWORD`: the app password from step 3
   - `ALERT_EMAIL`: who receives alerts (your address while testing, the client's after sign-off)
5. Go to the **Actions** tab, choose "Daily flight price check", and click **Run workflow** to test.

## Output
- `data/price_history.csv`: every price ever recorded (the source of truth)
- `data/Flight_Price_Tracker.xlsx`: Price Log tab (change and DROP flag per row) and Summary tab (latest, lowest, highest per option)

## Try it without keys
```
pip install -r requirements.txt
python tracker.py --mock --no-email --date 2026-11-01
```
Mock mode uses fake prices to test the logic. Delete the files in `data/` before the first real run.

## Things to verify on the first live run
- Whether SerpApi's price is the total for both travelers or per person. If per person, set `price_is_total_for_all_travelers` to `false` in `config.json`.
- Compare one result with the airline's own site before trusting alerts.
- Online senior discounts are generally not shown; call the airline to ask about them.
- Seat adjacency (3 in a row) cannot be confirmed from price data; check the seat map at booking.

## Settings (`config.json`)
`drop_threshold_pct` sets how big a one-day fall triggers an alert. `target_price_total` (a number) also alerts whenever a price is at or below it.
