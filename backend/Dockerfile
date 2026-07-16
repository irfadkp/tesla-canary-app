# Multi-stage build for Tesla Backend
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

# Download Instana Java agent so the JVM can be auto-instrumented at startup.
# Without -javaagent the agent process on the node cannot attach to this JVM,
# HTTP spans / error_rate / latency will never appear in Instana.
ARG INSTANA_AGENT_VERSION=1.2.0
RUN apk add --no-cache curl && \
    mkdir -p /instana && \
    curl -fLo /instana/instana-java-agent.jar \
      "https://artifact-public.instana.io/artifactory/shared/com/instana/standalone-collector-jvm/${INSTANA_AGENT_VERSION}/standalone-collector-jvm-${INSTANA_AGENT_VERSION}.jar" || \
    echo "WARNING: Instana agent download failed — traces will not be reported"

# Copy the built jar from build stage (includes Instana SDK)
COPY --from=build /app/target/*.jar app.jar

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health/live || exit 1

# Use shell form so env vars (INSTANA_SERVICE_NAME etc.) expand at runtime.
# JSON-array ENTRYPOINT does NOT do shell variable substitution.
ENTRYPOINT ["sh", "-c", "\
  AGENT_JAR=/instana/instana-java-agent.jar; \
  AGENT_OPTS=''; \
  if [ -f \"$AGENT_JAR\" ]; then \
    AGENT_OPTS=\"-javaagent:${AGENT_JAR}\"; \
    echo \"[Instana] Java agent attached: ${AGENT_JAR}\"; \
  else \
    echo \"[Instana] WARNING: agent jar not found, traces disabled\"; \
  fi; \
  exec java \
    $AGENT_OPTS \
    -Xms256m \
    -Xmx512m \
    -XX:+UseG1GC \
    -XX:MaxGCPauseMillis=200 \
    -Dinstana.service.name=${INSTANA_SERVICE_NAME:-tesla-backend} \
    -jar app.jar"]
