import React, { useState, useEffect, useRef } from 'react';
import './ErrorSimulatorPage.css';

const STATUS_CODES = [400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504];

const ErrorSimulatorPage = () => {
  const [statusCode, setStatusCode] = useState(500);
  const [message, setMessage] = useState('Simulated error for Instana testing');
  const [intervalSec, setIntervalSec] = useState(5);
  const [log, setLog] = useState([]);
  const [running, setRunning] = useState(false);
  const timerRef = useRef(null);
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log]);

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  const addLog = (code, msg, ok) => {
    const ts = new Date().toLocaleTimeString();
    setLog((prev) => [...prev.slice(-99), { ts, code, msg, ok }]);
  };

  const fire = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/simulate-error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ statusCode, message }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        addLog(response.status, errorData.error || message, false);
      } else {
        addLog(statusCode, message, true);
      }
    } catch (err) {
      addLog(statusCode, err.message || 'Network error', false);
    }
  };

  const handleFire = () => {
    fire();
  };

  const handleToggleRepeat = () => {
    if (running) {
      clearInterval(timerRef.current);
      setRunning(false);
    } else {
      fire();
      timerRef.current = setInterval(fire, intervalSec * 1000);
      setRunning(true);
    }
  };

  return (
    <div className="error-simulator-container">
      <div className="error-simulator-paper">
        <h2 className="error-simulator-title">Error Simulator</h2>
        <p className="error-simulator-subtitle">
          Trigger HTTP errors against the backend. Each request is traced by Instana and marked as erroneous.
        </p>

        <div className="error-simulator-form">
          {/* Status code selector */}
          <div className="form-group">
            <label htmlFor="status-code">HTTP Status Code</label>
            <select
              id="status-code"
              value={statusCode}
              onChange={(e) => setStatusCode(Number(e.target.value))}
              className="form-select"
            >
              {STATUS_CODES.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </div>

          {/* Message */}
          <div className="form-group">
            <label htmlFor="error-message">Error Message</label>
            <input
              id="error-message"
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="form-input"
            />
          </div>

          <hr className="divider" />

          {/* Repeat interval */}
          <div className="form-group">
            <label>Repeat interval: <strong>{intervalSec}s</strong></label>
            <input
              type="range"
              min="1"
              max="60"
              step="1"
              value={intervalSec}
              onChange={(e) => setIntervalSec(Number(e.target.value))}
              disabled={running}
              className="form-slider"
            />
            <div className="slider-marks">
              <span>1s</span>
              <span>30s</span>
              <span>60s</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="button-group">
            <button
              className="btn btn-error"
              onClick={handleFire}
              disabled={running}
            >
              Fire Once
            </button>
            <button
              className={`btn ${running ? 'btn-warning' : 'btn-secondary'}`}
              onClick={handleToggleRepeat}
            >
              {running ? `Stop (repeating every ${intervalSec}s)` : 'Start Repeating'}
            </button>
          </div>

          {running && (
            <div className="alert alert-warning">
              Firing <strong>{statusCode}</strong> every <strong>{intervalSec}s</strong> — click Stop to cancel.
            </div>
          )}

          {/* Log */}
          {log.length > 0 && (
            <div className="log-container">
              <h3 className="log-title">Request log</h3>
              <div className="log-box">
                {log.map((entry, i) => (
                  <div key={i} className="log-entry">
                    <span className={`log-chip ${entry.ok ? 'log-chip-default' : 'log-chip-error'}`}>
                      {entry.code}
                    </span>
                    <span className="log-time">{entry.ts}</span>
                    <span className="log-message"> — {entry.msg}</span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorSimulatorPage;
