export const initInstana = () => {
  const instanaKey = process.env.REACT_APP_INSTANA_KEY;
  const instanaUrl = process.env.REACT_APP_INSTANA_URL;

  if (!instanaKey || !instanaUrl) {
    console.warn('Instana monitoring not configured');
    return;
  }

  console.log('========================================');
  console.log('Initializing Instana RUM');
  console.log('========================================');
  console.log('Instana URL:', instanaUrl);
  console.log('Instana Key:', instanaKey.substring(0, 10) + '...');
  console.log('========================================');

  // Initialize Instana RUM
  if (window.ineum) {
    window.ineum('reportingUrl', instanaUrl);
    window.ineum('key', instanaKey);
    window.ineum('trackSessions');
    console.log('Instana RUM initialized successfully');
  } else {
    console.warn('Instana RUM library not loaded');
  }
};
