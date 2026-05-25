package com.ferrari.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.stereotype.Service;

import java.util.concurrent.ThreadLocalRandom;

@Service
public class LogGeneratorService {
    private static final Logger log = LoggerFactory.getLogger(LogGeneratorService.class);

    private static final String[] LOG_CONTEXTS = {
        "Database query execution",
        "Cache operation",
        "External API call",
        "Business logic processing",
        "Data validation",
        "Authentication check",
        "Authorization verification",
        "Transaction processing",
        "File operation",
        "Network communication"
    };

    public void logHeavily(String message) {
        // Generate multiple log entries for each operation
        log.info("=== START: {} ===", message);
        log.debug("Request received at: {}", System.currentTimeMillis());
        log.debug("Thread: {}", Thread.currentThread().getName());
        
        // Random additional context logs
        int logCount = ThreadLocalRandom.current().nextInt(3, 8);
        for (int i = 0; i < logCount; i++) {
            String context = LOG_CONTEXTS[ThreadLocalRandom.current().nextInt(LOG_CONTEXTS.length)];
            log.info("Processing step {}: {}", i + 1, context);
            log.debug("Memory usage: {} MB", Runtime.getRuntime().totalMemory() / 1024 / 1024);
        }
        
        log.info("=== END: {} ===", message);
    }

    public void logSuccess(String message) {
        log.info("✓ SUCCESS: {}", message);
        log.info("Response time: {} ms", ThreadLocalRandom.current().nextInt(50, 500));
        log.debug("Status: OK");
    }

    public void logWarning(String message) {
        log.warn("⚠ WARNING: {}", message);
        log.warn("This operation may have performance implications");
    }

    public void logError(String message, Exception e) {
        log.error("✗ ERROR: {}", message);
        log.error("Exception type: {}", e.getClass().getSimpleName());
        log.error("Exception message: {}", e.getMessage());
        log.error("Stack trace:", e);
    }

    public void logMetrics() {
        log.info("=== METRICS ===");
        log.info("Active threads: {}", Thread.activeCount());
        log.info("Free memory: {} MB", Runtime.getRuntime().freeMemory() / 1024 / 1024);
        log.info("Total memory: {} MB", Runtime.getRuntime().totalMemory() / 1024 / 1024);
        log.info("Max memory: {} MB", Runtime.getRuntime().maxMemory() / 1024 / 1024);
        log.info("Processors: {}", Runtime.getRuntime().availableProcessors());
    }
}
