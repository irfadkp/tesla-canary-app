#!/usr/bin/env python3
"""
OpenTelemetry Python Runtime Metrics Demo

Comprehensive runtime metrics collection using OpenTelemetry System Metrics Instrumentation:
- Application metrics (requests, connections, duration)
- System CPU metrics (system.cpu.time, system.cpu.utilization)
- System memory metrics (system.memory.usage, system.memory.utilization)
- Process CPU metrics (process.runtime.cpython.cpu_time, process.runtime.cpython.cpu.utilization)
- Process memory metrics (process.runtime.cpython.memory)
- Process thread count (process.runtime.cpython.thread_count)
- Python GC metrics (process.runtime.cpython.gc.count)
- Network I/O metrics (system.network.io)
- Disk I/O metrics (system.disk.io)

Sends metrics to configured backends every 20 seconds with OTLP and console exporters.
Uses opentelemetry-instrumentation-system-metrics for automatic system metrics collection.
"""

import time
import yaml
import logging
from typing import Dict, Any

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

# Check system metrics instrumentation availability
try:
    from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
    SYSTEM_METRICS_AVAILABLE = True
except ImportError:
    SYSTEM_METRICS_AVAILABLE = False
    SystemMetricsInstrumentor = None  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check and log system metrics availability
if not SYSTEM_METRICS_AVAILABLE:
    logger.warning("opentelemetry-instrumentation-system-metrics not available. Install with: pip install opentelemetry-instrumentation-system-metrics")

# NOTE: HTTP OTLP exporter requires 'opentelemetry-exporter-otlp-proto-http' package
# Install it with: pip install opentelemetry-exporter-otlp-proto-http==1.28.2
HTTP_EXPORTER_AVAILABLE = False
OTLPMetricExporter = None

try:
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter  # type: ignore
    HTTP_EXPORTER_AVAILABLE = True
except ImportError:
    logger.warning("HTTP OTLP exporter not available. Install with: pip install opentelemetry-exporter-otlp-proto-http")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    print(f"\n{'='*60}")
    print("STEP 1: Loading Configuration")
    print(f"{'='*60}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✓ Configuration loaded successfully from: {config_path}")
        print(f"  - Service Name: {config['opentelemetry']['service_name']}")
        
        # Display configured exporters
        otlp_config = config['opentelemetry']['otlp']
        if otlp_config.get('http', {}).get('enabled', True):
            print(f"  - HTTP OTLP Endpoint: {otlp_config['http']['endpoint']}")
        if otlp_config.get('grpc', {}).get('enabled', False):
            print(f"  - gRPC OTLP Endpoint: {otlp_config['grpc']['endpoint']}")
        
        print(f"  - Export Interval: {config['opentelemetry']['metrics']['export_interval_millis']}ms")
        
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def create_resource(config: Dict[str, Any]) -> Resource:
    """Create OpenTelemetry resource with service information."""
    print(f"\n{'='*60}")
    print("STEP 2: Creating OpenTelemetry Resource")
    print(f"{'='*60}")
    
    otel_config = config['opentelemetry']
    
    resource_attributes = {
        SERVICE_NAME: otel_config['service_name'],
        SERVICE_VERSION: otel_config['service_version'],
        'entity.label.attribute': 'sample label for Pyton',
    }
    
    # Add custom resource attributes from config
    if 'resource_attributes' in otel_config:
        resource_attributes.update(otel_config['resource_attributes'])
    
    resource = Resource.create(resource_attributes)
    
    print("✓ Resource created with attributes:")
    for key, value in resource_attributes.items():
        print(f"  - {key}: {value}")
    
    return resource


