import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from server.tools import EnhancedHotelAnalytics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(
    app,
    origins=["http://localhost:3000"],
    supports_credentials=True,
    methods=["GET", "POST", "OPTIONS"],
)

# API configurations
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


@contextmanager
def get_db_connection():
    conn = sqlite3.connect("amplifi_hotel.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                hotel_name TEXT NOT NULL, 
                location TEXT NOT NULL,
                total_rooms INTEGER NOT NULL, 
                base_occupancy INTEGER NOT NULL, 
                min_price REAL NOT NULL,
                max_price REAL NOT NULL, 
                star_rating INTEGER DEFAULT 3, 
                is_active BOOLEAN DEFAULT 1,
                auto_mode BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ancillary_revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                hotel_id INTEGER, 
                name TEXT NOT NULL,
                description TEXT, 
                suggested_price REAL, 
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hotel_id) REFERENCES hotel_configs (id)
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ota_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                hotel_id INTEGER, 
                ota_name TEXT NOT NULL,
                commission_rate REAL NOT NULL,
                booking_percentage REAL DEFAULT 0.4,
                FOREIGN KEY (hotel_id) REFERENCES hotel_configs (id)
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS competitor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                location TEXT, 
                hotel_name TEXT,
                price REAL, 
                stars REAL,
                brand TEXT,
                distance TEXT, 
                source TEXT, 
                date_collected TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                location TEXT, 
                event_name TEXT,
                event_date TEXT, 
                impact_level TEXT, 
                description TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                location TEXT, 
                target_date TEXT,
                recommended_price REAL, 
                occupancy REAL, 
                revpar REAL, 
                adr REAL,
                revenue REAL, 
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert default hotel only if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM hotel_configs")
        if cursor.fetchone()["count"] == 0:
            cursor.execute(
                """
                INSERT INTO hotel_configs 
                (hotel_name, location, total_rooms, base_occupancy, min_price, max_price, star_rating, auto_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                ("Our Hotel", "Montreal, Canada", 100, 65, 80, 500, 3, 1),
            )

            # Add default OTA commission rates
            hotel_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO ota_commissions (hotel_id, ota_name, commission_rate, booking_percentage)
                VALUES (?, ?, ?, ?), (?, ?, ?, ?), (?, ?, ?, ?)
            """,
                (
                    hotel_id,
                    "Booking.com",
                    0.18,
                    0.25,
                    hotel_id,
                    "Expedia",
                    0.20,
                    0.20,
                    hotel_id,
                    "Hotels.com",
                    0.15,
                    0.15,
                ),
            )

        conn.commit()
        logger.info("Database initialized successfully")


# API Routes
@app.route("/api/hotels", methods=["GET", "POST", "OPTIONS"])
def manage_hotels():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "GET":
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM hotel_configs WHERE is_active = 1 ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                hotels = [
                    {
                        "id": row["id"],
                        "hotelName": row["hotel_name"],
                        "location": row["location"],
                        "totalRooms": row["total_rooms"],
                        "baseOccupancy": row["base_occupancy"],
                        "minPrice": row["min_price"],
                        "maxPrice": row["max_price"],
                        "starRating": row["star_rating"],
                        "autoMode": bool(row["auto_mode"]),
                        "createdAt": row["created_at"],
                    }
                    for row in rows
                ]
                return jsonify({"success": True, "hotels": hotels})
        except Exception as e:
            logger.error(f"Error fetching hotels: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == "POST":
        try:
            data = request.get_json()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO hotel_configs 
                    (hotel_name, location, total_rooms, base_occupancy, min_price, max_price, star_rating, auto_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data.get("hotelName"),
                        data.get("location"),
                        data.get("totalRooms"),
                        data.get("baseOccupancy"),
                        data.get("minPrice"),
                        data.get("maxPrice"),
                        data.get("starRating", 3),
                        1,  # Default auto_mode to true
                    ),
                )

                hotel_id = cursor.lastrowid

                # Add default OTA commissions for new hotel
                cursor.execute(
                    """
                    INSERT INTO ota_commissions (hotel_id, ota_name, commission_rate, booking_percentage)
                    VALUES (?, ?, ?, ?), (?, ?, ?, ?), (?, ?, ?, ?)
                """,
                    (
                        hotel_id,
                        "Booking.com",
                        0.18,
                        0.25,
                        hotel_id,
                        "Expedia",
                        0.20,
                        0.20,
                        hotel_id,
                        "Hotels.com",
                        0.15,
                        0.15,
                    ),
                )

                conn.commit()
                return jsonify({"success": True, "hotel_id": hotel_id})
        except Exception as e:
            logger.error("Error creating hotel: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/price-recommendation", methods=["POST", "OPTIONS"])
