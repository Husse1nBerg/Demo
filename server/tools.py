import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from contextlib import contextmanager
import logging
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('amplifi_hotel.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class EnhancedHotelAnalytics:
    """Enhanced hotel analytics with real AI-powered data collection"""
    
    def __init__(self):
        self.anthropic_api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"
        self.scrapingbee_api_key = os.getenv('SCRAPINGBEE_API_KEY')
    
    def _make_ai_request(self, prompt: str, max_tokens: int = 1500) -> Optional[str]:
        """Make request to Claude API"""
        try:
            response = requests.post(
                self.anthropic_api_url,
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['content'][0]['text'].strip()
                return content.replace('```json', '').replace('```', '').strip()
            else:
                logger.error(f"AI API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error making AI request: {e}")
            return None
    
    def get_comprehensive_competitor_analysis(self, city: str, country: str, date: str) -> List[Dict]:
        """
        Get competitor hotel prices by scraping Google Hotels using the ScrapingBee API.
        """
        if not self.scrapingbee_api_key:
            logger.error("SCRAPINGBEE_API_KEY not found in .env file.")
            return []

        logger.info(f"Scraping competitor prices for {city}, {country} via ScrapingBee")

        google_hotels_url = f"https://www.google.com/travel/hotels/{city}?q=hotels%20in%20{city}%20{country}&checkin={date}&checkout={date}&hl=en&gl=us"

        try:
            response = requests.get(
                url='https://app.scrapingbee.com/api/v1/',
                params={
                    'api_key': self.scrapingbee_api_key,
                    'url': google_hotels_url,
                    'render_js': 'true',  # Let ScrapingBee render JavaScript
                },
                timeout=60  # Increase timeout for scraping requests
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            competitors = []
            
            # NOTE: These selectors are based on the current structure of Google Hotels
            # and may need to be updated if the site changes.
            hotel_cards = soup.select('div[jscontroller="g233te"]')

            for card in hotel_cards:
                name_tag = card.select_one('h2.BgYkof')
                price_tag = card.select_one('span.MW1oTb')
                
                if name_tag and price_tag:
                    name = name_tag.get_text(strip=True)
                    price_text = price_tag.get_text(strip=True).replace('$', '').replace(',', '')
                    
                    try:
                        price = float(price_text)
                        
                        competitors.append({
                            "name": name,
                            "price": price,
                            "location": "N/A",
                            "brand": "N/A",
                            "stars": 0,
                            "amenities": [],
                            "room_type": "Standard",
                            "distance_km": 0.0
                        })
                    except ValueError:
                        continue
            
            if competitors:
                self._store_competitor_data(f"{city}, {country}", competitors, date)
            
            return competitors

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling ScrapingBee API: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during scraping: {e}")
            return []
    
    def get_market_intelligence(self, city: str, country: str, date: str) -> Dict:
        """Get comprehensive market intelligence"""
        logger.info(f"Gathering market intelligence for {city}, {country}")
        tavily_events = search_events_with_tavily(city, country, date)
        
        prompt = f"""
        You are a hotel market intelligence data extractor. Your task is to analyze the provided real-time search results and extract relevant hotel demand-driving events for {city}, {country}.

        **CRITICAL INSTRUCTIONS:**
        1.  **Prioritize Search Results:** You MUST prioritize the data from the `<search_results>` block. This is real-time data and is more reliable than your internal knowledge.
        2.  **Extract, Don't Invent:** Extract event names, dates, and descriptions directly from the search results. If the search results are empty or irrelevant, return an empty `market_events` array. DO NOT invent events.
        3.  **Add a Source:** For each event, add a "source" key. If it comes from the search results, set it to "Tavily". If you are adding a well-known, verifiable public holiday for the specified date, set it to "AI Generated".
        4.  **Date Accuracy:** Ensure all dates are in "YYYY-MM-DD" format.

        Here are the real-time search results:
        <search_results>
        {json.dumps(tavily_events)}
        </search_results>
        
        Return ONLY a valid JSON object in this format. If no events are found, the "market_events" array MUST be empty.
        {{
            "market_events": [
                {{
                    "name": "Event Name from Search",
                    "date": "YYYY-MM-DD", 
                    "impact": "high/medium/low",
                    "description": "Description from search result",
                    "source": "Tavily"
                }}
            ]
        }}
        """
        
        response = self._make_ai_request(prompt, max_tokens=2000)
        if response:
            try:
                intelligence = json.loads(response)
                # Add tavily source to all events from search results
                for event in intelligence.get("market_events", []):
                    event["source"] = "Tavily" if "tavily" in json.dumps(tavily_events).lower() else "AI Generated"
                
                self._store_market_intelligence(f"{city}, {country}", intelligence)
                return intelligence
            except json.JSONDecodeError:
                pass
        
        return {"market_events": []}

    def get_demand_forecast(self, city: str, country: str, hotel_config: Dict) -> List[Dict]:
        """Generate a 90-day demand forecast."""
        logger.info(f"Generating 90-day demand forecast for {city}, {country}")
        
        prompt = f"""
        You are a hotel revenue management expert. Create a 90-day demand forecast for a {hotel_config.get('starRating', 3)}-star hotel in {city}, {country}.
        
        For each day starting from today, provide a demand level (low, medium, high, peak) and a key driver.
        
        Return ONLY a valid JSON array in this format:
        [
            {{
                "date": "YYYY-MM-DD",
                "demand_level": "low|medium|high|peak",
                "driver": "Weekend travel|Business travel|Conference|Holiday|etc."
            }}
        ]
        """
        
        response = self._make_ai_request(prompt, max_tokens=4000)
        if response:
            try:
                forecast = json.loads(response)
                if isinstance(forecast, list) and forecast:
                    return forecast
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse forecast JSON: {e}")
        
        # Fallback to demo data
        return [
            {"date": (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'), "demand_level": "medium", "driver": "Standard demand"} for i in range(15)
        ]

    def get_upsell_opportunities(self, hotel_config: Dict) -> List[Dict]:
        """Generate upsell and ancillary revenue opportunities."""
        logger.info("Generating upsell opportunities")
        
        prompt = f"""
        You are a hotel revenue management expert. For a {hotel_config.get('starRating', 3)}-star hotel, suggest 5-7 ancillary revenue and upsell opportunities.
        
        Return ONLY a valid JSON array in this format:
        [
            {{
                "name": "Early Check-in",
                "description": "Allow guests to check-in from 10 AM.",
                "suggested_price": 25.00,
                "type": "service"
            }}
        ]
        """
        
        response = self._make_ai_request(prompt)
        if response:
            try:
                opportunities = json.loads(response)
                if isinstance(opportunities, list) and opportunities:
                    return opportunities
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse upsell JSON: {e}")
        
        # Fallback to demo data
        return [
            {"name": "Early Check-in", "description": "Allow guests to check-in from 10 AM.", "suggested_price": 25.00, "type": "service"},
            {"name": "Late Check-out", "description": "Extend check-out time until 2 PM.", "suggested_price": 30.00, "type": "service"},
            {"name": "Room Upgrade", "description": "Upgrade to a room with a view.", "suggested_price": 50.00, "type": "upgrade"},
        ]

    def calculate_direct_booking_savings(self, hotel_config: Dict) -> Dict:
        """Calculate potential savings from direct bookings."""
        # This is a simplified model. A real implementation would use historical booking data.
        total_rooms = hotel_config.get('totalRooms', 100)
        avg_rate = (hotel_config.get('minPrice', 80) + hotel_config.get('maxPrice', 500)) / 2
        occupancy = hotel_config.get('baseOccupancy', 65) / 100
        
        ota_commission_rate = 0.18 # Average OTA commission
        ota_booking_percentage = 0.40 # Assume 40% of bookings come from OTAs
        
        monthly_rooms_sold = total_rooms * occupancy * 30
        ota_rooms_sold = monthly_rooms_sold * ota_booking_percentage
        
        total_revenue = monthly_rooms_sold * avg_rate
        ota_revenue = ota_rooms_sold * avg_rate
        commission_paid = ota_revenue * ota_commission_rate
        
        potential_savings = commission_paid * 0.25 # Assume 25% can be shifted to direct
        
        return {
            "monthly_ota_commission": round(commission_paid, 2),
            "potential_monthly_savings": round(potential_savings, 2)
        }
    
    def calculate_optimal_pricing(self, 
                                  location: str,
                                  date: str, 
                                  hotel_config: Dict,
                                  competitors: List[Dict],
                                  market_intel: Dict) -> Dict:
        """Calculate optimal pricing using advanced revenue management principles"""
        
        base_config = {
            'totalRooms': 100,
            'baseOccupancy': 65,
            'minPrice': 80,
            'maxPrice': 500
        }
        config = {**base_config, **hotel_config}
        
        # Competitor pricing analysis
        competitor_prices = [c.get('price', 0) for c in competitors if c.get('price', 0) > 50]
        
        competitor_stats = {}
        if competitor_prices:
            competitor_stats = {
                'min': min(competitor_prices),
                'max': max(competitor_prices),
                'avg': sum(competitor_prices) / len(competitor_prices),
                'median': sorted(competitor_prices)[len(competitor_prices)//2]
            }
            base_price = competitor_stats['avg'] * 0.92
        else:
            base_price = 150
        
        # Event-based demand adjustments
        events = market_intel.get('market_events', [])
        demand_multiplier = 1.0
        occupancy_boost = 0
        
        high_impact_events = [e for e in events if e.get('impact') == 'high']
        medium_impact_events = [e for e in events if e.get('impact') == 'medium']
        
        if high_impact_events:
            demand_multiplier = 1.35
            occupancy_boost = 20
        elif medium_impact_events:
            demand_multiplier = 1.15
            occupancy_boost = 10
        
        # Temporal pricing factors
        target_date = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = target_date.weekday()
        
        dow_multipliers = {
            0: 0.95, 1: 0.98, 2: 1.00, 3: 1.05,
            4: 1.20, 5: 1.25, 6: 1.10
        }
        
        seasonal_multiplier = self._get_seasonal_multiplier(target_date, location)
        
        lead_time = (target_date - datetime.now()).days
        lead_time_multiplier = 1.0
        if lead_time < 7 and high_impact_events:
            lead_time_multiplier = 1.1
        elif lead_time > 60:
            lead_time_multiplier = 0.95
        
        calculated_price = (base_price * demand_multiplier * dow_multipliers.get(day_of_week, 1.0) *
                          seasonal_multiplier *
                          lead_time_multiplier)
        
        recommended_price = max(config['minPrice'], min(config['maxPrice'], calculated_price))
        recommended_price = round(recommended_price, 2)
        
        # --- DYNAMIC OCCUPANCY CALCULATION ---
        base_occupancy = config['baseOccupancy']
        
        # Start with event-based boost
        projected_occupancy = min(95, base_occupancy + occupancy_boost)

        # Adjust based on price competitiveness (elasticity model)
        if competitor_stats and competitor_stats.get('avg'):
            price_ratio = recommended_price / competitor_stats['avg']
            # For every 1% more expensive than average, reduce occupancy by 0.5%
            # For every 1% cheaper than average, increase occupancy by 0.25%
            elasticity_adjustment = (1 - price_ratio) * 25
            projected_occupancy = min(95, max(30, projected_occupancy + elasticity_adjustment))
        
        # Calculate performance metrics
        rooms_sold = int(config['totalRooms'] * (projected_occupancy / 100))
        adr = recommended_price
        revpar = adr * (projected_occupancy / 100)
        total_revenue = rooms_sold * adr
        
        # Generate insights
        confidence = self._calculate_confidence(competitors, events, lead_time)
        reasoning = self._generate_pricing_reasoning(competitors, events, day_of_week, 
                                                    seasonal_multiplier, demand_multiplier)
        
        return {
            "recommended_price": recommended_price,
            "projected_occupancy": round(projected_occupancy, 1),
            "confidence_score": confidence,
            "reasoning": reasoning,
            "market_position": "competitive" if competitor_stats else "market_rate",
            "competitor_analysis": {
                "count": len(competitors),
                "avg_price": round(competitor_stats.get('avg', 0), 2),
                "price_range": f"${competitor_stats.get('min', 0):.0f} - ${competitor_stats.get('max', 0):.0f}" if competitor_stats else "N/A"
            },
            "demand_drivers": [e.get('name', '') for e in events if e.get('impact') in ['high', 'medium']],
            "kpis": {
                "adr": round(adr, 2),
                "revpar": round(revpar, 2),
                "projected_revenue": round(total_revenue, 2),
                "rooms_sold": rooms_sold
            }
        }
    
    def _get_seasonal_multiplier(self, date: datetime, location: str) -> float:
        """Get seasonal pricing multiplier based on location and date"""
        month = date.month
        
        # General North American patterns
        if "Canada" in location:
            # Canadian seasonal patterns
            if month in [6, 7, 8]:  # Summer peak
                return 1.2
            elif month in [12, 1]:  # Winter holidays/skiing
                return 1.15
            elif month in [3, 4]:   # Spring break
                return 1.1
            elif month in [2, 11]:  # Low season
                return 0.85
            else:
                return 1.0
        else:  # US patterns
            if month in [6, 7, 8, 12]:  # Summer + December
                return 1.15
            elif month in [1, 2]:       # Winter low
                return 0.9
            else:
                return 1.0
    
    def _calculate_confidence(self, competitors: List[Dict], events: List[Dict], lead_time: int) -> int:
        """Calculate confidence score for pricing recommendation"""
        confidence = 70  # Base confidence
        
        # Competitor data quality
        if len(competitors) >= 8:
            confidence += 15
        elif len(competitors) >= 5:
            confidence += 10
        elif len(competitors) >= 3:
            confidence += 5
        
        # Event intelligence
        if events:
            confidence += 10
        
        # Lead time factor
        if 7 <= lead_time <= 30:  # Sweet spot for accuracy
            confidence += 10
        elif lead_time > 90:      # Too far out, less certain
            confidence -= 5
        
        return min(95, max(65, confidence)) # Set a minimum confidence of 65
    
    def _generate_pricing_reasoning(self, competitors: List[Dict], events: List[Dict], 
                                  day_of_week: int, seasonal_mult: float, demand_mult: float) -> str:
        """Generate human-readable reasoning for pricing decision"""
        reasons = []
        
        if competitors:
            avg_comp_price = sum(c.get('price', 0) for c in competitors) / len(competitors)
            reasons.append(f"Positioned competitively vs {len(competitors)} competitors (avg: ${avg_comp_price:.0f})")
        
        if demand_mult > 1.2:
            reasons.append("High-impact events driving premium pricing")
        elif demand_mult > 1.05:
            reasons.append("Market events supporting rate increase")
        
        if day_of_week in [4, 5, 6]:  # Fri, Sat, Sun
            reasons.append("Weekend premium applied")
        
        if seasonal_mult > 1.1:
            reasons.append("Peak season pricing in effect")
        elif seasonal_mult < 0.95:
            reasons.append("Off-season discount applied")
        
        if not reasons:
            reasons.append("Based on market analysis and demand patterns")
        
        return "; ".join(reasons)
    
    def _store_competitor_data(self, location: str, competitors: List[Dict], date: str):
        """Store competitor data in database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM competitor_data WHERE location = ? AND date_collected = ?', 
                             (location, date))
                
                for comp in competitors:
                    cursor.execute('''
                        INSERT INTO competitor_data 
                        (location, hotel_name, price, distance, source, date_collected)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        location,
                        comp.get('name', 'Unknown'),
                        comp.get('price', 0),
                        comp.get('location', 'Unknown'),
                        comp.get('brand', 'Research'),
                        date
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing competitor data: {e}")
    
    def _store_market_intelligence(self, location: str, intel: Dict):
        """Store market intelligence in database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Store events
                events = intel.get('market_events', [])
                for event in events:
                    cursor.execute('''
                        INSERT OR REPLACE INTO market_events 
                        (location, event_name, event_date, impact_level, description)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        location,
                        event.get('name', ''),
                        event.get('date', ''),
                        event.get('impact', 'low'),
                        event.get('description', '')
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing market intelligence: {e}")

    def get_historical_performance(self, location: str, days: int = 15) -> Dict:
        """Get historical pricing performance data"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT target_date, recommended_price, occupancy, revpar, adr, revenue, confidence
                    FROM price_history 
                    WHERE location = ? 
                    ORDER BY target_date DESC 
                    LIMIT ?
                ''', (location, days))
                
                rows = cursor.fetchall()
                history = []
                total_revenue = 0
                avg_occupancy = 0
                
                for row in rows:
                    record = {
                        'date': row['target_date'],
                        'price': row['recommended_price'],
                        'occupancy': row['occupancy'],
                        'revpar': row['revpar'],
                        'adr': row['adr'],
                        'revenue': row['revenue'],
                        'confidence': row['confidence']
                    }
                    history.append(record)
                    total_revenue += row['revenue'] or 0
                    avg_occupancy += row['occupancy'] or 0
                
                # Calculate performance metrics
                if history:
                    avg_occupancy = avg_occupancy / len(history)
                    avg_adr = sum(h['adr'] for h in history) / len(history)
                    avg_revpar = sum(h['revpar'] for h in history) / len(history)
                else:
                    avg_adr = avg_revpar = 0
                
                return {
                    'history': history,
                    'performance_metrics': {
                        'total_revenue': round(total_revenue, 2),
                        'avg_occupancy': round(avg_occupancy, 1),
                        'avg_adr': round(avg_adr, 2),
                        'avg_revpar': round(avg_revpar, 2),
                        'data_points': len(history)
                    }
                }
        except Exception as e:
            logger.error(f"Error getting historical performance: {e}")
            return {'history': [], 'performance_metrics': {}}

# Legacy function wrappers for compatibility
def get_competitor_prices(city: str, date: str) -> list:
    """Legacy compatibility function"""
    analytics = EnhancedHotelAnalytics()
    country = "Canada"  # Default for legacy calls
    competitors = analytics.get_comprehensive_competitor_analysis(city, country, date)
    return [{"name": c.get("name"), "price": c.get("price"), "source": "AI Research"} 
            for c in competitors]

def get_internal_hotel_data(date: str, total_rooms: int, base_occupancy: int) -> dict:
    """Get internal hotel metrics"""
    target_date = datetime.strptime(date, "%Y-%m-%d")
    lead_time = (target_date - datetime.now()).days
    day_of_week = target_date.strftime("%A")
    
    # Determine pacing based on lead time and day of week
    if lead_time < 14 and target_date.weekday() in [4, 5]:  # Weekend, short lead
        pacing = "ahead of forecast"
    elif lead_time > 60:
        pacing = "behind forecast"
    else:
        pacing = "on track"
    
    return {
        "pacing_status": pacing,
        "day_of_week": day_of_week,
        "lead_time_days": max(0, lead_time),
        "current_occupancy_percent": base_occupancy,
        "total_rooms": total_rooms,
        "booking_pace": "strong" if base_occupancy > 70 else "moderate"
    }

def get_key_performance_indicators(recommended_price: float, 
                                 current_occupancy: int, 
                                 total_rooms: int) -> dict:
    """Calculate KPIs based on pricing recommendation"""
    rooms_sold = int(total_rooms * (current_occupancy / 100))
    adr = recommended_price
    revpar = adr * (current_occupancy / 100)
    total_revenue = rooms_sold * adr
    
    # Calculate additional metrics
    available_rooms = total_rooms - rooms_sold
    revenue_per_room = total_revenue / total_rooms if total_rooms > 0 else 0
    
    return {
        "adr": round(adr, 2),
        "revpar": round(revpar, 2),
        "projected_occupancy_percent": current_occupancy,
        "projected_revenue": round(total_revenue, 2),
        "rooms_sold": rooms_sold,
        "available_rooms": available_rooms,
        "revenue_per_room": round(revenue_per_room, 2),
        "market_penetration": min(100, (current_occupancy / 85) * 100)  # Assuming 85% is market max
    }

def search_events_with_tavily(city, country, date):
    """Search for events using Tavily API"""
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    if not TAVILY_API_KEY:
        logger.warning("Tavily API key not found.")
        return []
    try:
        search_date = datetime.strptime(date, '%Y-%m-%d')
        # New, more specific query for a wider range of events
        query = f"major events, concerts, movies, festivals, sports, F1 races, or celebrity appearances in {city}, {country} on or around {search_date.strftime('%B %d, %Y')}"
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query, "search_depth": "basic", "max_results": 5},
            timeout=10
        )
        return response.json().get('results', []) if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error searching Tavily events: {e}")
        return []