# AmpliFi Hotel Revenue Management System Clone

A professional hotel revenue management system built with React and Flask, featuring AI-powered pricing recommendations.

## Features
- Real-time AI pricing recommendations
- Competitor analysis
- Market intelligence
- KPI dashboards
- Multi-location support (US & Canada)
- Auto-pilot mode

## Quick Start

1. Backend Setup:
```bash
cd server
pip install -r requirements.txt
python app.py


2. frontend Setup:
```bash
cd client
npm start






##Frequently Asked Questions:


i. How is the recommended price calculated?
---------------------------------------------
        The recommended price is calculated in the calculate_optimal_pricing function in server/tools.py. 
        It's a dynamic process that synthesizes live market data rather than using fixed rules.

        Analyze Competitor Pricing: The system first fetches a list of competitor hotel prices for the target date using live API calls (primarily from SerpApi). It then calculates key statistical benchmarks from this data, including the average price, median, and the 25th and 75th percentiles.

        Determine Base Price from Market Position: Instead of a fixed percentage, the base price is strategically determined by the hotel's star rating relative to the live market data:

            4-5 Star Hotels (Premium): The base price is set to the 75th percentile of competitor prices (high-end option)
            3 Star Hotels (Market Rate): The base price is set to the median price to stay competitive with the bulk of the market.
            1-2 Star Hotels (Value): The base price is set to the 25th percentile to attract budget-conscious travelers.

        Apply Live Demand Multipliers: The price is then adjusted based on a total_multiplier derived from real-time factors:

        Market Events: High-impact events (concerts, major conferences) found via PredictHQ and Ticketmaster APIs significantly increase the multiplier.

        Day of the Week: Weekends (especially Saturday) have a higher built-in multiplier to capture leisure travel demand.

        Seasonality: Summer and holiday seasons increase the multiplier, while the off-season (January-February) decreases it.

        Lead Time: Bookings made at the last minute (0-3 days out) receive a price increase to capture urgent demand.

        Final Price Calculation: The final price is base_price * total_multiplier. This result is then constrained by the minPrice and maxPrice set in the hotel's configuration to ensure it never goes outside acceptable bounds.






ii. How is revenue per available room (RevPAR) calculated?
---------------------------------------------------------

Revenue per available room (RevPAR) is a key performance indicator calculated in the calculate_optimal_pricing function in server/tools.py. The formula remains the same, but the inputs are now dynamic.

The formula is: 

                    RevPAR = ADR × (ProjectedOccupancy/100)


where:  ADR (Average Daily Rate): This is the dynamically calculated recommended price for the day.
        Projected Occupancy: calculated in the _calculate_occupancy function by taking the hotel's baseOccupancy and adjusting it based on the demand level (derived from live market events) and the hotel's price competitiveness (how the final recommended price compares to the live competitor average).





iii. How is total revenue (daily projection) calculated?
---------------------------------------------------------

The total projected daily revenue is also calculated in the calculate_optimal_pricing function in server/tools.py. 
The calculation relies on the live, dynamic outputs of the pricing engine.

The formula is: 

                                TotalRevenue = RoomsSold × ADR



where:    

. Rooms Sold: This is calculated by taking the totalRooms for the hotel *  calculated projected_occupancy.
. ADR (Average Daily Rate): This is the final recommended price.

Essentially, the system projects revenue based on how many rooms it expects to sell at the optimal price it calculated for that specific day's market conditions.





iv. How is the confidence percentage calculated?
------------------------------------------------


The confidence percentage is calculated in the _calculate_confidence function in server/tools.py. 
It starts at a base of 50% and is built up based on the quality and quantity of live data available for the recommendation.

        Competitor Data Quality:
        ........................
        +25% for 20+ competitors found.
        +20% for 10-19 competitors.
        +15% for 5-9 competitors.

        The more real-time prices the system can analyze, the higher the confidence.



        Event Intelligence:
        ...................
        +15% for 5+ market events found.
        +10% for 2-4 events.

        The more event data available, the better the system understands demand drivers.



        Market Stability:
        .................
        +10% if the standard deviation of competitor prices is low (less than $30), indicating a stable, predictable market.

        The final score is capped at a maximum of 95%. A higher score means the recommendation is based on a wealth of high-quality, real-time data.





v. How are market events searched?
----------------------------------

Market events are sourced from multiple, specialized, live APIs, not a general web search tool like Tavily. This provides structured, high-quality data.

The get_market_intelligence function in server/tools.py aggregates data from:

PredictHQ API: A professional-grade event intelligence platform that provides data on conferences, festivals, sports, and community events, including their predicted impact.

Ticketmaster API: A direct source for concerts, theater shows, and major sporting events, providing real-time information on what's happening in the city.

Calendar & Seasonal Analysis: The system also programmatically identifies weekends, major public holidays, and seasonal demand periods (e.g., summer peak season) to supplement the API data.

The application does not use an AI model to parse unstructured web search results for events; it uses direct API connections for more reliable and accurate data.





