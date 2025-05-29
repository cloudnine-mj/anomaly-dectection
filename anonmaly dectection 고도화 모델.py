import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import requests
import yaml
from sklearn.ensemble import IsolationForest

# drift detector
try:
    from river import drift
except ImportError:
    drift = None

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(module)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

class ConfigLoader:
    """
    Load YAML configuration for anomaly detection.
    """
    @staticmethod
    def load(path: str) -> dict:
        with open(path, 'r') as f:
            cfg = yaml.safe_load(f)
        return cfg

class PrometheusClient:
    """
    Prometheus HTTP API client for range queries.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def query_range(self, metric: str, start: datetime, end: datetime, step: str) -> pd.Series:
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            'query': metric,
            'start': start.timestamp(),
            'end': end.timestamp(),
            'step': step
        }
        logging.debug(f"Querying Prometheus: {metric} from {start} to {end} step={step}")
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        result = resp.json().get('data', {}).get('result', [])
        if not result:
            return pd.Series(dtype=float)
        values = result[0]['values']
        timestamps, vals = zip(*values)
        idx = pd.to_datetime(timestamps, unit='s')
        return pd.Series(data=np.array(vals, dtype=float), index=idx)

class DriftDetectorWrapper:
    """
    Wrapper around river.ADWIN for univariate drift detection.
    """
    def __init__(self):
        if not drift:
            raise RuntimeError("river library is required for drift detection")
        self.detector = drift.ADWIN()

    def check(self, values: np.ndarray) -> bool:
        """
        Return True if a drift is detected in the sequence of values.
        """
        for v in values:
            if self.detector.update(v):
                return True
        return False

class AnomalyDetector:
    """
    Fetch metrics, optionally detect data drift, train/load model, and detect anomalies.
    """
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.prom = PrometheusClient(cfg['prometheus_url'])
        self.metrics = cfg['metrics']
        self.contamination = cfg.get('contamination', 0.01)
        self.window = timedelta(minutes=cfg.get('window_minutes', 60))
        self.step = cfg.get('step', '60s')
        self.model_path = cfg.get('model_path', 'anomaly_model.joblib')
        self.slack_webhook = cfg.get('slack_webhook_url')
        self.model = None
        self.drift_detector = None
        if cfg.get('drift_detection', False):
            if drift:
                self.drift_detector = DriftDetectorWrapper()
                logging.info("Drift detection enabled using ADWIN")
            else:
                logging.warning("Drift detection requested but river not installed. Skipping.")

    def fetch_data(self) -> pd.DataFrame:
        end = datetime.utcnow()
        start = end - self.window
        df = pd.DataFrame()
        for metric in self.metrics:
            series = self.prom.query_range(metric, start, end, self.step)
            df[metric] = series
        df = df.ffill().bfill()
        if df.empty:
            raise RuntimeError(f"No data fetched for metrics: {self.metrics}")
        return df

    def load_or_train(self, X: np.ndarray):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logging.info("Loaded model from %s", self.model_path)
        else:
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X)
            joblib.dump(self.model, self.model_path)
            logging.info("Trained and saved model to %s", self.model_path)

    def detect(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def alert(self, anomalies: pd.DataFrame):
        for ts, row in anomalies.iterrows():
            msg = f"[ALERT] Anomaly at {ts} -> " + ", ".join([f"{m}={row[m]:.2f}" for m in row.index])
            logging.warning(msg)
            if self.slack_webhook:
                payload = {"text": msg}
                try:
                    resp = requests.post(self.slack_webhook, json=payload)
                    resp.raise_for_status()
                except Exception as e:
                    logging.error("Slack alert failed: %s", e)

    def run(self):
        logging.info("=== Starting anomaly detection ===")
        df = self.fetch_data()
        X = df.values

        # Data drift detection
        if self.drift_detector:
            # simple drift on feature mean
            means = X.mean(axis=1)
            if self.drift_detector.check(means):
                logging.info("Data drift detected. Forcing retrain.")
                os.remove(self.model_path) if os.path.exists(self.model_path) else None

        # Train or load model
        self.load_or_train(X)

        # Detect anomalies
        labels = self.detect(X)
        results = df.copy()
        results['anomaly'] = labels
        anomalies = results[results['anomaly'] == -1]
        if not anomalies.empty:
            logging.info("Detected %d anomalies", len(anomalies))
            self.alert(anomalies)
        else:
            logging.info("No anomalies detected.")
        return results


def main(config_path: str = 'config.yaml'):
    setup_logging()
    cfg = ConfigLoader.load(config_path)
    detector = AnomalyDetector(cfg)
    results = detector.run()
    out_file = cfg.get('output_csv', 'anomaly_results.csv')
    results.to_csv(out_file)
    logging.info("Results written to %s", out_file)


# --- Airflow DAG integration ---
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    default_args = {
        'owner': 'anomaly_team',
        'depends_on_past': False,
        'email_on_failure': True,
        'email': ['alerts@company.com'],
        'retries': 1,
        'retry_delay': timedelta(minutes=15)
    }
    dag = DAG(
        dag_id='anomaly_detection_pipeline',
        default_args=default_args,
        schedule_interval=os.getenv('ANOMALY_CRON', '0 2 * * *'),
        start_date=datetime(2025, 5, 1),
        catchup=False
    )

    run_task = PythonOperator(
        task_id='run_anomaly_detection',
        python_callable=main,
        op_kwargs={'config_path': os.getenv('CONFIG_PATH', 'config.yaml')},
        dag=dag
    )
except ImportError:
    # Not running inside Airflow
    pass

if __name__ == '__main__':
    main()
