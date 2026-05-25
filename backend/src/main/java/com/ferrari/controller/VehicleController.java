package com.ferrari.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.ferrari.service.ErrorGeneratorService;
import com.ferrari.service.LogGeneratorService;
import com.ferrari.service.ExternalApiService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

@RestController
@RequestMapping("/api/vehicles")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class VehicleController {
    private static final Logger log = LoggerFactory.getLogger(VehicleController.class);

    private final ErrorGeneratorService errorGenerator;
    private final LogGeneratorService logGenerator;
    private final ExternalApiService externalApiService;

    @GetMapping
    public ResponseEntity<?> getAllVehicles() {
        logGenerator.logHeavily("GET /api/vehicles - Fetching all vehicles");
        
        // 30% chance of error
        if (errorGenerator.shouldFail(30)) {
            return errorGenerator.generateRandomError("Failed to fetch vehicles");
        }

        // Make external API call
        externalApiService.callExternalApi();

        List<Map<String, Object>> vehicles = Arrays.asList(
            createVehicle("488 GTB", "Sports", 250000, "Red"),
            createVehicle("F8 Tributo", "Sports", 280000, "Yellow"),
            createVehicle("Portofino", "Convertible", 215000, "Blue"),
            createVehicle("Roma", "GT", 220000, "Silver"),
            createVehicle("SF90", "Hybrid", 500000, "Black")
        );

        logGenerator.logSuccess("Successfully fetched " + vehicles.size() + " vehicles");
        return ResponseEntity.ok(vehicles);
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getVehicleById(@PathVariable String id) {
        logGenerator.logHeavily("GET /api/vehicles/" + id + " - Fetching vehicle details");
        
        // 25% chance of error
        if (errorGenerator.shouldFail(25)) {
            return errorGenerator.generateRandomError("Failed to fetch vehicle " + id);
        }

        // Simulate slow query
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(100, 500));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        Map<String, Object> vehicle = createVehicle("F-150", "Truck", 45000, "Blue");
        vehicle.put("id", id);
        
        logGenerator.logSuccess("Successfully fetched vehicle " + id);
        return ResponseEntity.ok(vehicle);
    }

    @PostMapping
    public ResponseEntity<?> createVehicle(@RequestBody Map<String, Object> vehicleData) {
        logGenerator.logHeavily("POST /api/vehicles - Creating new vehicle: " + vehicleData);
        
        // 35% chance of error on create
        if (errorGenerator.shouldFail(35)) {
            return errorGenerator.generateRandomError("Failed to create vehicle");
        }

        // Make external API call
        externalApiService.callExternalApi();

        vehicleData.put("id", UUID.randomUUID().toString());
        vehicleData.put("createdAt", new Date());
        
        logGenerator.logSuccess("Successfully created vehicle: " + vehicleData.get("id"));
        return ResponseEntity.status(HttpStatus.CREATED).body(vehicleData);
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateVehicle(@PathVariable String id, @RequestBody Map<String, Object> vehicleData) {
        logGenerator.logHeavily("PUT /api/vehicles/" + id + " - Updating vehicle");
        
        // 40% chance of error on update
        if (errorGenerator.shouldFail(40)) {
            return errorGenerator.generateRandomError("Failed to update vehicle " + id);
        }

        vehicleData.put("id", id);
        vehicleData.put("updatedAt", new Date());
        
        logGenerator.logSuccess("Successfully updated vehicle " + id);
        return ResponseEntity.ok(vehicleData);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteVehicle(@PathVariable String id) {
        logGenerator.logHeavily("DELETE /api/vehicles/" + id + " - Deleting vehicle");
        
        // 20% chance of error on delete
        if (errorGenerator.shouldFail(20)) {
            return errorGenerator.generateRandomError("Failed to delete vehicle " + id);
        }

        logGenerator.logSuccess("Successfully deleted vehicle " + id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/search")
    public ResponseEntity<?> searchVehicles(@RequestParam(required = false) String type,
                                           @RequestParam(required = false) String color) {
        logGenerator.logHeavily("GET /api/vehicles/search - Searching vehicles: type=" + type + ", color=" + color);
        
        // 28% chance of error
        if (errorGenerator.shouldFail(28)) {
            return errorGenerator.generateRandomError("Search failed");
        }

        // Make multiple external API calls
        externalApiService.callExternalApi();
        externalApiService.callExternalApi();

        List<Map<String, Object>> results = Arrays.asList(
            createVehicle("F-150", "Truck", 45000, "Blue"),
            createVehicle("Ranger", "Truck", 35000, "Silver")
        );

        logGenerator.logSuccess("Search returned " + results.size() + " results");
        return ResponseEntity.ok(results);
    }

    @GetMapping("/stats")
    public ResponseEntity<?> getStatistics() {
        logGenerator.logHeavily("GET /api/vehicles/stats - Fetching statistics");
        
        // 15% chance of error
        if (errorGenerator.shouldFail(15)) {
            return errorGenerator.generateRandomError("Failed to fetch statistics");
        }

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalVehicles", ThreadLocalRandom.current().nextInt(100, 1000));
        stats.put("totalSales", ThreadLocalRandom.current().nextInt(1000, 10000));
        stats.put("averagePrice", ThreadLocalRandom.current().nextInt(30000, 60000));
        stats.put("timestamp", new Date());

        logGenerator.logSuccess("Successfully fetched statistics");
        return ResponseEntity.ok(stats);
    }

    private Map<String, Object> createVehicle(String model, String type, int price, String color) {
        Map<String, Object> vehicle = new HashMap<>();
        vehicle.put("id", UUID.randomUUID().toString());
        vehicle.put("model", model);
        vehicle.put("type", type);
        vehicle.put("price", price);
        vehicle.put("color", color);
        vehicle.put("year", 2024);
        vehicle.put("inStock", ThreadLocalRandom.current().nextBoolean());
        return vehicle;
    }
}
