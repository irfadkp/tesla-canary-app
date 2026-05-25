package com.ferrari;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class FerrariBackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(FerrariBackendApplication.class, args);
    }
}
