package com.ferrari.service;

import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.concurrent.ThreadLocalRandom;

@Service
@RequiredArgsConstructor
public class BackgroundTaskService {

    private static final Logger log = LoggerFactory.getLogger(BackgroundTaskService.class);
    
    private final LogGeneratorService logGenerator;
    private final ExternalApiService externalApiService;
    private final ErrorGeneratorService errorGenerator;

    // Run every 10 seconds - Heavy logging
    @Scheduled(fixedRate = 10000)
    public void generateHeavyLogs() {
        log.info("========================================");
        log.info("SCHEDULED TASK: Heavy log generation");
        log.info("========================================");
        
        logGenerator.logHeavily("Background task execution");
        logGenerator.logMetrics();
        
        // Random warnings
        if (ThreadLocalRandom.current().nextInt(100) < 30) {
            logGenerator.logWarning("High memory usage detected");
        }
        
        log.info("Background task completed");
    }

    // Run every 15 seconds - External API calls
    @Scheduled(fixedRate = 15000)
    public void makeExternalApiCalls() {
        log.info("SCHEDULED TASK: Making external API calls");
        
        int callCount = ThreadLocalRandom.current().nextInt(2, 5);
        externalApiService.callMultipleApis(callCount);
        
        log.info("Completed {} external API calls", callCount);
    }

    // Run every 20 seconds - Simulate random errors
    @Scheduled(fixedRate = 20000)
    public void simulateRandomErrors() {
        log.info("SCHEDULED TASK: Error simulation check");
        
        // 40% chance of generating an error
        if (errorGenerator.shouldFail(40)) {
            log.error("SCHEDULED ERROR: Simulated background task failure");
            log.error("Error code: ERR_{}", ThreadLocalRandom.current().nextInt(1000, 9999));
            log.error("Severity: {}", ThreadLocalRandom.current().nextBoolean() ? "HIGH" : "MEDIUM");
            
            // Log fake stack trace
            log.error("  at com.ferrari.service.BackgroundTaskService.simulateRandomErrors");
            log.error("  at org.springframework.scheduling.support.ScheduledMethodRunnable.run");
            log.error("  at java.base/java.util.concurrent.Executors$RunnableAdapter.call");
        } else {
            log.info("Background task health check: OK");
        }
    }

    // Run every 30 seconds - Database simulation logs
    @Scheduled(fixedRate = 30000)
    public void simulateDatabaseOperations() {
        log.info("SCHEDULED TASK: Database operations simulation");
        
        String[] operations = {"SELECT", "INSERT", "UPDATE", "DELETE"};
        String operation = operations[ThreadLocalRandom.current().nextInt(operations.length)];
        
        log.info("Executing {} operation", operation);
        log.debug("Query execution time: {}ms", ThreadLocalRandom.current().nextInt(10, 500));
        log.debug("Rows affected: {}", ThreadLocalRandom.current().nextInt(1, 100));
        
        // 25% chance of slow query warning
        if (ThreadLocalRandom.current().nextInt(100) < 25) {
            log.warn("SLOW QUERY DETECTED: Execution time exceeded threshold");
            log.warn("Query: {} FROM vehicles WHERE ...", operation);
        }
        
        log.info("Database operation completed successfully");
    }

    // Run every minute - System health check
    @Scheduled(fixedRate = 60000)
    public void systemHealthCheck() {
        log.info("========================================");
        log.info("SYSTEM HEALTH CHECK");
        log.info("========================================");
        
        logGenerator.logMetrics();
        
        log.info("Service status: RUNNING");
        log.info("Uptime: {} seconds", System.currentTimeMillis() / 1000);
        log.info("Health check completed");
    }
}
