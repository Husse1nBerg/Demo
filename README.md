# Hotel Revenue Management System (RMS)

A **professional hotel revenue management system** built with **React** (frontend) and **Flask** (backend), featuring **AI-powered pricing recommendations** and real-time market intelligence.  

---

##  Features

-  **Real-time AI pricing recommendations**  
-  **Competitor analysis**  
-  **Market intelligence & demand forecasting**  
-  **KPI dashboards** (RevPAR, ADR, Total Revenue, Occupancy)  
-  **Multi-location support** (US & Canada)  
-  **Auto-pilot mode** (hands-free optimization)  

---

## ⚡ Quick Start

### 1. Backend Setup
```bash
cd server
pip install -r requirements.txt
python app.py
```

### 2. Frontend Setup
```bash
cd client
npm start
```

---

## ❓ Frequently Asked Questions (FAQ)

### 1. How is the **recommended price** calculated?  
The price recommendation is generated in `server/tools.py` (`calculate_optimal_pricing`).  
It dynamically synthesizes **live market data** instead of relying on fixed rules.  

**Process:**
1. **Analyze Competitor Pricing** (via SerpApi) → average, median, 25th & 75th percentiles.  
2. **Set Base Price by Market Position**:  
   - ⭐⭐⭐⭐ – ⭐⭐⭐⭐⭐: 75th percentile (premium positioning)  
   - ⭐⭐⭐                  : Median price (market competitive)  
   - ⭐–⭐⭐                 : 25th percentile (value-focused)  
3. **Apply Demand Multipliers**:  
   -  Market Events (via PredictHQ, Ticketmaster) → price up  
   -  Weekends → price up  
   -  Seasonality → peak vs. off-season adjustment  
   -  Lead Time → last-minute bookings increase rate  
4. **Final Price** = `base_price × total_multiplier`  
   - Constrained by `minPrice` and `maxPrice` from configuration.  

---

### 2. How is **RevPAR** calculated?  
Formula:  
```
RevPAR = ADR × (ProjectedOccupancy / 100)
```
- **ADR** = dynamically recommended price  
- **Projected Occupancy** = calculated from base occupancy, demand events, and price competitiveness  

---

### 3. How is **Total Revenue** calculated?  
Formula:  
```
TotalRevenue = RoomsSold × ADR
```
- **Rooms Sold** = totalRooms × projectedOccupancy  
- **ADR** = final recommended price  

---

### 4. How is the **confidence percentage** calculated?  
Defined in `tools.py::_calculate_confidence`.  

- Base = **50%**  
- **Competitor Data Quality**: +25% (20+ competitors), +20% (10–19), +15% (5–9)  
- **Event Intelligence**: +15% (5+ events), +10% (2–4 events)  
- **Market Stability**: +10% (if price deviation < $30)  
- **Capped at 95%**  

---

### 5. How are **market events** sourced?  
- **PredictHQ API** → Conferences, festivals, sports, community events  
- **Ticketmaster API** → Concerts, theater, sports  
- **Seasonal Analysis** → Weekends, holidays, peak travel seasons  

 No generic web search parsing → only structured, reliable APIs.  

---

### 6. How is the **Price vs. Occupancy Trends** chart generated?  
- **Data Logging**: AI recommendations stored in `price_history` (SQLite)  
- **API Endpoint**: `/api/historical-performance` returns last 14 days  
- **Fallback**: `generate_historical_data_from_sources` backfills realistic history using past competitor data  

---

### 7. How is the **7-day demand forecast** generated?  
- Endpoint: `/api/demand-forecast` → `tools.py:get_demand_forecast`  
- Steps:  
  1. Loop through next 7 days  
  2. Fetch live events via PredictHQ & Ticketmaster  
  3. Assign demand levels (low, medium, high, peak)  
  4. Highlight main driver (e.g., *“Toronto Maple Leafs Game”*)  

---

### 8. How are **OTA commissions** calculated?  
- Stored in local `ota_commissions` table  
- **Weighted average commission rate** based on booking share  
- **Dynamic monthly savings model**: projects savings if 25% of OTA bookings are shifted to direct bookings  

---

### 9. What **database** is used?  
- **SQLite** (`amplifi_hotel.db`)  
- Created in `server/app.py:init_database`  
- Stores hotel configs, pricing history, OTA commissions, etc.  

---

##  The "Chicken & Egg" Problem: Driving Direct Bookings

Hotels must offer **better value propositions** to encourage guests to book directly rather than via OTAs like Expedia.

### 1. Make Direct Offers Irresistible  
-  Best Rate Guarantee  
-  Exclusive perks (room upgrade, free breakfast, late checkout, loyalty points)  

### 2. Convert OTA Guests into Direct Customers (Trojan Horse)  
-  **At Check-in** → Train staff to upsell direct perks  
- 🛏 **During Stay** → Place QR code for direct discounts  
-  **After Stay** → Capture guest emails, send exclusive offers  

### 3. Build a Brand That Bypasses OTAs  
- Deliver **exceptional guest experience** → Guests search for your hotel by name  

---

##  How This App Helps  

The **Direct Booking Intelligence Tab** shows:  
-  *Estimated Monthly OTA Commissions* → Pain point (lost revenue)  
-  *Potential Monthly Savings* → Clear, measurable target  

> Example: “We can save **$3,000/month** in OTA commissions if 25% of guests book directly.”

