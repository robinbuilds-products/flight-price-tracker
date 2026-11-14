# Flight Price Tracker

An automated daily flight price tracker that watches fares, keeps a price history, shows pricing trends, and emails an alert when a fare hits a target or drops. Built as a forward-deployed product project: from a client's real need, through research and design, to a working, tested system.

Built with Microsoft Copilot in a single day: about two hours for the initial build, plus about an hour and a half of testing and refining the email message.

## The problem
A traveler booking premium-cabin flights for two wanted to buy at the best moment, without a travel agent. Fares move every day, checking by hand is easy to forget, and the flight price decided when hotel prices could be finalized.

## What it does
- Checks fares once a day (7:00 AM Central) for a round trip from St. Louis (STL) to St. Thomas (STT), 2 travelers, two April 2027 date windows
- Covers United and American, in Premium Economy and Business, with no overnight layovers
- Saves every day's price to a history file and rebuilds an Excel workbook with daily changes, drop flags, trend columns and a price chart
- Emails an alert when a fare is at or below a target price, or drops by a set percentage from the day before
- Makes each fare in the email a link that opens that fare's search on Google Flights
- Shares a pricing trend (up or down versus the 7-day average) once 7 days of data are in
- Sends a plain-language message written for an executive reader: what was found, the alert level, the pricing trend, and how to stop the emails

## How it works
1. GitHub Actions starts the check on a daily schedule.
2. `tracker.py` asks SerpApi for Google Flights prices, one search per airline, cabin and date window (8 a day).
3. Results are filtered for the right airline and no overnight layovers, and the lowest qualifying fare is kept.
4. The price is added to `data/price_history.csv`, and `data/Flight_Price_Tracker.xlsx` is rebuilt.
5. If an alert rule is met, an email goes out with the workbook attached.
6. The new data is saved back to the repository.

## Settings
Everything the client might change lives in `config.json`: route, dates, airlines, cabin codes, travelers, the percentage-drop threshold and the target price. No code changes are needed for these.

## Setup
1. Create a private GitHub repository and add these files.
2. Get a SerpApi key and a Gmail app password.
3. In the repository, go to Settings > Secrets and variables > Actions and add four secrets: `SERPAPI_KEY`, `SMTP_USER`, `SMTP_PASSWORD` and `ALERT_EMAIL` (who receives alerts).
4. Open the Actions tab, choose "Daily flight price check" and click Run workflow to test.

To try the logic without keys: `python tracker.py --mock --no-email` uses fake prices.

## Check frequency
The tracker runs once a day. Airlines change fares throughout the day with no published schedule, so there is no exact moment to sync to. Checking more often multiplies the searches used and would likely require a paid SerpApi plan.

## Pricing trends and the road to prediction
The tracker records every day's price, and the workbook shows daily changes in dollars and percent, the lowest price so far, and a 7-day average. From day 7, the email reports whether each fare is above or below its 7-day average. This describes what has happened; it does not forecast what will happen. It is the data foundation for a future drop-prediction model, which would need months of daily prices, including the holiday period, to be reliable.

## What testing found
Testing against the live source caught issues a fake-data test could not:
- The cabin codes were off by one and searched First instead of Business. Opening the saved link in Google Flights exposed it, and a one-line config fix resolved it.
- Premium Economy has no fares on this route right now, so the tracker correctly logs nothing for it and says so in the email.
- Google's page confirmed that prices are totals for both travelers.
- A first attempt to send from a custom-domain Zoho mailbox kept failing, so the build uses Gmail.

## Limits
- Fare data does not include seat maps or seat counts.
- Prices from the data service can differ slightly from the airline's own site.
- A target-price alert repeats daily while fares stay at or below it.
- Trends start after 7 days of data.
- The free data-plan limit has not been confirmed against about 240 searches a month.

## My role
Product manager and builder: defined the requirements with the client, researched what AI platforms and travel sites already offer, chose the data source and architecture, wrote the alert message for an executive reader, and tested the system end to end.

## Tech
Python, GitHub Actions, SerpApi (Google Flights data), openpyxl, Gmail SMTP.

## Case study
See [case-study.md](case-study.md) for the research, design decisions and lessons learned.
