# Multi-stage build for Ferrari Backend
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Install curl for downloading Instana agent
RUN apk add --no-cache curl

# Copy the built jar from build stage (includes Instana SDK)
COPY --from=build /app/target/*.jar app.jar

# Download Instana Java agent from agent service at runtime
RUN curl -o /opt/instana-agent.jar \
  http://instana-agent.instana-agent:42699/com.instana.agent-dynamic.jar || \
  echo "Warning: Instana agent download failed, will run without instrumentation"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health/live || exit 1

# Run application with Instana Java agent for automatic instrumentation
ENTRYPOINT ["java", \
  "-javaagent:/opt/instana-agent.jar", \
  "-Xms256m", \
  "-Xmx512m", \
  "-XX:+UseG1GC", \
  "-XX:MaxGCPauseMillis=200", \
  "-Dinstana.service.name=${INSTANA_SERVICE_NAME:-tesla-backend}", \
  "-jar", \
  "app.jar"]
