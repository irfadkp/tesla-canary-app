package com.ferrari.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ErrorSimulatorController {
    private static final Logger log = LoggerFactory.getLogger(ErrorSimulatorController.class);

    @PostMapping("/simulate-error")
    public ResponseEntity<?> simulateError(@RequestBody Map<String, Object> request) {
        Integer statusCode = (Integer) request.get("statusCode");
        String message = (String) request.get("message");

        if (statusCode == null) {
            statusCode = 500;
        }
        if (message == null || message.isEmpty()) {
            message = "Simulated error for Instana testing";
        }

        log.error("ERROR SIMULATOR: Generating {} error - {}", statusCode, message);
        log.error("Stack trace simulation for Instana tracing");
        
        // Create error response
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", message);
        errorResponse.put("status", statusCode);
        errorResponse.put("timestamp", System.currentTimeMillis());
        errorResponse.put("path", "/api/simulate-error");

        // Return the specified status code
        return ResponseEntity.status(HttpStatus.valueOf(statusCode)).body(errorResponse);
    }

    @GetMapping("/simulate-error/health")
    public ResponseEntity<?> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "ok");
        response.put("message", "Error simulator is ready");
        return ResponseEntity.ok(response);
    }
}
