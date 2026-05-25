package com.ferrari.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class ErrorGeneratorService {
    private static final Logger log = LoggerFactory.getLogger(ErrorGeneratorService.class);

    private static final String[] ERROR_MESSAGES = {
        "Database connection timeout",
        "Internal server error occurred",
        "Service temporarily unavailable",
        "Resource not found",
        "Invalid request parameters",
        "Authentication failed",
        "Rate limit exceeded",
        "Network connectivity issue",
        "Data validation failed",
        "Unexpected exception occurred"
    };

    private static final HttpStatus[] ERROR_STATUSES = {
        HttpStatus.INTERNAL_SERVER_ERROR,
        HttpStatus.SERVICE_UNAVAILABLE,
        HttpStatus.BAD_GATEWAY,
        HttpStatus.GATEWAY_TIMEOUT,
        HttpStatus.BAD_REQUEST,
        HttpStatus.CONFLICT,
        HttpStatus.UNPROCESSABLE_ENTITY
    };

    public boolean shouldFail(int failurePercentage) {
        return ThreadLocalRandom.current().nextInt(100) < failurePercentage;
    }

    public ResponseEntity<?> generateRandomError(String context) {
        int errorIndex = ThreadLocalRandom.current().nextInt(ERROR_MESSAGES.length);
        int statusIndex = ThreadLocalRandom.current().nextInt(ERROR_STATUSES.length);
        
        String errorMessage = ERROR_MESSAGES[errorIndex];
        HttpStatus status = ERROR_STATUSES[statusIndex];
        
        log.error("ERROR GENERATED - Context: {}, Status: {}, Message: {}", 
                  context, status.value(), errorMessage);
        
        // Log stack trace simulation
        log.error("Stack trace simulation: at com.ferrari.service.ErrorGeneratorService.generateRandomError");
        log.error("  at com.ferrari.controller.VehicleController.handleRequest");
        log.error("  at java.base/java.lang.Thread.run");
        
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", errorMessage);
        errorResponse.put("status", status.value());
        errorResponse.put("context", context);
        errorResponse.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.status(status).body(errorResponse);
    }

    public void simulateCrash() {
        log.error("CRITICAL ERROR: Application crash simulation!");
        log.error("OutOfMemoryError simulation");
        log.error("NullPointerException at critical path");
        throw new RuntimeException("Simulated application crash");
    }
}