def get_price_recommendation():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        location = data.get("location", {})
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        hotel_config = data.get("hotelConfig", {})

        city = location.get("city", "Montreal")
        country = location.get("country", "Canada")

        logger.info(f"Getting price recommendation for {city}, {country} on {date}")

        analytics = EnhancedHotelAnalytics()

        # Get real competitor data from multiple sources
        competitors = analytics.get_comprehensive_competitor_analysis(
            city, country, date
        )

        if not competitors:
            logger.warning(
                "No competitor data available, attempting alternative sources..."
            )
            competitors = analytics.get_fallback_competitor_data(city, country, date)

        logger.info(f"Found {len(competitors)} competitors from live data sources")

        # Get real market events
        market_intel = analytics.get_market_intelligence(city, country, date)

        # Calculate pricing based on real data
        pricing_result = analytics.calculate_optimal_pricing(
            f"{city}, {country}", date, hotel_config, competitors, market_intel
        )

        # Build comprehensive recommendation
        recommendation = {
            "recommended_price": pricing_result["recommended_price"],
            "confidence": pricing_result["confidence_score"],
            "reasoning": pricing_result["reasoning"],
            "competitors": competitors[:20],  # Limit to top 20 for UI performance
            "market_events": market_intel.get("market_events", [])[:10],  # Limit events
            "kpis": pricing_result["kpis"],
            "market_position": pricing_result["market_position"],
            "pricing_strategy": pricing_result.get("pricing_strategy", "Dynamic"),
            "demand_level": pricing_result.get("demand_level", "medium"),
            "market_factors": pricing_result.get("market_factors", []),
            "detailed_analysis": pricing_result.get("detailed_analysis", {}),
        }

        # Store in database for historical tracking
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO price_history 
                (location, target_date, recommended_price, occupancy, revpar, adr, revenue, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"{city}, {country}",
                    date,
                    pricing_result["recommended_price"],
                    pricing_result["kpis"].get("projected_occupancy", 0),
                    pricing_result["kpis"].get("revpar", 0),
                    pricing_result["kpis"].get("adr", 0),
                    pricing_result["kpis"].get("projected_revenue", 0),
                    pricing_result["confidence_score"],
                ),
            )
            conn.commit()

        logger.info(
            f"Recommendation generated with {pricing_result['confidence_score']*100:.1f}% confidence"
        )

        return jsonify({"success": True, "data": recommendation})

    except Exception as e:
        logger.error(f"Error in price recommendation endpoint: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/price-override", methods=["POST", "OPTIONS"])
def price_override():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        desired_rank = data.get("desiredRank", 1)
        competitors = data.get("competitors", [])
        hotel_config = data.get("hotelConfig", {})

        if not competitors:
            return (
                jsonify({"success": False, "error": "No competitor data available"}),
                400,
            )

        # Sort competitors by price
        sorted_competitors = sorted(
            competitors, key=lambda x: x.get("price", 0), reverse=True
        )

        # Calculate target price based on desired ranking
        if desired_rank <= len(sorted_competitors):
            if desired_rank == 1:
                # Premium positioning - 5% above highest
                target_price = sorted_competitors[0]["price"] * 1.05
            else:
                # Position between competitors
                higher_price = sorted_competitors[desired_rank - 2]["price"]
                lower_price = (
                    sorted_competitors[desired_rank - 1]["price"]
                    if desired_rank - 1 < len(sorted_competitors)
                    else higher_price * 0.95
                )
                target_price = (higher_price + lower_price) / 2
        else:
            # Value positioning - below lowest competitor
            lowest_price = sorted_competitors[-1]["price"]
            target_price = lowest_price * 0.95

        # Apply hotel's price boundaries
        min_price = hotel_config.get("minPrice", 80)
        max_price = hotel_config.get("maxPrice", 500)
        target_price = max(min_price, min(max_price, target_price))

        # Calculate KPIs based on positioning
        base_occupancy = hotel_config.get("baseOccupancy", 65)
        total_rooms = hotel_config.get("totalRooms", 100)

        # Price elasticity model
        avg_competitor_price = (
            sum(c["price"] for c in competitors) / len(competitors)
            if competitors
            else target_price
        )
        price_ratio = (
            target_price / avg_competitor_price if avg_competitor_price > 0 else 1.0
        )

        # Occupancy adjustment based on price positioning
        if price_ratio > 1.2:  # Premium pricing
            occupancy_adjustment = 0.85
            positioning = "premium"
        elif price_ratio > 1.05:  # Slightly above market
            occupancy_adjustment = 0.92
            positioning = "upscale"
        elif price_ratio < 0.85:  # Value pricing
            occupancy_adjustment = 1.15
            positioning = "value"
        elif price_ratio < 0.95:  # Below market
            occupancy_adjustment = 1.08
            positioning = "competitive-value"
        else:  # Market rate
            occupancy_adjustment = 1.0
            positioning = "competitive"

        projected_occupancy = min(95, max(30, base_occupancy * occupancy_adjustment))
        rooms_sold = int(total_rooms * (projected_occupancy / 100))
        revpar = target_price * (projected_occupancy / 100)
        total_revenue = rooms_sold * target_price

        return jsonify(
            {
                "success": True,
                "override_price": round(target_price, 2),
                "market_rank": desired_rank,
                "kpis": {
                    "projected_occupancy": round(projected_occupancy, 1),
                    "adr": round(target_price, 2),
                    "revpar": round(revpar, 2),
                    "projected_revenue": round(total_revenue, 2),
                    "rooms_sold": rooms_sold,
                },
                "positioning": positioning,
            }
        )

    except Exception as e:
        logger.error(f"Error in price override: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/demand-forecast", methods=["POST", "OPTIONS"])
