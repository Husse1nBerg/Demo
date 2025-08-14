import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from contextlib import contextmanager
import logging

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
        """Get comprehensive competitor analysis using AI"""
        logger.info(f"Analyzing competitors in {city}, {country}")
        
        prompt = f"""
        You are a hotel revenue management expert conducting competitor analysis for {city}, {country} on {date}.
        
        Research and provide realistic competitor hotel pricing data. Consider:
        1. Major hotel chains (Marriott, Hilton, Hyatt, IHG, Accor)
        2. Boutique and independent hotels  
        3. Different price segments (budget, mid-scale, upscale, luxury)
        4. Current market conditions and seasonal factors
        5. Location factors (downtown, airport, suburban)
        
        Return ONLY valid JSON array with 12-15 hotels in this format:
        [
            {{
                "name": "Hotel Name",
                "price": 299.99,
                "location": "Downtown/Airport/Suburb", 
                "brand": "Marriott/Hilton/Independent/etc",
                "stars": 3,
                "amenities": ["wifi", "pool", "gym"],
                "room_type": "Standard Queen/King Suite/etc",
                "distance_km": 2.5
            }}
        ]
        
        Ensure prices are realistic for {city} market conditions.
        Include mix of all price segments.
        Only return valid JSON, no explanatory text.
        """
        
        response = self._make_ai_request(prompt)
        if response:
            try:
                competitors = json.loads(response)
                if isinstance(competitors, list) and competitors:
                    self._store_competitor_data(f"{city}, {country}", competitors, date)
                    return competitors
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse competitor JSON: {e}")
        
        return []
    
    def get_market_intelligence(self, city: str, country: str) -> Dict:
        """Get comprehensive market intelligence"""
        logger.info(f"Gathering market intelligence for {city}, {country}")
        
        prompt = f"""
        You are a hotel market intelligence analyst for {city}, {country}.
        
        Analyze current market conditions and provide insights on:
        1. Major events in next 30 days affecting hotel demand
        2. Seasonal trends and patterns
        3. Economic factors impacting travel
        4. Supply/demand dynamics
        5. Key demand generators (business, leisure, events)
        
        Return ONLY valid JSON in this format:
        {{
            "market_events": [
                {{
                    "name": "Event Name",
                    "date": "YYYY-MM-DD", 
                    "impact": "high/medium/low",
                    "description": "Impact description",
                    "type": "conference/festival/sports/business/holiday",
                    "expected_visitors": 5000
                }}
            ],
            "market_conditions": {{
                "demand_level": "high/medium/low",
                "supply_growth": "increasing/stable/decreasing", 
                "price_trend": "rising/stable/falling",
                "occupancy_trend": "up/stable/down"
            }},
            "demand_drivers": ["business travel", "tourism", "events"],
            "seasonal_factors": {{
                "current_season": "peak/shoulder/low",
                "seasonal_multiplier": 1.2
            }}
        }}
        
        Only return valid JSON, no other text.
        """
        
        response = self._make_ai_request(prompt, max_tokens=2000)
        if response:
            try:
                intelligence = json.loads(response)
                self._store_market_intelligence(f"{city}, {country}", intelligence)
                return intelligence
            except json.JSONDecodeError:
                pass
        
        return {
            "market_events": [],
            "market_conditions": {"demand_level": "medium"},
            "demand_drivers": [],
            "seasonal_factors": {"seasonal_multiplier": 1.0}
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
        
        if competitor_prices:
            competitor_stats = {
                'min': min(competitor_prices),
                'max': max(competitor_prices),
                'avg': sum(competitor_prices) / len(competitor_prices),
                'median': sorted(competitor_prices)[len(competitor_prices)//2]
            }
            # Position at competitive rate (5-10% below average for volume)
            base_price = competitor_stats['avg'] * 0.92
        else:
            base_price = 150  # Market standard fallback
        
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
        
        # Day of week adjustments
        dow_multipliers = {
            0: 0.95,  # Monday
            1: 0.98,  # Tuesday  
            2: 1.00,  # Wednesday
            3: 1.05,  # Thursday
            4: 1.20,  # Friday
            5: 1.25,  # Saturday
            6: 1.10   # Sunday
        }
        
        # Seasonal adjustments based on location
        seasonal_multiplier = self._get_seasonal_multiplier(target_date, location)
        
        # Lead time pricing (book closer = higher price if demand is good)
        lead_time = (target_date - datetime.now()).days
        lead_time_multiplier = 1.0
        if lead_time < 7 and high_impact_events:
            lead_time_multiplier = 1.1
        elif lead_time > 60:
            lead_time_multiplier = 0.95
        
        # Calculate final price
        calculated_price = (base_price * 
                          demand_multiplier * 
                          dow_multipliers.get(day_of_week, 1.0) *
                          seasonal_multiplier *
                          lead_time_multiplier)
        
        # Apply min/max constraints
        recommended_price = max(config['minPrice'], 
                              min(config['maxPrice'], calculated_price))
        recommended_price = round(recommended_price, 2)
        
        # Calculate projected metrics
        base_occupancy = config['baseOccupancy']
        projected_occupancy = min(95, base_occupancy + occupancy_boost)
        
        # Price elasticity consideration
        if recommended_price > competitor_stats.get('avg', base_price) * 1.1:
            projected_occupancy *= 0.9  # Reduce occupancy if pricing too high
        
        total_rooms = config['totalRooms']
        rooms_sold = int(total_rooms * (projected_occupancy / 100))
        adr = recommended_price
        revpar = adr * (projected_occupancy / 100)
        total_revenue = rooms_sold * adr
        
        # Confidence scoring
        confidence = self._calculate_confidence(competitors, events, lead_time)
        
        # Generate reasoning
        reasoning = self._generate_pricing_reasoning(
            competitors, events, day_of_week, seasonal_multiplier, demand_multiplier
        )
        
        result = {
            "recommended_price": recommended_price,
            "confidence": confidence,
            "reasoning": reasoning,
            "competitors": competitors[:10],
            "market_factors": [e.get('name', '') for e in events[:5]],
            "kpis": {
                "projected_occupancy": round(projected_occupancy, 1),
                "adr": round(adr, 2),
                "revpar": round(revpar, 2),
                "projected_revenue": round(total_revenue, 2),
                "rooms_sold": rooms_sold
            },
            "price_range": {
                "min": config['minPrice'],
                "max": config['maxPrice'],
                "competitor_avg": round(competitor_stats.get('avg', base_price), 2) if competitor_prices else None
            },
            "demand_level": "high" if high_impact_events else "medium" if medium_impact_events else "normal",
            "market_position": "competitive" if competitor_prices else "market-rate"
        }
        
        return result
    
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
        
        return min(95, max(60, confidence))
    
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

    def get_historical_performance(self, location: str, days: int = 30) -> Dict:
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