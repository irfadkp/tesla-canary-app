package com.ferrari.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.ferrari.service.LogGeneratorService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/health")
@RequiredArgsConstructor
public class HealthController {
    private static final Logger log = LoggerFactory.getLogger(HealthController.class);

    private final LogGeneratorService logGenerator;

    @GetMapping("/live")
    public ResponseEntity<Map<String, Object>> liveness() {
        logGenerator.logHeavily("Liveness probe check");
        
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "ferrari-backend");
        health.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(health);
    }

    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> readiness() {
        logGenerator.logHeavily("Readiness probe check");
        
        Map<String, Object> health = new HashMap<>();
        health.put("status", "READY");
        health.put("service", "ferrari-backend");
        health.put("timestamp", System.currentTimeMillis());
        
        return ResponseEntity.ok(health);
    }
}
