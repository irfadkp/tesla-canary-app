package com.ferrari.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class ExternalApiService {
    private static final Logger log = LoggerFactory.getLogger(ExternalApiService.class);

    private final HttpClient httpClient;
    private static final String[] EXTERNAL_APIS = {
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://api.github.com/users/github",
        "https://httpbin.org/delay/1",
        "https://api.publicapis.org/entries",
        "https://catfact.ninja/fact"
    };

    public ExternalApiService() {
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    }

    public void callExternalApi() {
        String apiUrl = EXTERNAL_APIS[ThreadLocalRandom.current().nextInt(EXTERNAL_APIS.length)];
        
        log.info("Making external API call to: {}", apiUrl);
        
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();
            
            long startTime = System.currentTimeMillis();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            long duration = System.currentTimeMillis() - startTime;
            
            log.info("External API call completed - Status: {}, Duration: {}ms", 
                     response.statusCode(), duration);
            log.debug("Response body length: {} bytes", response.body().length());
            
            // 20% chance of logging the full response
            if (ThreadLocalRandom.current().nextInt(100) < 20) {
                log.debug("Full response: {}", response.body());
            }
            
        } catch (Exception e) {
            log.error("External API call failed to {}: {}", apiUrl, e.getMessage());
            log.error("Exception details:", e);
        }
    }

    public void callMultipleApis(int count) {
        log.info("Making {} external API calls", count);
        for (int i = 0; i < count; i++) {
            callExternalApi();
            try {
                Thread.sleep(ThreadLocalRandom.current().nextInt(100, 500));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