def create_metric_readers(config: Dict[str, Any]) -> list:
    """Create metric readers with HTTP, gRPC, and Console exporters."""
    print(f"\n{'='*60}")
    print("STEP 3: Creating Metric Exporters and Readers")
    print(f"{'='*60}")
    
    otel_config = config['opentelemetry']
    export_interval_ms = otel_config['metrics']['export_interval_millis']
    export_timeout_ms = otel_config['metrics']['export_timeout_millis']
    
    readers = []
    exporter_count = 0
    
    # 1. HTTP OTLP Exporter
    if otel_config['otlp']['http'].get('enabled', True):
        exporter_count += 1
        print(f"\n[{exporter_count}/3] Setting up HTTP OTLP Exporter...")
        
        if not HTTP_EXPORTER_AVAILABLE:
            print("✗ HTTP OTLP Exporter NOT AVAILABLE")
            print("  - Package 'opentelemetry-exporter-otlp-proto-http' is not installed")
            print("  - Install with: pip install opentelemetry-exporter-otlp-proto-http==1.28.2")
            print("  - Skipping HTTP exporter configuration")
        else:
            try:
                http_config = otel_config['otlp']['http']
                
                # Prepare headers
                headers = http_config.get('headers', {})
                headers_tuple = tuple(headers.items()) if headers else None
                
                otlp_exporter = OTLPMetricExporter(  # type: ignore[misc]
                    endpoint=f"{http_config['endpoint']}/v1/metrics",
                    timeout=http_config.get('timeout', 10),
                    headers=headers_tuple,
                )
                
                otlp_reader = PeriodicExportingMetricReader(
                    exporter=otlp_exporter,
                    export_interval_millis=export_interval_ms,
                    export_timeout_millis=export_timeout_ms,
                )
                
                readers.append(otlp_reader)
                print(f"✓ HTTP OTLP Exporter configured:")
                print(f"  - Endpoint: {http_config['endpoint']}/v1/metrics")
                print(f"  - Export Interval: {export_interval_ms}ms ({export_interval_ms/1000}s)")
                print(f"  - Timeout: {http_config.get('timeout', 10)}s")
                if headers:
                    print(f"  - Headers: {len(headers)} custom header(s) configured")
                    for key in headers.keys():
                        print(f"    • {key}: ***")
            except Exception as e:
                logger.error(f"Failed to create HTTP OTLP exporter: {e}")
    else:
        print("\n[Skipped] HTTP OTLP Exporter (disabled in config)")
    
    # 2. gRPC OTLP Exporter
    if otel_config['otlp']['grpc'].get('enabled', False):
        exporter_count += 1
        print(f"\n[{exporter_count}/3] Setting up gRPC OTLP Exporter...")
        try:
            grpc_config = otel_config['otlp']['grpc']
            
            # Prepare headers as metadata tuple
            headers = grpc_config.get('headers', {})
            metadata = tuple(headers.items()) if headers else None
            
            grpc_exporter = GRPCMetricExporter(
                endpoint=grpc_config['endpoint'],
                timeout=grpc_config.get('timeout', 10),
                headers=metadata,
                insecure=grpc_config.get('insecure', True),
            )
            
            grpc_reader = PeriodicExportingMetricReader(
                exporter=grpc_exporter,
                export_interval_millis=export_interval_ms,
                export_timeout_millis=export_timeout_ms,
            )
            
            readers.append(grpc_reader)
            print(f"✓ gRPC OTLP Exporter configured:")
            print(f"  - Endpoint: {grpc_config['endpoint']}")
            print(f"  - Export Interval: {export_interval_ms}ms ({export_interval_ms/1000}s)")
            print(f"  - Timeout: {grpc_config.get('timeout', 10)}s")
            print(f"  - Insecure: {grpc_config.get('insecure', True)}")
            if headers:
                print(f"  - Headers: {len(headers)} custom header(s) configured")
                for key in headers.keys():
                    print(f"    • {key}: ***")
        except Exception as e:
            logger.error(f"Failed to create gRPC OTLP exporter: {e}")
    else:
        print("\n[Skipped] gRPC OTLP Exporter (disabled in config)")
    
    # 3. Console/Debug Exporter
    exporter_count += 1
    print(f"\n[{exporter_count}/3] Setting up Console Debug Exporter...")
    try:
        console_exporter = ConsoleMetricExporter()
        
        console_reader = PeriodicExportingMetricReader(
            exporter=console_exporter,
            export_interval_millis=export_interval_ms,
            export_timeout_millis=export_timeout_ms,
        )
        
        readers.append(console_reader)
        print(f"✓ Console Debug Exporter configured:")
        print(f"  - Export Interval: {export_interval_ms}ms ({export_interval_ms/1000}s)")
        print(f"  - Output: Console/stdout")
    except Exception as e:
        logger.error(f"Failed to create console exporter: {e}")
    
    print(f"\n✓ Total exporters configured: {len(readers)}")
    
    return readers


