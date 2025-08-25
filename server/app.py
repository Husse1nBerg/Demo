from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
import requests
import os
from dotenv import load_dotenv
import time
import re
from tools import EnhancedHotelAnalytics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True, methods=["GET", "POST", "OPTIONS"])

# API configurations
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')


def parse_json_from_string(text):
    """Finds and parses the first valid JSON object from a string."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object found in the AI response.", text, 0)
    
    json_str = match.group(0)
    return json.loads(json_str)


@contextmanager
def get_db_connection():
    conn = sqlite3.connect('amplifi_hotel.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hotel_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, hotel_name TEXT NOT NULL, location TEXT NOT NULL,
                total_rooms INTEGER NOT NULL, base_occupancy INTEGER NOT NULL, min_price REAL NOT NULL,
                max_price REAL NOT NULL, star_rating INTEGER DEFAULT 3, is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ancillary_revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT, hotel_id INTEGER, name TEXT NOT NULL,
                description TEXT, suggested_price REAL, type TEXT,
                FOREIGN KEY (hotel_id) REFERENCES hotel_configs (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ota_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, hotel_id INTEGER, ota_name TEXT NOT NULL,
                commission_rate REAL NOT NULL,
                FOREIGN KEY (hotel_id) REFERENCES hotel_configs (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, hotel_name TEXT,
                price REAL, distance TEXT, source TEXT, date_collected TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, event_name TEXT,
                event_date TEXT, impact_level TEXT, description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, target_date TEXT,
                recommended_price REAL, occupancy REAL, revpar REAL, adr REAL,
                revenue REAL, confidence REAL
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully")


# API Routes
@app.route('/api/hotels', methods=['GET', 'POST', 'OPTIONS'])
def manage_hotels():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    if request.method == 'GET':
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM hotel_configs WHERE is_active = 1 ORDER BY created_at DESC')
                rows = cursor.fetchall()
                hotels = [{
                    'id': row['id'],
                    'hotelName': row['hotel_name'],
                    'location': row['location'],
                    'totalRooms': row['total_rooms'],
                    'baseOccupancy': row['base_occupancy'],
                    'minPrice': row['min_price'],
                    'maxPrice': row['max_price'],
                    'starRating': row['star_rating'],
                    'createdAt': row['created_at']
                } for row in rows]
                return jsonify({"success": True, "hotels": hotels})
        except Exception as e:
            logger.error(f"Error fetching hotels: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO hotel_configs (hotel_name, location, total_rooms, base_occupancy, min_price, max_price, star_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('hotelName'), data.get('location'), data.get('totalRooms'),
                    data.get('baseOccupancy'), data.get('minPrice'), data.get('maxPrice'),
                    data.get('starRating', 3)
                ))
                conn.commit()
                return jsonify({"success": True, "hotel_id": cursor.lastrowid})
        except Exception as e:
            logger.error(f"Error creating hotel: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/price-recommendation', methods=['POST', 'OPTIONS'])
def get_price_recommendation():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        location = data.get('location', {})
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        hotel_config = data.get('hotelConfig', {})
        
        city = location.get('city', 'Montreal')
        country = location.get('country', 'Canada')
        
        logger.info(f"Getting price recommendation for {city}, {country} on {date}")
        
        analytics = EnhancedHotelAnalytics()
        
        competitors = analytics.get_comprehensive_competitor_analysis(city, country, date)
        logger.info(f"Found {len(competitors)} competitors via RapidAPI")
        
        market_intel = analytics.get_market_intelligence(city, country, date)
        
        pricing_result = analytics.calculate_optimal_pricing(
            f"{city}, {country}", date, hotel_config, competitors, market_intel
        )
        
        recommendation = {
            "recommended_price": pricing_result["recommended_price"],
            "confidence": pricing_result["confidence_score"],
            "reasoning": pricing_result["reasoning"],
            "competitors": competitors,
            "market_events": market_intel.get("market_events", []),
            "kpis": pricing_result["kpis"],
            "market_position": pricing_result["market_position"],
            "pricing_strategy": "Data-Driven",
            "demand_level": "medium",
            "detailed_analysis": {
                "market_overview": f"Analysis based on {len(competitors)} scraped competitors from {len(set(c.get('source', '') for c in competitors))} sources",
                "competitive_landscape": pricing_result["competitor_analysis"]["price_range"],
                "demand_drivers": pricing_result["demand_drivers"],
                "pricing_strategy": "Dynamic pricing based on real competitor data via RapidAPI",
                "risk_factors": "Data quality dependent on API success",
                "revenue_optimization": f"Projected RevPAR: ${pricing_result['kpis']['revpar']:.2f}"
            }
        }
        
        logger.info(f"Recommendation confidence: {pricing_result['confidence_score']:.3f} ({pricing_result['confidence_score']*100:.1f}%)")
        
        return jsonify({"success": True, "data": recommendation})
    except Exception as e:
        logger.error(f"Error in price recommendation endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/price-override', methods=['POST', 'OPTIONS'])
def price_override():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        data = request.get_json()
        desired_rank = data.get('desiredRank', 1)
        competitors = data.get('competitors', [])
        hotel_config = data.get('hotelConfig', {})
        
        if not competitors:
            return jsonify({"success": False, "error": "No competitor data available"}), 400
        
        sorted_competitors = sorted(competitors, key=lambda x: x.get('price', 0), reverse=True)
        
        if desired_rank <= len(sorted_competitors):
            if desired_rank == 1:
                target_price = sorted_competitors[0]['price'] * 1.05
            else:
                higher_price = sorted_competitors[desired_rank - 2]['price']
                lower_price = sorted_competitors[desired_rank - 1]['price']
                target_price = (higher_price + lower_price) / 2
        else:
            lowest_price = sorted_competitors[-1]['price']
            target_price = lowest_price * 0.95
        
        min_price = hotel_config.get('minPrice', 80)
        max_price = hotel_config.get('maxPrice', 500)
        target_price = max(min_price, min(max_price, target_price))
        
        base_occupancy = hotel_config.get('baseOccupancy', 65)
        total_rooms = hotel_config.get('totalRooms', 100)
        
        avg_competitor_price = sum(c['price'] for c in competitors) / len(competitors)
        price_ratio = target_price / avg_competitor_price
        
        if price_ratio > 1.1:
            occupancy_adjustment = 0.9
        elif price_ratio < 0.9:
            occupancy_adjustment = 1.1
        else:
            occupancy_adjustment = 1.0
        
        projected_occupancy = min(95, base_occupancy * occupancy_adjustment)
        rooms_sold = int(total_rooms * (projected_occupancy / 100))
        revpar = target_price * (projected_occupancy / 100)
        
        return jsonify({
            "success": True,
            "override_price": round(target_price, 2),
            "market_rank": desired_rank,
            "kpis": {
                "projected_occupancy": round(projected_occupancy, 1),
                "adr": round(target_price, 2),
                "revpar": round(revpar, 2),
                "projected_revenue": round(rooms_sold * target_price, 2),
                "rooms_sold": rooms_sold
            },
            "positioning": "premium" if price_ratio > 1.1 else "value" if price_ratio < 0.9 else "competitive"
        })
        
    except Exception as e:
        logger.error(f"Error in price override: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/demand-forecast', methods=['POST', 'OPTIONS'])
def demand_forecast():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        location = data.get('location', {})
        hotel_config = data.get('hotelConfig', {})
        analytics = EnhancedHotelAnalytics()
        forecast = analytics.get_demand_forecast(location.get('city'), location.get('country'), hotel_config)
        return jsonify({"success": True, "forecast": forecast})
    except Exception as e:
        logger.error(f"Error in demand forecast endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ancillary-revenue', methods=['POST', 'OPTIONS'])
def ancillary_revenue():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        hotel_config = data.get('hotelConfig', {})
        analytics = EnhancedHotelAnalytics()
        opportunities = analytics.get_upsell_opportunities(hotel_config)
        return jsonify({"success": True, "opportunities": opportunities})
    except Exception as e:
        logger.error(f"Error in ancillary revenue endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/direct-booking-intelligence', methods=['POST', 'OPTIONS'])
def direct_booking_intelligence():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        hotel_config = data.get('hotelConfig', {})
        analytics = EnhancedHotelAnalytics()
        savings = analytics.calculate_direct_booking_savings(hotel_config)
        return jsonify({"success": True, "savings": savings})
    except Exception as e:
        logger.error(f"Error in direct booking intelligence endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/historical-performance', methods=['POST', 'OPTIONS'])
def get_historical_performance_data():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        location = data.get('location', {})
        days = data.get('days', 14)

        logger.info(f"Fetching {days} days of historical performance for {location.get('city')}, {location.get('country')}")
        
        analytics = EnhancedHotelAnalytics()
        performance_data = analytics.get_historical_performance(
            f"{location.get('city')}, {location.get('country')}",
            days
        )

        logger.info(f"Historical performance data contains {len(performance_data.get('history', []))} data points")
        return jsonify({"success": True, "data": performance_data})
    except Exception as e:
        logger.error(f"Error in historical performance endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    init_database()
    logger.info("AmpliFi Backend starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)