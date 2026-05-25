import React, { useState, useEffect } from 'react';
import './App.css';
import VehicleList from './components/VehicleList';
import VehicleForm from './components/VehicleForm';
import ErrorBoundary from './components/ErrorBoundary';
import { logHeavily, logError, logSuccess } from './utils/logger';

function App() {
  const [activeTab, setActiveTab] = useState('list');
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    logHeavily('App component mounted');
    console.log('========================================');
    console.log('Ferrari Vehicle Management System');
    console.log('Version: 1.0.0');
    console.log('Build: Canary Deployment Demo');
    console.log('========================================');

    // Simulate periodic logging
    const logInterval = setInterval(() => {
      console.log('[HEARTBEAT]', new Date().toISOString(), 'App is running');
      console.log('[METRICS] Active tab:', activeTab);
      console.log('[METRICS] Error count:', errorCount);
    }, 10000);

    return () => {
      clearInterval(logInterval);
      logHeavily('App component unmounting');
    };
  }, [activeTab, errorCount]);

  const handleTabChange = (tab) => {
    logHeavily(`Switching to tab: ${tab}`);
    console.log('Previous tab:', activeTab);
    console.log('New tab:', tab);
    setActiveTab(tab);
    logSuccess(`Successfully switched to ${tab} tab`);
  };

  const handleError = () => {
    const newCount = errorCount + 1;
    setErrorCount(newCount);
    logError('Error occurred in application', new Error('Simulated error'));
    console.error('Total errors:', newCount);
  };

  // Simulate random errors
  useEffect(() => {
    const errorInterval = setInterval(() => {
      if (Math.random() < 0.2) { // 20% chance
        handleError();
      }
    }, 15000);

    return () => clearInterval(errorInterval);
  }, [errorCount]);

  return (
    <ErrorBoundary>
      <div className="App">
        <header className="App-header">
          <h1>🚗 Ferrari Vehicle Management</h1>
          <p className="subtitle">Canary Deployment Demo</p>
          <div className="error-counter">
            Errors: <span className="error-count">{errorCount}</span>
          </div>
        </header>

        <nav className="App-nav">
          <button 
            className={activeTab === 'list' ? 'active' : ''}
            onClick={() => handleTabChange('list')}
          >
            Vehicle List
          </button>
          <button 
            className={activeTab === 'add' ? 'active' : ''}
            onClick={() => handleTabChange('add')}
          >
            Add Vehicle
          </button>
          <button 
            className={activeTab === 'stats' ? 'active' : ''}
            onClick={() => handleTabChange('stats')}
          >
            Statistics
          </button>
        </nav>

        <main className="App-main">
          {activeTab === 'list' && <VehicleList onError={handleError} />}
          {activeTab === 'add' && <VehicleForm onError={handleError} />}
          {activeTab === 'stats' && (
            <div className="stats-container">
              <h2>Application Statistics</h2>
              <div className="stat-card">
                <h3>Total Errors</h3>
                <p className="stat-value">{errorCount}</p>
              </div>
              <div className="stat-card">
                <h3>Active Tab</h3>
                <p className="stat-value">{activeTab}</p>
              </div>
              <div className="stat-card">
                <h3>Uptime</h3>
                <p className="stat-value">{Math.floor(performance.now() / 1000)}s</p>
              </div>
            </div>
          )}
        </main>

        <footer className="App-footer">
          <p>Ferrari Backend API: {process.env.REACT_APP_API_URL || 'http://localhost:8080'}</p>
          <p>Deployment: Canary Strategy</p>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;
