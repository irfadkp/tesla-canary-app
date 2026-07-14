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

# Install curl for downloading Instana agent at runtime
RUN apk add --no-cache curl

# Copy the built jar from build stage (includes Instana SDK)
COPY --from=build /app/target/*.jar app.jar

# Create startup script that downloads agent and starts app
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "Downloading Instana Java agent..."' >> /app/start.sh && \
    echo 'curl -f -o /opt/instana-agent.jar http://instana-agent.instana-agent:42699/com.instana.agent-dynamic.jar' >> /app/start.sh && \
    echo 'if [ -f /opt/instana-agent.jar ]; then' >> /app/start.sh && \
    echo '  echo "Instana agent downloaded, starting with instrumentation..."' >> /app/start.sh && \
    echo '  exec java -javaagent:/opt/instana-agent.jar -Xms256m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Dinstana.service.name=${INSTANA_SERVICE_NAME:-tesla-backend} -jar /app/app.jar' >> /app/start.sh && \
    echo 'else' >> /app/start.sh && \
    echo '  echo "WARNING: Instana agent not available, starting without instrumentation..."' >> /app/start.sh && \
    echo '  exec java -Xms256m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Dinstana.service.name=${INSTANA_SERVICE_NAME:-tesla-backend} -jar /app/app.jar' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    chmod +x /app/start.sh

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health/live || exit 1

# Run startup script that downloads agent and starts application
ENTRYPOINT ["/app/start.sh"]
