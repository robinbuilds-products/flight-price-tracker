# Case Study: Automating Flight Price Tracking Around the Holiday Price Drop

## The problem
A traveler booking premium-cabin flights for two people from St. Louis to St. Thomas wanted to buy at the best moment instead of paying a travel agent. Airlines often adjust fares around the holidays, but the timing is unpredictable and checking prices by hand every day is tedious and easy to forget. The flight price also decided when hotel prices would be finalized, so a missed drop delayed the whole trip plan.

## Requirements
- Two adults, round trip, two possible date windows in April 2027
- United and American, in Premium Economy or Business
- No overnight layovers
- Avoid specific booking sites the traveler distrusts
- A daily record of prices so the moment of a drop is visible
- Automatic email alerts, tested on the builder first and then switched to the traveler
- Bookings are made by the traveler directly, never by the tool

## Research: how existing AI flight trackers work
Before building, we looked at the flight trackers already offered by AI platforms and travel sites, and at where their data comes from.

**What exists (as of November 2026)**
- **Google AI Mode** added flight price tracking on August 27, 2026. You ask it to track prices in a chat and it emails you if prices change for your dates. Google says results draw on more than 300 partner airlines and travel sites.
- **Google Flight Deals** (beta) turns a plain-English trip description into fares and badges those at least 20% below the typical price.
- **Travel sites with built-in AI**, such as KAYAK's Ask AI, Expedia and Skyscanner, which also run apps inside ChatGPT, show live prices from their own systems.
- **Plug-in data services** connect live Google Flights-style fares to assistants such as Claude or ChatGPT, with a daily scheduled scan that alerts only when a fare is rated low.
- **General chatbots on their own** (ChatGPT, Claude, Gemini) are good for planning and research, but one review found them unreliable for live prices unless connected to a data source.

**Where the data comes from**
- The AI tools generally do not buy airline content directly. The AI is a layer on top of existing travel-data pipelines: a search engine's own flight data (Google's partner network), the booking sites' own inventory, or a data service.
- We found no public evidence of an AI company paying airlines directly for fare content, so we treat that as unconfirmed.
- Airlines supply fares to distributors and aggregators through the industry's usual booking systems and agreements.

**What the built-in tools do not cover**
- They do not keep a price history you can analyze, which is what shows *when* a drop happened.
- You cannot set your own rules, such as a percentage-drop threshold, a target price, or a two-window comparison across both airlines and both cabins.
- Seat maps are not part of fare data. They sit inside the airline's own booking flow, so no fare tracker can confirm that three seats are together in a row. That check has to be made on the airline's site at the moment of purchase.

This is why a custom tracker was still worth building: the platform tools alert on a price change, while this build records every day's price and flags the day the drop happens.

## Approach
1. **Define the rules first.** Search settings live in one config file, so changing dates or airlines needs no code changes.
2. **Use a data service instead of scraping.** Google Flights data comes through the SerpApi service. This avoids the excluded sites, and scraping airline pages is fragile and often against their terms.
3. **One search per option.** 2 date windows x 2 airlines x 2 cabins = 8 searches per day, about 240 a month, which fits a free plan.
4. **Filter, then pick the lowest.** Each result is checked for overnight layovers and the correct airline before the cheapest qualifying fare is logged.
5. **Keep history in plain files.** A CSV is the source of truth, and an Excel workbook is rebuilt from it each day with change amounts, percentages and DROP flags.
6. **Run on a schedule for free.** GitHub Actions runs the check daily, commits the new data and sends an email through a Gmail app password. Keys are stored as encrypted secrets, never in the code.
7. **Test before trusting.** A mock mode generates fake prices with a simulated drop, so the alert logic was tested without spending searches or sending email.

## Safeguards and quality control
- Alerts name the option, old price, new price and percentage change, and remind the reader to verify on the airline's site.
- The tracker never books anything; a person makes the purchase.
- Reruns on the same day replace that day's rows instead of duplicating them.
- If every lookup fails, a failure email is sent so silent breakage is noticed.
- A short written guide lets a non-technical person run the same search by hand with Copilot as a backup.

## Known limits
- Seat availability cannot be confirmed from price data (see the research above).
- Data-service prices can differ slightly from the airline's own site.
- Not yet confirmed: the data service's free-plan limit, and whether its price is the total for both travelers or per person.

## Results
Live results will be added here after the tracker has collected at least several weeks of data, including the day the drop was detected, the size of the drop, and how the purchase price compared with the earliest price tracked.

## Lessons
- Check what the platforms already offer before building. Their tools cover alerts; the gap is price history and custom rules.
- Writing the rules down before coding made the tool simple to change.
- A mock mode is the fastest way to test alert logic safely.
- Keeping secrets out of code and using a private repository protects client information.

## Sources
- Google, "3 new ways to plan and book travel in Search" (blog.google, August 27, 2026)
- Fello AI, "How to Find Cheap Flights with AI in 2026"
- FlightPowers, "Create your 24/7 AI travel agent"
- Blame the Fare, "The Best AI Flight Search Tools in 2026, Compared"
- Kiwi.com Magazine, "Best AI for Flights in 2026"
- The Convergence, "AI Travel Booking 2026"
