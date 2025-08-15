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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# API configurations
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def create_fallback_data(city, country, date, hotel_config, is_holiday_season, is_major_city, tavily_events):
    """Create realistic fallback data when AI fails"""
    base_price = 120
    if is_major_city:
        base_price = 180
    if is_holiday_season:
        base_price *= 1.4
    
    base_occupancy = hotel_config.get('baseOccupancy', 65)
    if is_holiday_season:
        base_occupancy = min(95, base_occupancy * 1.3)
    
    competitors = []
    hotel_data = [
        (f"Four Seasons Hotel {city}", "Four Seasons", 5, 2.5, "Downtown"),
        (f"The Ritz-Carlton {city}", "Marriott", 5, 2.4, "Downtown"),
        (f"W {city}", "Marriott", 4, 1.8, "Downtown"),
        (f"Grand Hyatt {city}", "Hyatt", 4, 1.6, "Downtown"),
        (f"Hilton {city}", "Hilton", 4, 1.4, "Downtown"),
        (f"{city} Marriott", "Marriott", 4, 1.5, "City Center"),
        (f"InterContinental {city}", "IHG", 4, 1.7, "Downtown"),
        (f"The Westin {city}", "Marriott", 4, 1.6, "Downtown"),
        (f"Hyatt Regency {city}", "Hyatt", 4, 1.4, "City Center"),
        (f"Courtyard by Marriott {city}", "Marriott", 3, 1.1, "Downtown"),
        (f"Hampton Inn & Suites {city}", "Hilton", 3, 0.8, "Downtown"),
        (f"Holiday Inn Express {city}", "IHG", 3, 0.9, "City Center"),
        (f"Boutique Hotel {city}", "Independent", 3, 1.2, "Historic District")
    ]
    
    for name, brand, stars, multiplier, location in hotel_data:
        price_variation = 0.85 + (hash(f"{name}{city}") % 100) / 100 * 0.3
        price = round(base_price * multiplier * price_variation, 2)
        competitors.append({
            "name": name, "price": price, "location": location,
            "brand": brand, "stars": stars
        })
    
    events = list(tavily_events) if tavily_events else []
    
    if is_holiday_season:
        if "12-24" in date:
            events.append({
                "name": "Christmas Eve", "date": date, "impact": "high",
                "description": "Peak holiday travel and family gatherings", "type": "holiday", "source": "ai"
            })
        events.append({
            "name": "Holiday Season", "date": date,
            "impact": "high" if "12-24" in date or "12-31" in date else "medium",
            "description": "Increased tourism and holiday travel demand", "type": "holiday", "source": "ai"
        })
    
    if is_major_city:
        events.append({
            "name": f"{city} Winter Events", "date": date, "impact": "medium",
            "description": "Various winter attractions and business activities", "type": "tourism", "source": "ai"
        })
    
    total_rooms = hotel_config.get('totalRooms', 100)
    rooms_sold = int(total_rooms * (base_occupancy / 100))
    
    return {
        "recommended_price": round(base_price, 2), "confidence": 85,
        "reasoning": f"Fallback pricing for {city} due to API error. Using standard model for {'holiday season' if is_holiday_season else 'regular season'}.",
        "detailed_analysis": {
            "market_overview": "Fallback data used due to an API error. Market analysis could not be performed.",
            "competitive_landscape": "Fallback data used due to an API error. Competitive landscape could not be analyzed.",
            "demand_drivers": "Fallback data used due to an API error. Demand drivers could not be analyzed.",
            "pricing_strategy": "Fallback data used due to an API error. A standard pricing strategy has been applied.",
            "risk_factors": "Fallback data used due to an API error. Risk factors could not be analyzed.",
            "revenue_optimization": "Fallback data used due to an API error. Revenue optimization strategies could not be generated."
        },
        "competitors": competitors, "market_events": events,
        "kpis": {
            "projected_occupancy": round(base_occupancy, 1),
            "adr": round(base_price, 2),
            "revpar": round(base_price * (base_occupancy / 100), 2),
            "projected_revenue": round(rooms_sold * base_price, 2),
            "rooms_sold": rooms_sold
        },
        "market_factors": ["Fallback Data", "Standard Seasonal Model"], "demand_level": "medium",
        "market_position": "competitive",
        "pricing_strategy": "standard"
    }


