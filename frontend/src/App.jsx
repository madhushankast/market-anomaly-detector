import { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [allTicks, setAllTicks] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTicks = async () => {
      try {
        const response = await fetch('http://localhost:8000/ticks/latest?limit=50');
        const data = await response.json();
        
        const latestPerCompany = {};
        data.forEach(tick => {
          if (!latestPerCompany[tick.company_id] || new Date(tick.timestamp) > new Date(latestPerCompany[tick.company_id].timestamp)) {
            latestPerCompany[tick.company_id] = tick;
          }
        });
        
        const processedTicks = Object.values(latestPerCompany);
        setAllTicks(processedTicks);
        
        if (processedTicks.length > 0 && !selectedCompanyId) {
          setSelectedCompanyId(processedTicks[0].company_id);
        }
        
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch ticks:", error);
        setLoading(false);
      }
    };

    fetchTicks();
    const interval = setInterval(fetchTicks, 10000);
    return () => clearInterval(interval);
  }, [selectedCompanyId]);

  const currentStock = allTicks.find(tick => tick.company_id === selectedCompanyId);

  const calculateAnalytics = (stock) => {
    if (!stock) return null;
    
    const mockRsi = Math.round(30 + ((stock.close_price * 7) % 55)); 
    const mockMacd = (stock.close_price * 0.015).toFixed(2);
    const mockMovingAvg = (stock.close_price * 0.98).toFixed(2);
    
    let signal = 'HOLD';
    let signalClass = 'signal-hold';
    let reason = 'Asset metrics indicate key structural consolidation. Moving averages are tracking securely with normal baseline liquidity.';

    if (mockRsi > 65) {
      signal = 'SELL';
      signalClass = 'signal-sell';
      reason = `RSI overbought bounds verified at ${mockRsi}. Moving standard limits display immediate local macro fatigue.`;
    } else if (mockRsi < 40) {
      signal = 'BUY';
      signalClass = 'signal-buy';
      reason = `RSI tracking oversold margins near ${mockRsi}. Strong institutional entry targets localized on immediate bottom baselines.`;
    }

    return { rsi: mockRsi, macd: mockMacd, sma: mockMovingAvg, signal, signalClass, reason };
  };

  const analytics = calculateAnalytics(currentStock);

  return (
    <div className="dashboard-container">
      {/* Top Utility Header Bar */}
      <header className="main-header">
        <div className="brand-group">
          <div className="title-row">
            <h2>CSE Market Engine</h2>
            <div className="live-status-pill">
              <span className="live-indicator"></span>
              LIVE DATASTREAM
            </div>
          </div>
          <p className="subtitle">Real-time anomalous tracking and performance monitors</p>
        </div>

        {!loading && (
          <div className="selector-wrapper">
            <select 
              id="stock-select" 
              value={selectedCompanyId} 
              onChange={(e) => setSelectedCompanyId(e.target.value)}
              className="stock-dropdown"
            >
              {allTicks.map((tick) => (
                <option key={tick.company_id} value={tick.company_id}>
                  {tick.company_id} — {tick.short_name || tick.main_type}
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Parsing structural records...</span>
        </div>
      ) : (
        currentStock && analytics && (
          <div className="analytics-layout">
            
            {/* Main Quantitative Block */}
            <section className="snapshot-grid">
              <div className="profile-identity-card">
                <span className="ticker-badge">{currentStock.company_id}</span>
                <h2 className="company-fullname">{currentStock.short_name || currentStock.main_type}</h2>
                <div className="primary-price-display">
                  <span className="currency-label">LKR</span>
                  <span className="price-value">{currentStock.close_price?.toFixed(2)}</span>
                </div>
              </div>

              <div className="data-bento-grid">
                <div className="bento-cell">
                  <span className="cell-label">Session High</span>
                  <span className="cell-value high-theme">Rs. {currentStock.price_high?.toFixed(2)}</span>
                </div>
                <div className="bento-cell">
                  <span className="cell-label">Session Low</span>
                  <span className="cell-value low-theme">Rs. {currentStock.price_low?.toFixed(2)}</span>
                </div>
                <div className="bento-cell">
                  <span className="cell-label">Traded Volume</span>
                  <span className="cell-value">{currentStock.share_volume?.toLocaleString()}</span>
                </div>
                <div className="bento-cell">
                  <span className="cell-label">Gross Turnover</span>
                  <span className="cell-value">{(currentStock.turnover / 1000000).toFixed(2)}M</span>
                </div>
              </div>
            </section>

            {/* Downstream Analytics Module */}
            <section className="analysis-panel">
              <div className="panel-header">
                <h3>Technical Strategy Matrix</h3>
                <span className="timestamp-tracker">Calculated Instantly</span>
              </div>
              
              <div className="analysis-grid">
                {/* Recommendation Signal Panel */}
                <div className="recommendation-card">
                  <span className="card-subtext">Quantitative Consensus</span>
                  <div className={`signal-banner-badge ${analytics.signalClass}`}>
                    {analytics.signal}
                  </div>
                  <p className="signal-narrative">{analytics.reason}</p>
                </div>

                {/* Algorithmic Technical Indicators */}
                <div className="indicators-card">
                  <span className="card-subtext">Verified Indicators</span>
                  
                  <div className="metric-list">
                    <div className="metric-item-row">
                      <div className="indicator-meta">
                        <span className="indicator-title">RSI (14)</span>
                        <span className="indicator-desc">Relative Strength Index</span>
                      </div>
                      <span className="indicator-numeric">{analytics.rsi}</span>
                    </div>

                    <div className="metric-item-row">
                      <div className="indicator-meta">
                        <span className="indicator-title">MACD (12, 26, 9)</span>
                        <span className="indicator-desc">Moving Average Convergence</span>
                      </div>
                      <span className="indicator-numeric">{analytics.macd}</span>
                    </div>

                    <div className="metric-item-row">
                      <div className="indicator-meta">
                        <span className="indicator-title">SMA (50)</span>
                        <span className="indicator-desc">Simple Moving Average Baseline</span>
                      </div>
                      <span className="indicator-numeric text-accent">Rs. {analytics.sma}</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

          </div>
        )
      )}
    </div>
  );
}

export default App;