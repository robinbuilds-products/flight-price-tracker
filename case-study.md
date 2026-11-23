# Case Study: Automating Flight Price Tracking Around the Holiday Price Drop

Built with Microsoft Copilot in a single day: about three hours in total, including QA testing and refining the email message.

## The problem
A client booking premium-cabin flights for two wanted to buy at the best moment, without a travel agent and without checking prices by hand every day. She also wanted to see how much, and in which direction, prices were changing, in dollars and percent. The flight price also decided when hotel prices could be finalized, so a missed drop delayed the whole trip plan.

## How it started
The client first tried to build a tracker herself with Copilot in her personal Microsoft 365 account, as a way to learn to build with AI. She wasn't getting the results she wanted, so she asked me to build an AI flight tracker using Google Flights data.

I had Copilot clarify what the issue was with her first attempt: Copilot couldn't get live Google Flights prices on its own. That told me the first job was finding a reliable price source. Before any build work started, I also asked the client what outcome she wanted. That outcome is what was delivered.

## Requirements
- Two adults, round trip, St. Louis to St. Thomas, two April 2027 date windows
- United and American, in Premium Economy or Business, with no overnight layovers
- Avoid booking sites the client distrusts
- A daily record of prices, so the day of a drop is visible
- Automatic email alerts, tested on me first and then switched to the client
- The tool never books anything; the client books directly

## Research: what AI platforms already offer
Before building, I looked at the flight trackers already offered by AI platforms and travel sites, and at where their data comes from.

- **Google AI Mode** added flight price tracking on August 27, 2026. You ask it to track prices in a chat, and it emails you if prices change for your dates. Google says results draw on more than 300 partner airlines and travel sites.
- **Google Flight Deals** (beta) turns a plain-English trip description into fares and badges those at least 20% below the typical price.
- **Travel sites with built-in AI**, such as KAYAK, Expedia and Skyscanner, show live prices from their own systems.
- **Plug-in data services** connect live Google Flights-style fares to assistants such as Claude or ChatGPT.
- **General chatbots on their own** are good for planning, but one review found them unreliable for live prices unless connected to a data source.

The AI tools generally don't buy airline content directly. They sit on top of existing travel-data pipelines. I found no public evidence of an AI company paying airlines directly for fare content, so I treat that as unconfirmed.

**What the built-in tools don't cover:** a price history you can analyze, your own alert rules, and a comparison across both airlines, both cabins and both date windows. Fare data also doesn't include seat maps. That gap is why a custom tracker was still worth building.

## The first challenge
The first challenge was finding a reliable way to get flight information that includes prices without paying for a service. Along the way, I learned why this is hard: booking data is often shared, but airlines only give live pricing to sellers that turn searches into bookings. This is called the look-to-book ratio, for example, one booking expected for every 1,500 searches. I explored the options with Copilot and chose a solution before building anything. We decided to build in GitHub rather than inside Copilot itself. GitHub is owned by Microsoft, so this keeps the code in the Microsoft ecosystem and makes it easy to share with anyone who wants the same kind of tracker.

## Approach
1. **Rules first.** Search settings live in one config file, so changing dates, airlines, cabins or the alert level needs no code changes.
2. **A data service instead of scraping.** Google Flights data comes through SerpApi. That avoids the sites the client dislikes, and scraping airline pages is fragile.
3. **One search per option.** 2 date windows x 2 airlines x 2 cabins is 8 searches a day, 240 to 248 a month. SerpApi's free plan allows 250 a month, so the daily run costs nothing. I also estimated the cost if the client wants the tracker to run longer to build up the price history.
4. **Filter, then pick the lowest.** Each result is checked for the right airline and no overnight layovers before the cheapest qualifying fare is logged.
5. **Plain-file history.** A CSV is the source of truth, and an Excel workbook is rebuilt from it each day with changes, drop flags, trend columns and a price chart.
6. **A free daily schedule.** GitHub Actions runs the check at 7:00 AM Central, saves the data and sends the email through Gmail. Keys are stored as encrypted secrets, never in the code.
7. **Two alert rules.** An email goes out when a fare is at or below a target price, or drops by a set percentage from the day before.

