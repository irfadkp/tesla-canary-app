export const logHeavily = (message) => {
  console.log('========================================');
  console.log('[LOG]', new Date().toISOString());
  console.log('[MESSAGE]', message);
  console.log('[STACK]', new Error().stack);
  console.log('[MEMORY]', performance.memory ? 
    `${(performance.memory.usedJSHeapSize / 1048576).toFixed(2)} MB` : 'N/A');
  console.log('========================================');
};

export const logError = (message, error) => {
  console.error('========================================');
  console.error('[ERROR]', new Date().toISOString());
  console.error('[MESSAGE]', message);
  console.error('[ERROR OBJECT]', error);
  console.error('[ERROR MESSAGE]', error?.message);
  console.error('[ERROR STACK]', error?.stack);
  console.error('========================================');
};

export const logSuccess = (message) => {
  console.log('========================================');
  console.log('[SUCCESS]', new Date().toISOString());
  console.log('[MESSAGE]', message);
  console.log('========================================');
};

export const logWarning = (message) => {
  console.warn('========================================');
  console.warn('[WARNING]', new Date().toISOString());
  console.warn('[MESSAGE]', message);
  console.warn('========================================');
};

// Auto-log every 5 seconds
setInterval(() => {
  console.log('[HEARTBEAT]', new Date().toISOString(), 'Application running');
  console.log('[PERFORMANCE]', {
    navigation: performance.getEntriesByType('navigation')[0],
    memory: performance.memory
  });
}, 5000);