def search_events_with_tavily(city, country, date):
    if not TAVILY_API_KEY:
        logger.warning("Tavily API key not found.")
        return []
    try:
        search_date = datetime.strptime(date, '%Y-%m-%d')
        query = f"major events, conferences, or festivals in {city}, {country} around {search_date.strftime('%B %Y')}"
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query, "search_depth": "basic", "max_results": 5},
            timeout=10
        )
        return response.json().get('results', []) if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error searching Tavily events: {e}")
        return []


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
        # Add other table creation statements here if needed
        conn.commit()
        logger.info("Database initialized successfully")


def get_ai_recommendation(city, country, date, hotel_config):
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file.")
        is_holiday_season = "12-" in date or "01-" in date
        is_major_city = city.lower() in ['san francisco', 'new york']
        return create_fallback_data(city, country, date, hotel_config, is_holiday_season, is_major_city, [])

    is_holiday_season = "12-" in date or "01-" in date
    is_major_city = city.lower() in ['san francisco', 'new york', 'los angeles', 'chicago', 'toronto', 'vancouver']
    tavily_events = search_events_with_tavily(city, country, date)

    prompt = f"""You are an expert hotel revenue management AI for {city}, {country} on {date}.
    Hotel Config: {json.dumps(hotel_config)}. Star Rating: {hotel_config.get('starRating', 3)}.
    Real-time events found: {json.dumps(tavily_events)}.
    CRITICAL: Provide a JSON response with 15+ REAL competitor hotels with SPECIFIC, existing names and brands in {city}. No generic names.
    Return ONLY a JSON object with keys: recommended_price, confidence, reasoning, detailed_analysis, competitors, market_events, kpis, market_factors, demand_level, market_position, pricing_strategy."""

    for attempt in range(2):
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json={
                    "model": "claude-3-haiku-20240307", "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                timeout=60
            )

            if response.status_code == 200:
                content = response.json()['content'][0]['text'].strip()
                try:
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start != -1 and json_end != -1:
                        json_str = content[json_start:json_end + 1]
                        result = json.loads(json_str)
                        
                        required_keys = ['kpis', 'competitors', 'market_events', 'detailed_analysis']
                        if all(key in result and result[key] is not None for key in required_keys):
                            return result
                        else:
                            logger.warning("AI response was valid JSON but missed required keys. Retrying...")
                            raise ValueError("Incomplete AI response")
                    else:
                        raise json.JSONDecodeError("No JSON object found in the AI response.", content, 0)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"AI response parsing/validation failed on attempt {attempt + 1}: {e}")
                    if attempt == 1:
                        raise e
                    time.sleep(1)
            else:
                logger.error(f"AI API request failed on attempt {attempt + 1}: {response.status_code} - {response.text}")
                if attempt == 1:
                    raise Exception("AI API request failed after multiple attempts.")
        except Exception as e:
            logger.error(f"General error in get_ai_recommendation on attempt {attempt + 1}: {e}")
            if attempt == 1:
                return create_fallback_data(city, country, date, hotel_config, is_holiday_season, is_major_city, tavily_events)

    return create_fallback_data(city, country, date, hotel_config, is_holiday_season, is_major_city, tavily_events)

# API Routes
@app.route('/api/hotels', methods=['GET', 'POST'])
def manage_hotels():
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

@app.route('/api/price-recommendation', methods=['POST'])
def get_price_recommendation():
    try:
        data = request.get_json()
        location = data.get('location', {})
        recommendation = get_ai_recommendation(
            location.get('city', 'Montreal'),
            location.get('country', 'Canada'),
            data.get('date', datetime.now().strftime('%Y-%m-%d')),
            data.get('hotelConfig', {})
        )
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

if __name__ == '__main__':
    init_database()
    logger.info("AmpliFi Backend starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)