def setup_meter_provider(config: Dict[str, Any]) -> metrics.Meter:
    """Setup MeterProvider with configured exporters."""
    print(f"\n{'='*60}")
    print("STEP 4: Setting up MeterProvider")
    print(f"{'='*60}")
    
    resource = create_resource(config)
    readers = create_metric_readers(config)
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=readers,
    )
    
    metrics.set_meter_provider(meter_provider)
    
    print("\n✓ MeterProvider configured and set as global provider")
    
    meter = metrics.get_meter(
        name=config['opentelemetry']['service_name'],
        version=config['opentelemetry']['service_version'],
    )
    
    print(f"✓ Meter created: {config['opentelemetry']['service_name']}")
    
    return meter


def setup_system_metrics_instrumentation(config: Dict[str, Any]):
    """Setup automatic system metrics instrumentation."""
    print(f"\n{'='*60}")
    print("STEP 5: Setting up System Metrics Instrumentation")
    print(f"{'='*60}")
    
    if not SYSTEM_METRICS_AVAILABLE:
        print("\n⚠️  WARNING: opentelemetry-instrumentation-system-metrics is not installed!")
        print("   Install with: pip install opentelemetry-instrumentation-system-metrics")
        print("   System and runtime metrics will not be collected automatically\n")
        return None
    
    try:
        # Configure which metrics to collect
        print("\nConfiguring system metrics collection...")
        print("  - CPU metrics (system.cpu.time, system.cpu.utilization)")
        print("  - Memory metrics (system.memory.usage, system.memory.utilization)")
        print("  - Network I/O metrics (system.network.io)")
        print("  - Disk I/O metrics (system.disk.io)")
        print("  - Process CPU metrics (process.runtime.cpython.cpu_time, cpu.utilization)")
        print("  - Process memory metrics (process.runtime.cpython.memory)")
        print("  - Process thread count (process.runtime.cpython.thread_count)")
        print("  - Python GC metrics (process.runtime.cpython.gc.count)")
        print("\nNote: system.network.connections excluded (requires elevated permissions on macOS)")
        
        # Start the instrumentation with default configuration
        # This collects ALL available metrics including GC metrics
        # Note: system.network.connections may fail on macOS due to permissions
        # but the error is logged and doesn't stop other metrics from being collected
        print("\nUsing default configuration to collect all available metrics")
        print("(system.network.connections errors will be logged but won't stop collection)")
        instrumentor = SystemMetricsInstrumentor()  # type: ignore[misc]
        instrumentor.instrument()
        print("\n✓ System Metrics Instrumentation started successfully")
        print("✓ Automatic collection of system and runtime metrics enabled")
        
        return instrumentor
        
    except Exception as e:
        logger.error(f"Failed to setup system metrics instrumentation: {e}")
        return None


