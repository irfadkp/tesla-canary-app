# Multi-stage build for Ferrari Backend
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /app

# Copy Maven settings with Instana credentials
COPY .mvn/maven-settings.xml /root/.m2/settings.xml

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy the built jar from build stage (includes Instana SDK)
COPY --from=build /app/target/*.jar app.jar

# Copy Instana Java agent from Maven dependencies
COPY --from=build /root/.m2/repository/com/instana/javaagent-attach/1.0.11/javaagent-attach-1.0.11.jar /opt/instana-agent.jar

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