vi. How is the Price vs. Occupancy trends chart generated
----------------------------------------------------------

The "Price & Occupancy Trends" chart is generated from real historical performance data stored in the application's own database. It is not demo data.

Here's the process:

Data Logging: Every time a successful AI recommendation is generated, the key results (price, projected occupancy, RevPAR, ADR) are saved to the price_history table in the amplifi_hotel.db database file.

Data Fetching: The frontend fetchPriceHistory function calls the /api/historical-performance endpoint on the backend.

Backend Response: The backend queries the price_history table and returns the last 14 days of saved, real data points for the selected location.

Fallback Generation: If no historical data exists for a location, the generate_historical_data_from_sources function in tools.py intelligently backfills the chart. It does this by running the pricing engine on past dates using real historical competitor data, creating a realistic and accurate historical view.





vii. How is the 7-day demand forecast generated?
------------------------------------------------

The 7-day demand forecast is generated by running the application's live market intelligence engine for each of the next seven days. 
It is not based on general AI knowledge.

The /api/demand-forecast endpoint calls the get_demand_forecast function in tools.py. This function:

    Loops through the next 7 days.
    For each day, it makes live API calls to PredictHQ and Ticketmaster to find all real events occurring on that specific day.
    It analyzes the impact and volume of these events to determine a demand level (low, medium, high, or peak).
    The "driver" listed for each day is typically the most significant event found (e.g., "Weekend Travel," "Toronto Maple Leafs Game," "Tech Conference").

This ensures the forecast is grounded in actual, scheduled events that will drive hotel bookings.





viii. How are OTA commissions calculated?
-----------------------------------------

The OTA commission calculations in calculate_direct_booking_savings are now based on data stored in the local database, making it specific to the hotel.

Real Commission Rates: When a new hotel is added, the system populates the ota_commissions table with default but realistic commission rates and booking percentages for major OTAs (Booking.com, Expedia, etc.). These values can be customized for each hotel.

Weighted Average: The system calculates a weighted average commission rate based on what percentage of bookings comes from each OTA.

Dynamic Calculation: The calculation uses the hotel's totalRooms, baseOccupancy, and average rate from its configuration to estimate total monthly revenue.

Savings Model: It then applies the weighted average commission rate to the portion of revenue generated by OTAs to find the total monthly commission paid. The "potential savings" are based on a realistic goal of shifting 25% of those OTA bookings to commission-free direct channels.





ix. What database is it using?
------------------------------

The application uses SQLite. The init_database function in server/app.py creates a local file named amplifi_hotel.db in the server/ directory.

This is a serverless, file-based database, meaning all your application's data—hotel configurations, historical pricing data, OTA commission rates—is stored directly in that single file. This makes the application self-contained and allows data to persist between sessions without needing a separate database server.




##The "Chicken and Egg" Problem

The solution is not to beat Expedia at being a search engine, but to provide a better value proposition once a customer discovers your hotel. You have to give them a compelling reason to make the extra click to your website.

1. Make the Direct Offer Irresistible
You have to reward the customer for booking directly. The key is to offer exclusive perks that OTAs cannot.

Best Rate Guarantee: This is the minimum. Promise that the price on your website is the lowest available anywhere.

Exclusive Perks: This is where you win. Offer tangible benefits that are only available to guests who book direct:

    A complimentary room upgrade
    Free breakfast
    A welcome drink upon arrival
    Guaranteed late check-out
    Extra loyalty points

The message becomes: "Find us on Expedia, but book with us directly to get more for your money."



2. Convert OTA Guests into Direct Customers (The Trojan Horse)
Even if a guest finds you and books through an OTA for their first stay, you have a golden opportunity to capture them for all future stays.

        At Check-In: This is your most important customer interaction. The front desk staff should be trained to say: "We're so glad you're staying with us! Just so you know for next time, when you book on our website you get free breakfast and a potential room upgrade."

        During the Stay: Place a small card in the room with a QR code that leads to your booking page with a special "Welcome Back" discount.

        After the Stay: An OTA often masks the guest's real email. But if you can get it at check-in, you can add them to your marketing list and send them exclusive offers that are better than what they'd find on an OTA.

The goal is to pay the OTA commission once to acquire the customer, then make all their future business commission-free.



3. Build a Brand That Bypasses the Middleman

A truly great guest experience is the ultimate marketing tool. If guests love your hotel, they won't search for "hotels in Montreal" on their next trip. They will search for "Your Hotel's Name" directly, and your website should be the first result.

How Your App Helps
This is where your Direct Booking Intelligence tab is so powerful. It provides the "why."

It shows the hotel manager in stark, undeniable terms how much money is leaving their pocket every month.

The "Estimated Monthly OTA Commissions" isn't just a number; it's the marketing budget. It's the financial pain point that motivates the manager to invest in the strategies above.

The "Potential Monthly Savings" is the concrete goal. It turns an abstract idea ("we should get more direct bookings") into a measurable target: "We need to implement a plan to save that $3,000 in commission fees."