def demand_forecast():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        location = data.get("location", {})
        hotel_config = data.get("hotelConfig", {})

        analytics = EnhancedHotelAnalytics()

        # Get real demand forecast based on actual events and patterns
        forecast = analytics.get_demand_forecast(
            location.get("city"), location.get("country"), hotel_config
        )

        # Ensure we return at least 7 days of forecast
        if not forecast or len(forecast) < 7:
            logger.warning(
                "Insufficient forecast data, generating based on historical patterns"
            )
            forecast = analytics.generate_pattern_based_forecast(
                location.get("city"), location.get("country"), 7
            )

        return jsonify(
            {"success": True, "forecast": forecast[:7]}
        )  # Return 7 days for UI

    except Exception as e:
        logger.error(f"Error in demand forecast endpoint: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ancillary-revenue", methods=["POST", "OPTIONS"])
def ancillary_revenue():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        hotel_config = data.get("hotelConfig", {})

        analytics = EnhancedHotelAnalytics()

        # Get data-driven upsell opportunities
        opportunities = analytics.get_upsell_opportunities(hotel_config)

        # Store successful opportunities in database
        if opportunities:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                hotel_id = hotel_config.get("id", 1)

                for opp in opportunities[:5]:  # Store top 5
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO ancillary_revenue 
                        (hotel_id, name, description, suggested_price, type)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            hotel_id,
                            opp.get("name"),
                            opp.get("description"),
                            opp.get("suggested_price"),
                            opp.get("type"),
                        ),
                    )
                conn.commit()

        return jsonify({"success": True, "opportunities": opportunities})

    except Exception as e:
        logger.error(f"Error in ancillary revenue endpoint: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/direct-booking-intelligence", methods=["POST", "OPTIONS"])
def direct_booking_intelligence():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        hotel_config = data.get("hotelConfig", {})

        analytics = EnhancedHotelAnalytics()

        # Calculate savings based on real commission data
        savings = analytics.calculate_direct_booking_savings(hotel_config)

        return jsonify({"success": True, "savings": savings})

    except Exception as e:
        logger.error(
            f"Error in direct booking intelligence endpoint: {e}", exc_info=True
        )
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/historical-performance", methods=["POST", "OPTIONS"])
def get_historical_performance_data():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json()
        location = data.get("location", {})
        days = data.get("days", 14)

        city = location.get("city", "Montreal")
        country = location.get("country", "Canada")
        location_str = f"{city}, {country}"

        logger.info(
            f"Fetching {days} days of historical performance for {location_str}"
        )

        analytics = EnhancedHotelAnalytics()

        # Get historical performance data
        performance_data = analytics.get_historical_performance(location_str, days)

        # Ensure we have data for visualization
        if not performance_data.get("history"):
            logger.info("No historical data found, generating from live sources...")
            performance_data = analytics.generate_historical_data_from_sources(
                location_str, days
            )

        logger.info(
            f"Returning {len(performance_data.get('history', []))} historical data points"
        )

        return jsonify({"success": True, "data": performance_data})

    except Exception as e:
        logger.error(f"Error in historical performance endpoint: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify API status"""
    try:
        analytics = EnhancedHotelAnalytics()
        api_status = analytics.check_api_status()

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "apis": api_status,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    init_database()
    logger.info("AmpliFi Backend starting on http://localhost:5000")
    logger.info("Make sure all API keys are configured in .env file:")
    logger.info("  - SERPAPI_API_KEY (required for competitor data)")
    logger.info("  - PREDICTHQ_API_KEY (for event data)")
    logger.info("  - TICKETMASTER_API_KEY (for entertainment events)")
    logger.info("  - RAPIDAPI_KEY (for additional hotel data)")

    # Default to False if the variable isn't set
    is_debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=is_debug, host="0.0.0.0", port=5000)
