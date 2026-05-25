import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { initInstana } from './utils/instana';

// Initialize Instana monitoring
initInstana();

// Heavy logging on app start
console.log('========================================');
console.log('Ferrari Frontend Application Starting');
console.log('========================================');
console.log('Environment:', process.env.NODE_ENV);
console.log('API URL:', process.env.REACT_APP_API_URL || 'http://localhost:8080');
console.log('Timestamp:', new Date().toISOString());
console.log('User Agent:', navigator.userAgent);
console.log('Screen Resolution:', `${window.screen.width}x${window.screen.height}`);
console.log('========================================');

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Log performance metrics
window.addEventListener('load', () => {
  console.log('========================================');
  console.log('Performance Metrics');
  console.log('========================================');
  const perfData = performance.getEntriesByType('navigation')[0];
  console.log('DOM Content Loaded:', perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart, 'ms');
  console.log('Load Complete:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
  console.log('========================================');
});

// Log errors globally
window.addEventListener('error', (event) => {
  console.error('========================================');
  console.error('GLOBAL ERROR CAUGHT');
  console.error('========================================');
  console.error('Message:', event.message);
  console.error('Source:', event.filename);
  console.error('Line:', event.lineno);
  console.error('Column:', event.colno);
  console.error('Error:', event.error);
  console.error('========================================');
});

// Log unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('========================================');
  console.error('UNHANDLED PROMISE REJECTION');
  console.error('========================================');
  console.error('Reason:', event.reason);
  console.error('Promise:', event.promise);
  console.error('========================================');
});
