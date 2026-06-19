import { useState, useEffect } from 'react';
import '../styles/live.css';

export default function LiveSignals() {
  const [signals, setSignals] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchSignals = async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      const url = `http://localhost:8000/signals/live${forceRefresh ? '?refresh=true' : ''}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to retrieve active predictions from backend.');
      }
      
      const data = await response.json();
      setSignals(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    // Auto-refresh signals every 30 seconds
    const interval = setInterval(() => {
      fetchSignals(false);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    fetchSignals(true);
  };

  const filteredSignals = signals.filter(sig => 
    sig.company_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="signals-container">
      <div className="glass-panel signals-header-block">
        <div className="signals-title-group">
          <h2>Predictive Trade Signal Engine</h2>
          <p>
            Machine learning consensus tracking structural anomalies and direction probabilities.
          </p>
        </div>
        <div>
          <button 
            onClick={handleManualRefresh} 
            className="btn-primary"
            disabled={loading || refreshing}
          >
            {refreshing ? (
              <>
                <span className="spinner" style={{ width: '14px', height: '14px', margin: 0 }}></span>
                Calculating...
              </>
            ) : (
              '⚡ Refresh Predictions'
            )}
          </button>
        </div>
      </div>

      <div className="glass-panel filter-bar">
        <input 
          type="text" 
          placeholder="Filter by Stock Symbol (e.g. JKH, COMB)..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        {signals.length > 0 && (
          <span className="timestamp-tracker">
            Total Asset Coverage: {filteredSignals.length} / {signals.length}
          </span>
        )}
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Loading predictive matrix model...</span>
        </div>
      ) : error ? (
        <div className="glass-panel empty-state">
          <div className="empty-state-icon">⚠️</div>
          <h3>Inference Server Error</h3>
          <p style={{ color: 'var(--color-sell)' }}>{error}</p>
          <button onClick={() => fetchSignals(false)} className="btn-primary" style={{ marginTop: '1rem' }}>
            Retry Connection
          </button>
        </div>
      ) : filteredSignals.length === 0 ? (
        <div className="glass-panel empty-state">
          <div className="empty-state-icon">🔍</div>
          <h3>No Signals Located</h3>
          <p>Verify that the ingestion loop and ML pipeline training files have run successfully.</p>
        </div>
      ) : (
        <div className="glass-panel table-wrapper">
          <table className="signals-table">
            <thead>
              <tr>
                <th>Company Symbol</th>
                <th>Inference Date</th>
                <th>Closing Price</th>
                <th>RSI (14)</th>
                <th>Volatility (20)</th>
                <th>Predictive Consensus</th>
                <th>Up Probability</th>
              </tr>
            </thead>
            <tbody>
              {filteredSignals.map((sig) => {
                // If predicted direction is 1 -> UP (BUY), 0 -> DOWN (SELL)
                const isUp = sig.predicted_direction === 1;
                const probPercent = Math.round(sig.up_probability * 100);
                
                return (
                  <tr key={sig.company_id}>
                    <td style={{ fontWeight: '700', letterSpacing: '0.05em' }}>{sig.company_id}</td>
                    <td className="mono-cell" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {sig.trading_date}
                    </td>
                    <td className="mono-cell" style={{ fontWeight: '600' }}>
                      Rs. {sig.close_price?.toFixed(2)}
                    </td>
                    <td className="mono-cell">{sig.rsi_14?.toFixed(2)}</td>
                    <td className="mono-cell">{sig.volatility_20?.toFixed(4)}</td>
                    <td>
                      <span className={`badge-direction ${isUp ? 'up' : 'down'}`}>
                        {isUp ? '▲ BUY / UP' : '▼ SELL / DOWN'}
                      </span>
                    </td>
                    <td>
                      <div className="probability-bar-container">
                        <div className="probability-bar-track">
                          <div 
                            className="probability-bar-fill" 
                            style={{ 
                              width: `${probPercent}%`,
                              backgroundColor: isUp ? 'var(--color-buy)' : 'var(--color-sell)'
                            }}
                          ></div>
                        </div>
                        <span className="probability-text">{probPercent}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
