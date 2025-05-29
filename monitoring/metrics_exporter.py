from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time
import threading

# Metric 정의
REQUEST_LATENCY = Histogram(
    'anomaly_detection_request_latency_seconds',
    'Latency of anomaly detection run'
)
ERROR_COUNT = Counter(
    'anomaly_detection_errors_total',
    'Total number of errors during anomaly detection'
)
DETECTED_ANOMALIES = Counter(
    'anomaly_detection_anomalies_total',
    'Total number of anomalies detected'
)
LAST_RUN = Gauge(
    'anomaly_detection_last_run_timestamp',
    'Timestamp of the last anomaly detection run'
)

def run_metrics_server(port: int = 8000):
    """
    Starts the Prometheus metrics HTTP server in a separate thread.
    """
    def _start():
        start_http_server(port)
        # Keep the thread alive
        while True:
            time.sleep(1)
    t = threading.Thread(target=_start, daemon=True)
    t.start()
    print(f"Prometheus metrics server started on port {port}")

def instrumented_run(func):
    """
    Decorator to wrap the anomaly detection run function and update metrics.
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            results = func(*args, **kwargs)
        except Exception as e:
            ERROR_COUNT.inc()
            raise
        duration = time.time() - start
        REQUEST_LATENCY.observe(duration)
        # Count anomalies
        if hasattr(results, 'get'):
            # pandas DataFrame
            try:
                count = int(results['anomaly'].astype(bool).sum())
                DETECTED_ANOMALIES.inc(count)
            except Exception:
                pass
        LAST_RUN.set_to_current_time()
        return results
    return wrapper


if __name__ == '__main__':
    from anomaly_detection import main
    # Start metrics server
    run_metrics_server(port=8000)

    # Wrap the main run function
    from anomaly_detection import AnomalyDetector, ConfigLoader
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml')
    args = parser.parse_args()
    cfg = ConfigLoader.load(args.config)

    detector = AnomalyDetector(cfg)
    # Instrument the run method
    detector.run = instrumented_run(detector.run)

    # Execute detection loop
    while True:
        detector.run()
        # Sleep until next schedule (e.g., every minute)
        time.sleep(cfg.get('run_interval_seconds', 300))  
