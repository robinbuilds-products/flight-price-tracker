# Flight Price Tracker

An automated daily flight price tracker that watches fares, keeps a price history, shows pricing trends, and emails an alert when a fare hits a target or drops. I built it as a forward-deployed product project, from a client's real need through research, design and testing to a working system.

Built with Microsoft Copilot in a single day: about three hours in total, including QA testing and refining the email message.

Cost: about one day's worth of Copilot Cowork usage.

## Client goal

A client booking premium-cabin flights for two wanted to buy at the best moment, without a travel agent and without checking prices by hand every day. She also wanted to see how much, and in which direction, prices were changing, in dollars and percent.

Doing this by hand meant running eight separate searches every day (two airlines, two cabins, two date windows), writing down each fare, and working out on her own whether each price had gone up or down, and by how much. The implementation was meant to take that daily work off her plate entirely: one automated check, a full price history, and an email whenever a fare hits her alert level.

## Discovery

The client first tried to build a tracker herself with Copilot in her personal Microsoft 365 account, as a way to learn to build with AI. She wasn't getting the results she wanted, so she asked me to build an AI flight tracker using Google Flights data.

What I did:

- Had Copilot clarify what the issue was with the client's first attempt: Copilot couldn't get live Google Flights prices on its own. That told me the first job was finding a reliable price source.
- Asked the client what outcome she wanted before any build work started. That outcome is what was delivered.
- Defined the requirements with the client: route, travel dates, airlines, cabins, number of travelers, and what should trigger an alert.
- Researched what AI platforms and travel sites already offer.
- Talked with the client about what she needed to see in an alert before writing it.

## Solutioning

The first challenge was finding a reliable way to get flight information that includes prices without paying for a service. Along the way, I learned why this is hard: booking data is often shared, but airlines only give live pricing to sellers that turn searches into bookings. This is called the look-to-book ratio, for example, one booking expected for every 1,500 searches. I explored the options with Copilot and chose a solution before building anything.

What I did:

- Chose SerpApi (Google Flights data) as the data source. Its free plan covers 250 searches a month, enough for 8 searches a day.
- Worked out how many searches the plan allows, then estimated the cost if the client wants the tracker to run longer to build up the price history.
- Chose to build in GitHub rather than inside Copilot itself. GitHub is owned by Microsoft, so this keeps the code in the Microsoft ecosystem and makes it easy to share with anyone who wants the same kind of tracker.
- Chose GitHub Actions to run the check once a day, with no server to maintain.
- Wrote a tailored email for an executive reader that:
  - Reminds her why she is receiving it.
  - Lets her click straight to that fare's search on Google Flights, because seats can fill up fast.
  - Attaches the Excel file with the full price history.
  - Shows at a glance whether prices went up or down, and by how much. This starts after 7 days of data.

## Configuration and testing

What I did:

- Put everything the client might change in `config.json`: route, dates, airlines, cabin codes, travelers, the percentage-drop threshold and the target price. No code changes are needed for these.
- Set the alert level: an email goes out when a fare is $5,501 or less for 2 travelers, or when a price drops 5% or more from the day before.
- Checked that everything private stays private: the API key, email password and alert email address are stored as encrypted GitHub secrets and never appear in the code, data files or public repository.
- Tested against the live source, which caught issues a fake-data test could not:
  - The cabin codes were off by one and searched First instead of Business. Opening the saved link in Google Flights exposed it, and a one-line config fix resolved it.
  - Premium Economy has no fares on this route right now, so the tracker correctly logs nothing for it and says so in the email.
  - Google's page confirmed that prices are totals for both travelers.
  - A first attempt to send from a custom-domain Zoho mailbox kept failing, so the build uses Gmail.

## Go-live

What I did:

- Turned on the daily schedule: the tracker checks fares every day at 7:00 AM Central and sends the alert email.
- Checked the first live emails and refined the wording before handing it to the client.
- Walked the client through the solution and the email to see if any changes or tweaks were needed. None were.
- Next step: we are now building up the historical prices so predictive AI can be layered on top.

