package com.ferrari.controller;

import com.instana.sdk.annotation.Span;
import com.instana.sdk.support.SpanSupport;
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
public class InstanaTestController {
    private static final Logger log = LoggerFactory.getLogger(InstanaTestController.class);

    @PostMapping("/instana-test-error")
    @Span(value = "test-error-endpoint", type = Span.Type.ENTRY)
    public ResponseEntity<?> testInstanaError(@RequestBody Map<String, Object> request) {
        Integer statusCode = (Integer) request.getOrDefault("statusCode", 500);
        String message = (String) request.getOrDefault("message", "Instana SDK test error");

        log.error("INSTANA TEST: Generating {} error - {}", statusCode, message);
        
        // Mark span as erroneous using Instana SDK
        SpanSupport.annotate(Span.Type.ENTRY, "error", true);
        SpanSupport.annotate(Span.Type.ENTRY, "http.status", statusCode);
        SpanSupport.annotate(Span.Type.ENTRY, "error.message", message);
        
        // Throw exception for 5xx errors
        if (statusCode >= 500) {
            RuntimeException error = new RuntimeException("INSTANA TEST ERROR: " + message);
            SpanSupport.annotate(Span.Type.ENTRY, "error.object", error);
            throw error;
        }
        
        // For 4xx errors, return error response
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", message);
        errorResponse.put("status", statusCode);
        errorResponse.put("timestamp", System.currentTimeMillis());
        errorResponse.put("path", "/api/instana-test-error");
        errorResponse.put("note", "Using Instana SDK annotations");

        return ResponseEntity.status(HttpStatus.valueOf(statusCode)).body(errorResponse);
    }

    @GetMapping("/instana-test-success")
    @Span(value = "test-success-endpoint", type = Span.Type.ENTRY)
    public ResponseEntity<?> testInstanaSuccess() {
        log.info("INSTANA TEST: Success endpoint called");
        
        SpanSupport.annotate(Span.Type.ENTRY, "http.status", 200);
        SpanSupport.annotate(Span.Type.ENTRY, "test.type", "success");
        
        Map<String, String> response = new HashMap<>();
        response.put("status", "ok");
        response.put("message", "Instana SDK test - success");
        response.put("timestamp", String.valueOf(System.currentTimeMillis()));
        
        return ResponseEntity.ok(response);
    }
}
