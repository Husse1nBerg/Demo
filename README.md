# DEMO Hotel Revenue Management System (RMS)

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





i. How is the recommended price calculated?
____________________________________________
The recommended price is calculated in the calculate_optimal_pricing function within the server/tools.py file. The calculation is a multi-step process that considers several factors:

. Base Price: The process starts by determining a base_price. If there is competitor data, the base price is set to 92% of the average competitor price to maintain a competitive rate. If there's no competitor data, it defaults to a market standard of $150.

. Demand Multipliers: The price is then adjusted based on market events.

    High-impact events increase the price by 35% (demand_multiplier = 1.35).
    Medium-impact events increase the price by 15% (demand_multiplier = 1.15).

. Day of the Week Adjustments: The price is further modified based on the day of the week, with weekends having higher multipliers:

    Friday: 20% increase
    Saturday: 25% increase
    Sunday: 10% increase
    Thursday: 5% increase

. Seasonal Adjustments: A seasonal multiplier is applied based on the hotel's location (Canada or US) and the month. For example, summer months in Canada have a 20% price increase.

. Lead Time Pricing: A lead time multiplier is also factored in. If the booking is less than 7 days away and there are high-impact events, the price is increased by 10%. If the booking is more than 60 days away, the price is decreased by 5%.

Final Price Calculation: The final recommended price is calculated by multiplying the base_price by all these multipliers (demand_multiplier, dow_multipliers, seasonal_multiplier, lead_time_multiplier).

 Constraints: The final price is constrained by the minimum and maximum price set in the hotel's configuration.




ii. How is revenue per available room calculated?
Revenue per available room (RevPAR) is calculated in two places: the create_fallback_data function in server/app.py and the get_key_performance_indicators and calculate_optimal_pricing functions in server/tools.py.

The formula used is:

revpar = adr * (projected_occupancy / 100)

Where:
    adr is the Average Daily Rate (which is the recommended price).
    projected_occupancy is the projected occupancy percentage for the given day.





iii. How is total revenue (daily projections) calculated?
The total projected revenue is calculated in the get_key_performance_indicators and calculate_optimal_pricing functions in server/tools.py and also in the fallback data creation in server/app.py.

The formula is:

total_revenue = rooms_sold * adr
                   |
                   |__ = total_rooms * (projected_occupancy / 100).

where:                       
    rooms_sold is the projected number of rooms sold
    adr is the Average Daily Rate (the recommended price).



    iv. The confidence percentage is calculated in the _calculate_confidence function in server/tools.py. It starts with a base confidence of 70% and is adjusted based on the following factors:

. Competitor Data Quality:

            +15% if there are 8 or more competitors.
            +10% if there are 5 to 7 competitors.
            +5% if there are 3 to 4 competitors.


. Event Intelligence:

            +10% if there are any market events.


. Lead Time:

            +10% for lead times between 7 and 30 days (considered the "sweet spot" for accuracy).
            -5% for lead times greater than 90 days.

The final confidence score is capped between a minimum of 65% and a maximum of 95%.




v. How are market events searched? Is it Tavily? Is it AI?
Market events are searched for using a combination of the Tavily Search API and an AI model. Here's the process:

Tavily Search: The search_events_with_tavily function in server/app.py makes a POST request to the Tavily API with a detailed query about major events, concerts, festivals, sports, etc., in the specified city and country around the given date.

AI Processing: The raw search results from Tavily are then passed to an AI model (Anthropic's Claude) within the get_ai_recommendation function. 
The AI is prompted to act as an expert hotel revenue management AI and to parse the results, identify the most important events, extract the correct dates, and combine them with its own knowledge of other relevant events. 

So, Tavily is used for the initial, real-time web search, and then an AI model processes and refines that information.





vi. How is the graph vs. occupancy trends chart generated? Is it from web search?

The "Price & Occupancy Trends" chart is generated from demo data created on the frontend. 
It is not from a web search. 
The generateDemoHistory function in client/src/App.js creates a 15-day history of prices and occupancy rates with simulated weekend effects and random events. 
This data is then used to populate the chart.



vii. How is the 7-day demand forecast generated? What data is it pulling?

The forecast is based on the AI's general knowledge and the data it was trained on; it does not appear to be pulling from a live, real-time data source for this specific feature.

The 7-day demand forecast is generated by an AI model. 
The /api/demand-forecast endpoint in server/app.py calls the get_demand_forecast function in server/tools.py. 

This function sends a prompt to the Claude AI model, asking it to create a 90-day demand forecast for a hotel with the given star rating in the specified city and country. 
The AI is instructed to provide a demand level (low, medium, high, peak) and a key driver for each day. 
If the AI fails to generate a forecast, the application falls back to providing a 7-day forecast with "Standard demand" as the driver. 



viii. how are OTA comissions calculated? 

The monthly OTA commission and potential savings are calculated in the calculate_direct_booking_savings function in server/tools.py. The calculation is a simplified model and uses several hardcoded assumptions:

Average OTA commission rate: 18%. This is a fairly standard commission rate in the hotel industry, which can range from 15% to 25% or even higher.
OTA booking percentage: 40% of all bookings are assumed to come from OTAs.
Potential for shift to direct bookings: 25% of OTA bookings are assumed to be shiftable to direct bookings.

The potential monthly savings are generated from the idea that if the hotel can convince 25% of the guests who would have booked through an OTA to book directly with the hotel instead, the hotel would save the 18% commission on those bookings.




ix. What database is it using? 

The application uses SQLite, which is a serverless, self-contained, transactional SQL database engine. The init_database function in server/app.py creates a local file named amplifi_hotel.db if it doesn't exist and sets up the necessary tables.

it's a file on the local filesystem where the backend server is running. The data persists when you relaunch the web app because it's being written to and read from this local file.




HOW TO MAXIMIZE REVENUE:
________________________

1. Boost Direct Bookings to Avoid OTA Commissions
    how: Use a high-conversion booking engine like innQuest making it easy for guests to book directly. Offer incentives for bokoking directly

2. Implement Dynamic and Intelligent Rate Management
   Your pricing should not be static. It needs to adapt to market conditions in real-time to maximize both Average Daily Rate (ADR) and Revenue Per Available Room (RevPAR).

3. Centralize and Streamline Operations
   Efficiency is key to profitability. The more you can automate and centralize your operations, the more time you and your staff have to focus on guest experience and revenue-generating activities.

   how: invest in better property management systems

4. Focus on Guest Lifetime Value (LTV): Shift from viewing bookings as single transactions and focus on long-term revenue potential. 
   Create guest profiles to understand booking behavior and spending patterns.

5. Maximize Ancillary Revenue

6. Integrate Total Property Revenue: 
     Break down departmental silos. Align F&B and meeting space operations with hotel occupancy and demand patterns to maximize overall revenue.

7. Leverage Technology: Use an integrated system with a PMS (roomMaster), Channel Manager, and Booking Engine to automate and streamline operations. 