### What the alert email looks like

<img width="1167" height="902" alt="flight-alert-email" src="https://github.com/user-attachments/assets/c4ecf344-75b3-4240-a460-6f0cd1d0de6b" />

*Sample alert from November 23, 2026. Email addresses are hidden.*

## Outcome

**Baseline (before):** The client had to run eight searches by hand every day, record each fare, and calculate the changes herself. Her own attempt to build a tracker with Copilot didn't give her the results she wanted. She had no price history and no way to see whether fares were rising or falling. The other option was paying a travel agent.

**Result (after):** Eight fare searches run automatically every day (each airline, cabin and date window), with no hand-checking and no data cost. Every day's price is saved. The client gets one email with clickable fares, the full price history in Excel, and from day 7, how each fare compares with its 7-day average. No travel agent is needed.

**How it was measured:**

- GitHub Actions run history: one completed check per day.
- `data/price_history.csv`: a new row for each fare, every day.
- `data/Flight_Price_Tracker.xlsx`: daily changes in dollars and percent, lowest price so far, and the 7-day average.
- The daily alert email itself, checked against Google Flights during testing.

## What it does

- Checks fares once a day (7:00 AM Central) for a round trip from St. Louis (STL) to St. Thomas (STT), 2 travelers, two April 2027 date windows
- Covers United and American, in Premium Economy and Business, with no overnight layovers
- Saves every day's price to a history file and rebuilds an Excel workbook with daily changes, drop flags, trend columns and a price chart
- Emails an alert when a fare is at or below a target price, or drops by a set percentage from the day before
- Makes each fare in the email a link that opens that fare's search on Google Flights
- Shares a pricing trend (up or down versus the 7-day average) once 7 days of data are in

## How it works

1. GitHub Actions starts the check on a daily schedule.
2. `tracker.py` asks SerpApi for Google Flights prices, one search per airline, cabin and date window (8 a day).
3. Results are filtered for the right airline and no overnight layovers, and the lowest qualifying fare is kept.
4. The price is added to `data/price_history.csv`, and `data/Flight_Price_Tracker.xlsx` is rebuilt.
5. If an alert rule is met, an email goes out with the workbook attached.
6. The new data is saved back to the repository.

## Setup

1. Create a private GitHub repository and add these files.
2. Get a SerpApi key and a Gmail app password.
3. In the repository, go to Settings > Secrets and variables > Actions and add four secrets: `SERPAPI_KEY`, `SMTP_USER`, `SMTP_PASSWORD` and `ALERT_EMAIL` (who receives alerts).
4. Open the Actions tab, choose "Daily flight price check" and click Run workflow to test.

To try the logic without keys: `python tracker.py --mock --no-email` uses fake prices.

## Check frequency

The tracker runs once a day. Airlines change fares throughout the day with no published schedule, so there is no exact moment to sync to. Checking more often multiplies the searches used and would likely require a paid SerpApi plan.

## Pricing trends and the road to prediction

The tracker records every day's price. The workbook shows daily changes in dollars and percent, the lowest price so far, and a 7-day average. From day 7, the email reports whether each fare is above or below its 7-day average.

This describes what has already happened. It does not forecast what will happen. We are now building up the price history so predictive AI can be layered on top. That needs about six months of data first, so the database has to fill up before prediction can be added.

## Limits

- Fare data does not include seat maps or seat counts.
- Prices from the data service can differ slightly from the airline's own site.
- A target-price alert repeats daily while fares stay at or below it.
- Trends start after 7 days of data.
- SerpApi's free plan allows 250 searches a month. At 8 a day, the tracker uses 240 to 248, which leaves little room for manual test runs.

## My role

Product manager and builder. I defined the requirements with the client, researched what AI platforms and travel sites already offer, chose the data source and architecture, wrote the alert message for an executive reader, and tested the system end to end.

## Tech

Python, GitHub Actions, SerpApi (Google Flights data), openpyxl, Gmail SMTP.

## Case study

See [case-study.md](case-study.md) for the research, design decisions and lessons learned.