## Designing the email
The email is written for an executive who values clear, literal wording. After several rounds of edits, the final message:
- States up front that it is automated.
- Lists the fares by date window, and makes each fare a link that opens that fare's search on Google Flights.
- Reminds her of her alert level and why she is receiving the email.
- Shows a pricing trend. For the first 7 days it explains that daily changes are in the attached file. From day 7, it reports whether each fare is above or below its 7-day average.
- Explains why Premium Economy isn't shown, when no fares are available.
- Ends with "Does the price look right?", a prompt to check the airline's website, and how to stop the emails.

After review, I cut a disclaimer and a repeated mention of the attachment. I also wrote the subject line to say exactly what the email is: "Automated flight price alert: STL to STT, April 2027".

## Testing the live build
I checked the first live run against Google Flights in a browser. That caught problems a fake-price test could not.
- **Wrong cabin codes.** The first run logged almost identical prices for Premium Economy and Business. Opening the saved link showed the search was set to First. The data service numbers cabins 1 = Economy, 2 = Premium Economy, 3 = Business, 4 = First, and my config was off by one. After the fix, the browser showed Business with the same price the tracker logged.
- **No Premium Economy fares.** After the fix, Premium Economy rows disappeared. Google Flights showed no results for that cabin on these dates, so the tracker was right to log nothing.
- **Price basis confirmed.** Google's page states that prices include taxes and fees for 2 adults, so the logged total covers both travelers.
- **Email sender.** My first attempt to send from a custom-domain Zoho mailbox kept failing at the sign-in step, even after I tried two servers and two connection methods. I switched to Gmail, which works, and deleted the unused Zoho app password.
- **Email alert confirmed.** With a target price above the current fares, the next run sent the alert, which confirmed the full chain from price pull to inbox.

## Pricing trends and the road to AI prediction
The tracker records every day's price. The workbook shows daily changes in dollars and percent, the lowest price so far and a 7-day average. This describes what has already happened. It does not forecast what will happen.

AI price prediction needs months of daily data, including the holiday period, to be reliable. We are now building up the price history so predictive AI can be layered on top. That needs about six months of data first, so the database has to fill up before prediction can be added.

## Safeguards
- The tracker never books anything; a person makes the purchase.
- Reruns on the same day replace that day's rows instead of duplicating them.
- If every lookup fails, a failure email is sent so silent breakage is noticed.
- Keys are stored as encrypted secrets and are never in the code.

## Limits
- Fare data does not include seat maps or seat counts.
- Prices from the data service can differ slightly from the airline's own site.
- A target-price alert repeats daily while fares stay at or below the target.
- Trends start after 7 days of data.
- SerpApi's free plan allows 250 searches a month. At 8 a day, the tracker uses 240 to 248, which leaves little room for manual test runs.

## Outcome so far
The tracker is delivered, tested and running once a day. After the test phase, alerts were switched from my inbox to the client's, as planned. I walked the client through the solution and the email to see if any changes or tweaks were needed. None were. We are now building up the price history so predictive AI can be layered on top. Results, including the day a drop is detected, its size and how the purchase price compares with the earliest price tracked, will be added here once the client books.

## Cost and time
- Time: about three hours in total, including QA testing and refining the email message, in one day.
- Cost: about one day's worth of Copilot Cowork usage.

## Lessons
- Check what the platforms already offer before building. Their tools cover alerts. The gap is price history and custom rules.
- Test against the real source early. A fake-data test can't catch a wrong setting, but a ten-minute comparison with the live website did.
- Keep the rules in one config file, so fixes are one-line changes.
- Write for the reader. An executive needs plain labels, a clear reason for the email and an easy way to stop it.
- Be honest about what the data can and can't do. Trends describe the past, and prediction needs more data.

## Sources
- Google, "3 new ways to plan and book travel in Search" (blog.google, August 27, 2026)
- Fello AI, "How to Find Cheap Flights with AI in 2026"
- FlightPowers, "Create your 24/7 AI travel agent"
- Blame the Fare, "The Best AI Flight Search Tools in 2026, Compared"
- Kiwi.com Magazine, "Best AI for Flights in 2026"
- The Convergence, "AI Travel Booking 2026"
