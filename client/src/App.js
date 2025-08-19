import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  DollarSign, TrendingUp, Users, Calendar, MapPin, Settings,
  Zap, Target, BarChart3, Activity, Hotel,
  RefreshCw, Play, Pause, ChevronDown, ChevronUp,
  Wifi, WifiOff, Plus, X,
  Star, Crown, Package, Briefcase, Info, Percent
} from 'lucide-react';






const AmpliFiApp = () => {
  // Core State Management
  const [selectedLocation, setSelectedLocation] = useState({ city: 'Montreal', country: 'Canada', region: 'QC' });
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0]);
  const [currentHotel, setCurrentHotel] = useState(0);
  const [hotels, setHotels] = useState([
    {
      id: 1,
      hotelName: 'Our Hotel',
      location: 'Montreal, Canada',
      totalRooms: 100,
      baseOccupancy: 65,
      minPrice: 80,
      maxPrice: 500,
      starRating: 3,
      autoMode: true
    }
  ]);

  // UI State
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showAddHotel, setShowAddHotel] = useState(false);
  const [showPriceOverride, setShowPriceOverride] = useState(false);
  const [expandedAnalysis, setExpandedAnalysis] = useState(false);
  const [discountPercentage, setDiscountPercentage] = useState(0);

  // Data State
  const [currentRecommendation, setCurrentRecommendation] = useState(null);
  const [competitorData, setCompetitorData] = useState([]);
  const [kpiData, setKpiData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [marketEvents, setMarketEvents] = useState([]);
  const [demandForecast, setDemandForecast] = useState({ loading: true, data: [] });
  const [ancillaryOpportunities, setAncillaryOpportunities] = useState({ loading: true, data: [] });
  const [directBookingSavings, setDirectBookingSavings] = useState(null);
  const [error, setError] = useState(null);

  // Real-time connection status
  const [connectionStatus, setConnectionStatus] = useState('connected');

  // Form states
  const [newHotel, setNewHotel] = useState({
    hotelName: '',
    location: '',
    totalRooms: 100,
    baseOccupancy: 65,
    minPrice: 80,
    maxPrice: 500,
    starRating: 3
  });

  const [priceOverride, setPriceOverride] = useState({
    desiredRank: 1,
    targetPrice: 0
  });

  // Get current hotel config
  const getCurrentHotel = useCallback(() => hotels[currentHotel] || hotels[0], [hotels, currentHotel]);

  // Location options for North America
  const locations = [
    { city: 'Montreal', country: 'Canada', region: 'QC' },
    { city: 'Toronto', country: 'Canada', region: 'ON' },
    { city: 'Vancouver', country: 'Canada', region: 'BC' },
    { city: 'Calgary', country: 'Canada', region: 'AB' },
    { city: 'New York', country: 'USA', region: 'NY' },
    { city: 'Los Angeles', country: 'USA', region: 'CA' },
    { city: 'Chicago', country: 'USA', region: 'IL' },
    { city: 'Miami', country: 'USA', region: 'FL' },
    { city: 'Las Vegas', country: 'USA', region: 'NV' },
    { city: 'San Francisco', country: 'USA', region: 'CA' }
  ];

  const loadHotels = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/hotels`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.hotels && data.hotels.length > 0) {
          setHotels(data.hotels);
        } else {
          console.log('No hotels found in database, using default');
        }
      } else {
        console.log('Backend not available, using default hotel data');
      }
    } catch (error) {
      console.log('Using default hotel data:', error.message);
    }
  };

const fetchPriceHistory = useCallback(async () => {
  try {
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/historical-performance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        location: selectedLocation,
        days: 30 
      })
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.data.history) {
        setPriceHistory(data.data.history);
      }
    }
  } catch (error) {
    console.error('Error fetching price history:', error);
  }
}, [selectedLocation]);

  const generateDemoHistory = useCallback(() => {
    const history = [];
    let basePrice = 150 + Math.random() * 50;
    let baseOccupancy = 65 + Math.random() * 10;

    for (let i = 14; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        
        let price = basePrice;
        let occupancy = baseOccupancy;

        // Weekend effect
        if ([5, 6].includes(date.getDay())) {
            price *= 1.25;
            occupancy *= 1.15;
        }

        // Random event simulation
        if (Math.random() < 0.2) {
            price *= 1.4;
            occupancy *= 1.2;
        }

        // General noise
        price *= (0.95 + Math.random() * 0.1);
        occupancy *= (0.95 + Math.random() * 0.1);
        
        occupancy = Math.min(98, Math.max(55, occupancy));
        price = Math.round(price);
        
        history.push({
            date: date.toISOString().split('T')[0],
            price,
            occupancy: Math.round(occupancy),
            revpar: Math.round(price * (occupancy / 100)),
            adr: price
        });
    }
    setPriceHistory(history);
  }, []);

  // Generate initial demo data
 useEffect(() => {
  fetchPriceHistory();
  loadHotels();
}, [selectedLocation, fetchPriceHistory]);

  const addNewHotel = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/hotels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newHotel)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          await loadHotels();
          setShowAddHotel(false);
          setNewHotel({
            hotelName: '',
            location: '',
            totalRooms: 100,
            baseOccupancy: 65,
            minPrice: 80,
            maxPrice: 500,
            starRating: 3
          });
        } else {
          console.error('Failed to create hotel:', data.error);
        }
      } else {
        console.error('Failed to create hotel: HTTP', response.status);
      }
    } catch (error) {
      console.error('Error adding hotel:', error);
    }
  };

  const handlePriceOverride = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/price-override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          desiredRank: priceOverride.desiredRank,
          competitors: competitorData,
          hotelConfig: getCurrentHotel()
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setCurrentRecommendation(prev => ({
            ...prev,
            recommended_price: data.override_price,
            kpis: data.kpis,
            market_position: data.positioning,
            reasoning: `Manual override: Positioned at rank #${data.market_rank} in market with ${data.positioning} pricing strategy.`
          }));
          setKpiData(data.kpis);
          setShowPriceOverride(false);
        } else {
          console.error('Price override failed:', data.error);
        }
      } else {
        console.error('Price override request failed:', response.status);
      }
    } catch (error) {
      console.error('Error overriding price:', error);
    }
  };
  
  const getRecommendation = useCallback(async () => {
    setIsLoading(true);
    setConnectionStatus('connecting');
    setError(null);

    try {
      const hotel = getCurrentHotel();
      console.log('Making request to backend...');

      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/price-recommendation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          location: selectedLocation,
          date: targetDate,
          hotelConfig: hotel
        })
      });

      console.log('Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
          const result = data.data;
          setCurrentRecommendation(result);
          setCompetitorData(result.competitors || []);
          setKpiData(result.kpis || {});
          setMarketEvents(result.market_events || []);
          setConnectionStatus('connected');

          // Add to history
          const newEntry = {
            date: targetDate,
            price: result.recommended_price,
            occupancy: result.kpis?.projected_occupancy || hotel.baseOccupancy,
            revpar: result.kpis?.revpar || 0,
            adr: result.kpis?.adr || result.recommended_price
          };
          setPriceHistory(prev => {
            const filtered = prev.filter(entry => entry.date !== targetDate);
            const updated = [...filtered, newEntry].sort((a, b) => new Date(a.date) - new Date(b.date));
            return updated.slice(-15);
          });
        } else {
          throw new Error(data.error || 'Unknown API error');
        }
      } else {
        const errorText = await response.text();
        throw new Error(`Backend unavailable (HTTP ${response.status}): ${errorText}`);
      }
    } catch (error) {
      console.error('Backend Error:', error);
      setError(error.message);
      setConnectionStatus('error');

      // Show more helpful error message
      if (error.message.includes('Failed to fetch')) {
        setError(`Cannot connect to backend server. Make sure it is running on ${process.env.REACT_APP_API_URL}`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedLocation, targetDate, getCurrentHotel]);

  // Auto-refresh when in auto mode
  useEffect(() => {
    const hotel = getCurrentHotel();
    if (hotel?.autoMode && currentRecommendation) {
      const interval = setInterval(getRecommendation, 300000); // 5 minutes
      return () => clearInterval(interval);
    }
  }, [currentRecommendation, getRecommendation, getCurrentHotel]);

  const fetchAncillaryData = useCallback(async () => {
    setAncillaryOpportunities({ loading: true, data: [] });
    const hotel = getCurrentHotel();
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/ancillary-revenue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hotelConfig: hotel }),
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success) setAncillaryOpportunities({ loading: false, data: data.opportunities });
    } else {
      setAncillaryOpportunities({ loading: false, data: [] });
    }
  }, [getCurrentHotel]);

  const fetchDirectBookingData = useCallback(async () => {
    const hotel = getCurrentHotel();
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/direct-booking-intelligence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hotelConfig: hotel }),
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success) setDirectBookingSavings(data.savings);
    }
  }, [getCurrentHotel]);

  const fetchDemandForecast = useCallback(async () => {
    setDemandForecast({ loading: true, data: [] });
    const hotel = getCurrentHotel();
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/demand-forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location: selectedLocation, hotelConfig: hotel }),
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success) setDemandForecast({ loading: false, data: data.forecast });
    } else {
      setDemandForecast({ loading: false, data: [] });
    }
  }, [selectedLocation, getCurrentHotel]);

  useEffect(() => {
    if (activeTab === 'ancillary') fetchAncillaryData();
    if (activeTab === 'directBooking') fetchDirectBookingData();
    if (activeTab === 'demandForecast') fetchDemandForecast();
  }, [activeTab, fetchAncillaryData, fetchDirectBookingData, fetchDemandForecast]);

  const updateHotelConfig = (key, value) => {
    setHotels(prev => prev.map((hotel, index) =>
      index === currentHotel ? { ...hotel, [key]: value } : hotel
    ));
  };

  const renderStarRating = (rating, interactive = false, onChange = null) => {
    return (
      <div className="flex space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-5 w-5 ${
              star <= rating
                ? 'text-yellow-400 fill-current'
                : 'text-gray-300'
              } ${interactive ? 'cursor-pointer hover:text-yellow-300' : ''}`}
            onClick={interactive ? () => onChange(star) : undefined}
          />
        ))}
      </div>
    );
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Connection Status */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <WifiOff className="h-5 w-5 text-red-500 mr-2" />
            <p className="text-red-700 font-medium">Connection Error</p>
          </div>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <p className="text-red-500 text-xs mt-2">
            Make sure backend is running: <code className="bg-red-100 px-1 rounded">cd server && python app.py</code>
          </p>
        </div>
      )}

      {/* Hotel Selector & Action Button */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Revenue Dashboard: {getCurrentHotel().hotelName}
          </h2>
          <span className="text-lg text-gray-600">
            📍 {selectedLocation.city}, {selectedLocation.region}
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={getRecommendation}
            disabled={isLoading}
            className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-5 w-5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Getting AI Insights...' : 'Get AI Recommendation'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recommended Price</p>
              <p className="text-2xl font-bold text-gray-900">
                ${currentRecommendation?.recommended_price?.toFixed(2) || '--'}
              </p>
              {currentRecommendation && (
                <p className="text-sm text-green-600">
                  {currentRecommendation.confidence > 1
                    ? currentRecommendation.confidence
                    : (currentRecommendation.confidence * 100).toFixed(0)}
                  % confidence
                </p>
              )}
            </div>
            <DollarSign className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">RevPAR</p>
              <p className="text-2xl font-bold text-gray-900">
                ${kpiData?.revpar?.toFixed(2) || '--'}
              </p>
              <p className="text-sm text-gray-500">Revenue per available room</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Occupancy</p>
              <p className="text-2xl font-bold text-gray-900">
                {kpiData?.projected_occupancy || getCurrentHotel().baseOccupancy}%
              </p>
              <p className="text-sm text-gray-500">Projected for {targetDate}</p>
            </div>
            <Users className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                ${kpiData?.projected_revenue?.toLocaleString() || '--'}
              </p>
              <p className="text-sm text-gray-500">Daily projection</p>
            </div>
            <Target className="h-8 w-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Enhanced AI Analysis */}
      {currentRecommendation && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
          <div className="flex items-start space-x-3">
            <Zap className="h-6 w-6 text-blue-600 mt-1" />
            <div className="flex-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-blue-900"> AI Analysis & Research</h3>
                <button
                  onClick={() => setExpandedAnalysis(!expandedAnalysis)}
                  className="flex items-center text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
                >
                  {expandedAnalysis ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                  {expandedAnalysis ? 'Collapse Analysis' : 'Full Analysis Report'}
                </button>
              </div>

              {/* Research Summary */}
              <div className="bg-white p-4 rounded-lg border border-blue-200 mb-4">
                <h4 className="font-semibold text-gray-900 mb-2">🔍 Research Summary</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {currentRecommendation.confidence > 1
                        ? currentRecommendation.confidence
                        : (currentRecommendation.confidence * 100).toFixed(0)}
                      %
                    </div>
                    <div className="text-gray-600">Confidence</div>
                    <div className="text-xs text-gray-500">Analysis reliability</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{marketEvents.length}</div>
                    <div className="text-gray-600">Market Events</div>
                    <div className="text-xs text-gray-500">
                    {marketEvents.filter(e => e.source === 'Tavily').length} from Live Search, {marketEvents.filter(e => e.source !== 'Tavily').length} from AI
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{competitorData.length}</div>
                    <div className="text-gray-600">Hotels Analyzed</div>
                    <div className="text-xs text-gray-500">Real competitor data</div>
                  </div>
                </div>
              </div>

              {/* Main Reasoning */}
              <div className="bg-blue-100 p-4 rounded-lg mb-4">
                <h4 className="font-semibold text-blue-900 mb-2">💡 Key Insights</h4>
                <p className="text-blue-800">{currentRecommendation.reasoning}</p>
              </div>

              {/* Strategy Tags */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                   Demand: {currentRecommendation.demand_level || 'Medium'}
                </span>
                <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                   {competitorData.length} Competitors
                </span>
                <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm">
                   {marketEvents.length} Market Events
                </span>
                {currentRecommendation.pricing_strategy && (
                  <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm">
                     Strategy: {currentRecommendation.pricing_strategy}
                  </span>
                )}
                {currentRecommendation.market_position && (
                  <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm">
                     Position: {currentRecommendation.market_position}
                  </span>
                )}
              </div>
              
              {/* Expanded Analysis */}
              {expandedAnalysis && currentRecommendation.detailed_analysis && (
                <div className="bg-white p-6 rounded-lg border border-blue-200 space-y-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4"> Comprehensive Analysis Report</h4>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                        Market Overview
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.market_overview}</p>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                        Competitive Landscape
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.competitive_landscape}</p>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                        Demand Drivers
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.demand_drivers}</p>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                        Pricing Strategy
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.pricing_strategy}</p>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                        Risk Factors
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.risk_factors}</p>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
                        Revenue Optimization
                      </h5>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-700 text-sm">{currentRecommendation.detailed_analysis.revenue_optimization}</p>
                      </div>
                    </div>
                  </div>

                  {/* Research Methodology */}
                  <div className="border-t pt-6">
                    <h5 className="font-semibold text-gray-900 mb-3">🔬 Research Methodology</h5>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <h6 className="font-medium text-blue-900 mb-2">Data Sources</h6>
                          <ul className="space-y-1 text-blue-800">
                            <li>• AI-powered competitor research</li>
                            <li>• {marketEvents.filter(e => e.source === 'tavily').length > 0 ? 'Real-time event data (Tavily)' : 'Market intelligence analysis'}</li>
                            <li>• Historical pricing patterns</li>
                            <li>• Seasonal demand modeling</li>
                          </ul>
                        </div>
                        <div>
                          <h6 className="font-medium text-blue-900 mb-2">Analysis Factors</h6>
                          <ul className="space-y-1 text-blue-800">
                            {Array.isArray(currentRecommendation.market_factors) && currentRecommendation.market_factors.map((factor, index) => (
                              <li key={index}>• {factor}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Start Guide when no recommendation */}
      {!currentRecommendation && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Zap className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-blue-900">Welcome to AmpliFi Revenue Management</h3>
          </div>
          <p className="text-blue-800 mb-4">
            Get started by clicking "Get AI Recommendation" to receive intelligent pricing insights powered by real-time market data.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2"> AI-Powered Pricing</h4>
              <p className="text-blue-700">Advanced algorithms analyze competitor rates, demand patterns, and market events</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2"> Real-Time Insights</h4>
              <p className="text-blue-700">Live market data and event detection for optimal revenue management</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2"> Auto-Pilot Mode</h4>
              <p className="text-blue-700">Automated pricing updates with customizable boundaries and manual override</p>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price History Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Price & Occupancy Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceHistory.slice().sort((a, b) => new Date(a.date) - new Date(b.date))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(date) => {
                        const d = new Date(date);
                        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                    }}
                />
                <YAxis yAxisId="price" orientation="left" label={{ value: 'Price ($)', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="occupancy" orientation="right" label={{ value: 'Occupancy (%)', angle: 90, position: 'insideRight' }} />
                <Tooltip
                    formatter={(value, name) => [
                        name === 'Price' ? `$${Number(value).toFixed(2)}` : `${Number(value).toFixed(1)}%`,
                        name
                    ]}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Legend />
                <Line 
                    yAxisId="price" 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#3b82f6" 
                    strokeWidth={2} 
                    name="Price" 
                    dot={false}
                    connectNulls={true}
                />
                <Line 
                    yAxisId="occupancy" 
                    type="monotone" 
                    dataKey="occupancy" 
                    stroke="#10b981" 
                    strokeWidth={2} 
                    name="Occupancy" 
                    dot={false}
                    connectNulls={true}
                />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Competitor Analysis */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Competitor Pricing Landscape</h3>
            <div className="text-sm text-gray-600">
              {selectedLocation.city}, {selectedLocation.region} • {competitorData.length} Hotels
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={competitorData.slice(0, 10).map(comp => ({
              ...comp,
              shortName: comp.name.length > 20 ? comp.name.substring(0, 17) + '...' : comp.name
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="shortName"
                tick={{ fontSize: 9 }}
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
              />
              <YAxis />
              <Tooltip
                formatter={(value, name, props) => [`$${value}`, props.payload.name]}
                labelFormatter={(label, payload) => {
                  if (payload && payload[0]) {
                    const hotel = payload[0].payload;
                    return `${hotel.name} (${hotel.stars}⭐)`;
                  }
                  return label;
                }}
              />
              <Bar
                dataKey="price"
                fill="#6366f1"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
          {competitorData.length > 10 && (
            <div className="text-center mt-2 text-sm text-gray-500">
              Showing top 10 of {competitorData.length} competitors
            </div>
          )}
        </div>
      </div>

       {/* Market Events */}
       {marketEvents.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <h3 className="text-lg font-semibold">Market Events Impact</h3>
              <div className="relative group ml-2">
                <Info className="h-4 w-4 text-gray-400 cursor-pointer" />
                <div className="absolute bottom-full mb-2 w-64 bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <span className="font-bold">🔴 Live:</span> Sourced from real-time web search.
                  <br />
                  <span className="font-bold"> AI:</span> Sourced from general knowledge (e.g., public holidays).
                </div>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {marketEvents.map((event, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium flex items-center">
                    {event.source === 'Tavily' && <span className="text-red-500 mr-2">●</span>}
                    {event.name || event.event_name}
                  </p>
                  <p className="text-sm text-gray-600">{event.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{new Date(event.date).toLocaleDateString()}</p>
                  <span className={`inline-block px-2 py-1 rounded text-xs ${
                    event.impact === 'high' ? 'bg-red-100 text-red-700' :
                      event.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                    }`}>
                    {event.impact} impact
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderCompetitors = () => {
    const ourHotel = getCurrentHotel();
    const ourPrice = currentRecommendation ? currentRecommendation.recommended_price * (1 - discountPercentage / 100) : 0;
  
    const allHotels = [
      ...competitorData,
      {
        ...ourHotel,
        price: ourPrice,
        name: ourHotel.hotelName,
        isOurHotel: true
      }
    ].sort((a, b) => b.price - a.price);
  
    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Competitor Analysis</h3>
            <div className="flex items-center space-x-3">
              <button 
                onClick={() => setShowPriceOverride(true)}
                disabled={!currentRecommendation || competitorData.length === 0}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                <Crown className="h-4 w-4 mr-2" />
                Set Market Position
              </button>
              <button 
                onClick={getRecommendation}
                disabled={isLoading}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh Data
              </button>
            </div>
          </div>
          
          {/* Dynamic Discount Tool */}
          {currentRecommendation && (
            <div className="bg-gray-50 p-4 rounded-lg mb-6 border">
              <h4 className="font-semibold mb-2">Dynamic Discount Modeling</h4>
              <div className="flex items-center space-x-4">
                <Percent className="h-5 w-5 text-gray-600" />
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={discountPercentage}
                  onChange={(e) => setDiscountPercentage(Number(e.target.value))}
                  className="w-full"
                />
                <span className="font-bold text-lg w-24 text-right">{discountPercentage}% Off</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Apply a temporary discount to see how your market ranking changes in real-time.
              </p>
            </div>
          )}
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Rank</th>
                  <th className="text-left py-3 px-4">Hotel Name</th>
                  <th className="text-left py-3 px-4">Price</th>
                  <th className="text-left py-3 px-4">Brand</th>
                  <th className="text-left py-3 px-4">Stars</th>
                </tr>
              </thead>
              <tbody>
                {allHotels.map((hotel, index) => (
                  <tr key={index} className={`border-b ${hotel.isOurHotel ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
                    <td className="py-3 px-4 font-bold">#{index + 1}</td>
                    <td className="py-3 px-4 font-medium">{hotel.name}</td>
                    <td className={`py-3 px-4 font-bold ${hotel.isOurHotel ? 'text-blue-600' : ''}`}>${hotel.price.toFixed(2)}</td>
                    <td className="py-3 px-4 text-gray-600">{hotel.brand || 'Independent'}</td>
                    <td className="py-3 px-4">
                      <div className="flex">
                        {[...Array(hotel.starRating || 3)].map((_, i) => (
                          <span key={i} className="text-yellow-400">★</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderAncillaryRevenue = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">AI-Suggested Upsell Opportunities</h3>
            <button onClick={fetchAncillaryData} disabled={ancillaryOpportunities.loading} className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <RefreshCw className={`h-4 w-4 mr-2 ${ancillaryOpportunities.loading ? 'animate-spin' : ''}`} />
                Refresh
            </button>
        </div>
        
        {ancillaryOpportunities.loading ? (
            <p>Loading AI suggestions...</p>
        ) : ancillaryOpportunities.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ancillaryOpportunities.data.map((item, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-blue-800">{item.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                <div className="mt-2 text-lg font-bold text-green-600">${item.suggested_price.toFixed(2)}</div>
                </div>
            ))}
            </div>
        ) : (
            <p>No upsell opportunities found. Try again later.</p>
        )}
      </div>
    </div>
  );

  const renderDirectBooking = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Direct Booking Intelligence</h3>
        <p className="text-gray-600 mb-6">
            Reduce reliance on expensive Online Travel Agencies (OTAs). This module estimates your monthly commission costs and highlights potential savings by shifting guests to direct booking channels.
        </p>
        {directBookingSavings ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-red-50 p-6 rounded-lg">
              <div className="flex items-center text-sm text-red-600 font-medium">
                <DollarSign className="h-4 w-4 mr-2" />
                Estimated Monthly OTA Commissions
              </div>
              <div className="text-3xl font-bold text-red-900 mt-2">${directBookingSavings.monthly_ota_commission.toLocaleString()}</div>
              <p className="text-xs text-red-700 mt-1">This is an estimate of what you pay to OTAs each month (e.g., Booking.com, Expedia) based on a 40% booking share and an 18% commission rate.</p>
            </div>
            <div className="bg-green-50 p-6 rounded-lg">
              <div className="flex items-center text-sm text-green-600 font-medium">
                <TrendingUp className="h-4 w-4 mr-2" />
                Potential Monthly Savings
              </div>
              <div className="text-3xl font-bold text-green-900 mt-2">${directBookingSavings.potential_monthly_savings.toLocaleString()}</div>
              <p className="text-xs text-green-700 mt-1">Represents the savings if you could shift 25% of your OTA bookings to direct channels, saving on commission fees.</p>
            </div>
          </div>
        ) : (
            <p>Loading direct booking intelligence...</p>
        )}
      </div>
    </div>
  );

  const renderDemandForecast = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">7-Day Demand Forecast</h3>
            <button onClick={fetchDemandForecast} disabled={demandForecast.loading} className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <RefreshCw className={`h-4 w-4 mr-2 ${demandForecast.loading ? 'animate-spin' : ''}`} />
                Refresh Forecast
            </button>
        </div>
        {demandForecast.loading ? (
            <p>Generating 90-day forecast...</p>
        ) : demandForecast.data.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {demandForecast.data.map((day, index) => (
            <div key={index} className={`p-3 rounded-lg border ${
              day.demand_level === 'peak' ? 'bg-red-100 border-red-200' :
                day.demand_level === 'high' ? 'bg-orange-100 border-orange-200' :
                  day.demand_level === 'medium' ? 'bg-yellow-100 border-yellow-200' : 
                  'bg-green-100 border-green-200'
            }`}>
              <div className="font-bold text-sm text-gray-800">{new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</div>
              <div className="text-xs text-gray-600 mt-1">{day.driver}</div>
              <div className={`mt-2 text-xs font-bold uppercase px-2 py-1 rounded-full inline-block ${
                day.demand_level === 'peak' ? 'bg-red-200 text-red-800' :
                day.demand_level === 'high' ? 'bg-orange-200 text-orange-800' :
                day.demand_level === 'medium' ? 'bg-yellow-200 text-yellow-800' : 
                'bg-green-200 text-green-800'
              }`}>{day.demand_level}</div>
            </div>
          ))}
        </div>
        ) : (
            <p>Could not generate a demand forecast at this time. Please try again later.</p>
        )}
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      {/* Hotel Management */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Hotel Management</h3>
          <button
            onClick={() => setShowAddHotel(true)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Hotel
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {hotels.map((hotel, index) => (
            <div
              key={index}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                currentHotel === index
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }`}
              onClick={() => setCurrentHotel(index)}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">{hotel.hotelName}</h4>
                {renderStarRating(hotel.starRating)}
              </div>
              <p className="text-sm text-gray-600 mb-1">{hotel.location}</p>
              <p className="text-sm text-gray-500">{hotel.totalRooms} rooms</p>
              <div className="mt-2 flex items-center space-x-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  hotel.autoMode
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                  }`}>
                  {hotel.autoMode ? 'Auto-Pilot' : 'Manual'}
                </span>
                {currentHotel === index && (
                  <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">
                    Active
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current Hotel Configuration */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">
          {getCurrentHotel().hotelName} Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Hotel Name</label>
            <input
              type="text"
              value={getCurrentHotel().hotelName}
              onChange={(e) => updateHotelConfig('hotelName', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Star Rating</label>
            <div className="flex items-center space-x-2">
              {renderStarRating(
                getCurrentHotel().starRating,
                true,
                (rating) => updateHotelConfig('starRating', rating)
              )}
              <span className="text-sm text-gray-600">
                ({getCurrentHotel().starRating} {getCurrentHotel().starRating === 1 ? 'star' : 'stars'})
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Total Rooms</label>
            <input
              type="number"
              value={getCurrentHotel().totalRooms}
              onChange={(e) => updateHotelConfig('totalRooms', parseInt(e.target.value) || 100)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Base Occupancy (%)</label>
            <input
              type="number"
              value={getCurrentHotel().baseOccupancy}
              onChange={(e) => updateHotelConfig('baseOccupancy', parseInt(e.target.value) || 65)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Price ($)</label>
            <input
              type="number"
              value={getCurrentHotel().minPrice}
              onChange={(e) => updateHotelConfig('minPrice', parseInt(e.target.value) || 80)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Price ($)</label>
            <input
              type="number"
              value={getCurrentHotel().maxPrice}
              onChange={(e) => updateHotelConfig('maxPrice', parseInt(e.target.value) || 500)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Automation Settings */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Automation Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-Pilot Mode</p>
              <p className="text-sm text-gray-600">Automatically refresh recommendations every 5 minutes</p>
            </div>
            <button
              onClick={() => updateHotelConfig('autoMode', !getCurrentHotel().autoMode)}
              className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${
                getCurrentHotel().autoMode ? 'bg-blue-600' : 'bg-gray-200'
                }`}
            >
              <span
                className={`inline-block w-4 h-4 transform transition-transform bg-white rounded-full ${
                  getCurrentHotel().autoMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">System Status</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Backend Connection</span>
            <div className={`flex items-center space-x-2 ${
              connectionStatus === 'connected' ? 'text-green-600' :
                connectionStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600'
              }`}>
              {connectionStatus === 'connected' ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
              <span className="capitalize">{connectionStatus}</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">API Endpoint</span>
            <span className="text-sm text-gray-500">http://localhost:5000</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Last Update</span>
            <span className="text-sm text-gray-500">
              {currentRecommendation ? 'Just now' : 'Never'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Tavily Integration</span>
            <span className="text-sm text-green-600">Real-time Events</span>
          </div>
        </div>
      </div>
    </div>
  );

  // Modals
  const renderAddHotelModal = () => {
    if (!showAddHotel) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Add New Hotel</h3>
            <button onClick={() => setShowAddHotel(false)}>
              <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hotel Name</label>
              <input
                type="text"
                value={newHotel.hotelName}
                onChange={(e) => setNewHotel(prev => ({ ...prev, hotelName: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Enter hotel name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text"
                value={newHotel.location}
                onChange={(e) => setNewHotel(prev => ({ ...prev, location: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="City, Country"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Star Rating</label>
              <div className="flex items-center space-x-2">
                {renderStarRating(
                  newHotel.starRating,
                  true,
                  (rating) => setNewHotel(prev => ({ ...prev, starRating: rating }))
                )}
                <span className="text-sm text-gray-600">
                  ({newHotel.starRating} {newHotel.starRating === 1 ? 'star' : 'stars'})
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Total Rooms</label>
                <input
                  type="number"
                  value={newHotel.totalRooms}
                  onChange={(e) => setNewHotel(prev => ({ ...prev, totalRooms: parseInt(e.target.value) || 100 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base Occupancy (%)</label>
                <input
                  type="number"
                  value={newHotel.baseOccupancy}
                  onChange={(e) => setNewHotel(prev => ({ ...prev, baseOccupancy: parseInt(e.target.value) || 65 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Price ($)</label>
                <input
                  type="number"
                  value={newHotel.minPrice}
                  onChange={(e) => setNewHotel(prev => ({ ...prev, minPrice: parseInt(e.target.value) || 80 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Price ($)</label>
                <input
                  type="number"
                  value={newHotel.maxPrice}
                  onChange={(e) => setNewHotel(prev => ({ ...prev, maxPrice: parseInt(e.target.value) || 500 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              onClick={() => setShowAddHotel(false)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={addNewHotel}
              disabled={!newHotel.hotelName || !newHotel.location}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Add Hotel
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderPriceOverrideModal = () => {
    if (!showPriceOverride) return null;

    const maxRank = competitorData.length + 1;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full mx-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Manual Price Override</h3>
            <button onClick={() => setShowPriceOverride(false)}>
              <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          </div>

          <div className="space-y-4">
            <p className="text-gray-600">
              Choose where you want your hotel to rank among {competitorData.length} competitors:
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Desired Market Ranking
              </label>
              <select
                value={priceOverride.desiredRank}
                onChange={(e) => setPriceOverride(prev => ({ ...prev, desiredRank: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {Array.from({ length: maxRank }, (_, i) => i + 1).map(rank => (
                  <option key={rank} value={rank}>
                    #{rank} - {
                      rank === 1 ? 'Highest Price (Premium)' :
                        rank <= Math.ceil(maxRank * 0.3) ? 'High Price (Luxury)' :
                          rank <= Math.ceil(maxRank * 0.7) ? 'Mid-Market (Competitive)' :
                            'Lower Price (Value)'
                    }
                  </option>
                ))}
              </select>
            </div>

            {competitorData.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Current Market Landscape:</h4>
                <div className="space-y-1 text-sm">
                  {competitorData
                    .sort((a, b) => b.price - a.price)
                    .slice(0, 5)
                    .map((competitor, index) => (
                      <div key={index} className="flex justify-between">
                        <span>#{index + 1} {competitor.name}</span>
                        <span>${competitor.price}</span>
                      </div>
                    ))}
                  {competitorData.length > 5 && (
                    <div className="text-gray-500">...and {competitorData.length - 5} more</div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              onClick={() => setShowPriceOverride(false)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handlePriceOverride}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Apply Override
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Zap className="h-8 w-8 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">DEMO RMS AI</h1>
              </div>
              <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                connectionStatus === 'connected' ? 'bg-green-100 text-green-700' :
                  connectionStatus === 'connecting' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                }`}>
                {connectionStatus === 'connected' ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {connectionStatus}
              </div>
              <div className="flex items-center space-x-2">
                <Hotel className="h-5 w-5 text-gray-500" />
                <select
                  value={currentHotel}
                  onChange={(e) => setCurrentHotel(parseInt(e.target.value))}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  {hotels.map((hotel, index) => (
                    <option key={index} value={index}>
                      {hotel.hotelName} ({hotel.starRating}★)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Location Selector */}
              <div className="relative">
                <select
                  value={`${selectedLocation.city}, ${selectedLocation.region}`}
                  onChange={(e) => {
                    const location = locations.find(loc =>
                      `${loc.city}, ${loc.region}` === e.target.value
                    );
                    if (location) setSelectedLocation(location);
                  }}
                  className="pl-8 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  {locations.map((location) => (
                    <option key={`${location.city}-${location.region}`} value={`${location.city}, ${location.region}`}>
                      {location.city}, {location.region}
                    </option>
                  ))}
                </select>
                <MapPin className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              </div>

              {/* Date Picker */}
              <div className="relative">
                <input
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <Calendar className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              </div>

              {/* Auto Mode Toggle */}
              <div className="flex items-center space-x-2">
                {getCurrentHotel().autoMode ? <Play className="h-4 w-4 text-green-600" /> : <Pause className="h-4 w-4 text-gray-400" />}
                <span className="text-sm text-gray-600">
                  {getCurrentHotel().autoMode ? 'Auto-Pilot' : 'Manual'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
              { id: 'competitors', name: 'Competitor Analysis', icon: Activity },
              { id: 'demandForecast', name: 'Demand Forecast', icon: TrendingUp },
              { id: 'ancillary', name: 'Ancillary Revenue', icon: Package },
              { id: 'directBooking', name: 'Direct Bookings', icon: Briefcase },
              { id: 'settings', name: 'Settings', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'text-gray-600 hover:text-gray-900'
                  }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div>
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'competitors' && renderCompetitors()}
          {activeTab === 'ancillary' && renderAncillaryRevenue()}
          {activeTab === 'directBooking' && renderDirectBooking()}
          {activeTab === 'demandForecast' && renderDemandForecast()}
          {activeTab === 'settings' && renderSettings()}
        </div>

        {/* Modals */}
        {renderAddHotelModal()}
        {renderPriceOverrideModal()}

        {/* Loading Overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex items-center space-x-3">
                <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
                <div>
                  <p className="font-semibold">Analyzing Market Data</p>
                  <p className="text-sm text-gray-600">Getting AI-powered recommendations with real-time events...</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AmpliFiApp;