def create_application_metrics(meter: metrics.Meter) -> Dict[str, Any]:
    """Create application-level metrics instruments."""
    print(f"\n{'='*60}")
    print("STEP 6: Creating Application Metrics Instruments")
    print(f"{'='*60}")
    
    instruments = {}
    
    # Application-level metrics (simulated)
    print("\n[1/3] Creating request counter...")
    instruments['request_counter'] = meter.create_counter(
        name="app.requests.total",
        description="Total number of requests processed",
        unit="1",
    )
    print("✓ Counter created: app.requests.total")
    
    print("\n[2/3] Creating request duration histogram...")
    instruments['request_duration'] = meter.create_histogram(
        name="app.request.duration",
        description="Request duration in milliseconds",
        unit="ms",
    )
    print("✓ Histogram created: app.request.duration")
    
    print("\n[3/3] Creating active connections counter...")
    instruments['active_connections'] = meter.create_up_down_counter(
        name="app.connections.active",
        description="Number of active connections",
        unit="1",
    )
    print("✓ UpDownCounter created: app.connections.active")
    
    print(f"\n✓ Total application metrics created: {len(instruments)}")
    print("✓ System and runtime metrics are collected automatically by SystemMetricsInstrumentor")
    
    return instruments


def simulate_application_activity(instruments: Dict[str, Any], iteration: int):
    """Simulate application activity by recording metrics."""
    import random
    
    print(f"\n{'─'*60}")
    print(f"Iteration #{iteration}: Simulating Application Activity")
    print(f"{'─'*60}")
    
    # Simulate requests
    num_requests = random.randint(5, 15)
    print(f"\n[Activity 1/3] Processing {num_requests} requests...")
    for i in range(num_requests):
        instruments['request_counter'].add(1, {"endpoint": f"/api/v1/resource{i%3}"})
        duration = random.uniform(10, 500)
        instruments['request_duration'].record(duration, {"endpoint": f"/api/v1/resource{i%3}"})
    print(f"✓ Recorded {num_requests} requests with durations")
    
    # Simulate connection changes
    connection_change = random.randint(-2, 5)
    print(f"\n[Activity 2/3] Connection change: {connection_change:+d}")
    instruments['active_connections'].add(connection_change)
    print(f"✓ Updated active connections")
    
    # Observable gauges are automatically collected
    print(f"\n[Activity 3/3] Observable gauges (memory, CPU) will be collected automatically")
    print(f"✓ Activity simulation complete for iteration #{iteration}")


def main():
    """Main function to run the OpenTelemetry metrics demo."""
    print("\n" + "="*60)
    print("OpenTelemetry Python Runtime Metrics Demo")
    print("="*60)
    print("This demo collects comprehensive system and runtime metrics")
    print("using OpenTelemetry System Metrics Instrumentation")
    print("="*60)
    
    instrumentor = None
    
    try:
        # Load configuration
        config = load_config()
        
        # Setup OpenTelemetry MeterProvider
        meter = setup_meter_provider(config)
        
        # Setup automatic system metrics instrumentation
        instrumentor = setup_system_metrics_instrumentation(config)
        
        # Create application-level metrics instruments
        instruments = create_application_metrics(meter)
        
        print(f"\n{'='*60}")
        print("STEP 7: Starting Metrics Collection Loop")
        print(f"{'='*60}")
        print("\nMetrics will be exported every 20 seconds...")
        print("System metrics are collected automatically in the background")
        print("Press Ctrl+C to stop\n")
        
        # Run the application loop
        iteration = 0
        while True:
            iteration += 1
            
            # Simulate application activity
            simulate_application_activity(instruments, iteration)
            
            # Wait for next iteration
            print(f"\n{'─'*60}")
            print(f"Waiting 5 seconds before next activity simulation...")
            print(f"(Metrics export happens automatically every 20 seconds)")
            print(f"{'─'*60}\n")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Shutting down gracefully...")
        print("="*60)
        
        # Uninstrument system metrics if it was started
        if instrumentor and SYSTEM_METRICS_AVAILABLE:
            try:
                instrumentor.uninstrument()
                print("✓ System metrics instrumentation stopped")
            except Exception as e:
                logger.warning(f"Failed to uninstrument system metrics: {e}")
        
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
