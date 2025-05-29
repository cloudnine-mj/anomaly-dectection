import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import requests
import yaml
from sklearn.ensemble import IsolationForest

# Configure logging
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
        # Combine multi-series by summing or average as needed; here take first
        values = result[0]['values']
        timestamps, vals = zip(*values)
        idx = pd.to_datetime(timestamps, unit='s')
        return pd.Series(data=np.array(vals, dtype=float), index=idx)

class AnomalyDetector:
    """
    Fetch metrics, train/load model, and detect anomalies.
    """
    def __init__(self, cfg: dict):
        self.prom = PrometheusClient(cfg['prometheus_url'])
        self.metrics = cfg['metrics']
        self.contamination = cfg.get('contamination', 0.01)
        self.window = timedelta(minutes=cfg.get('window_minutes', 60))
        self.step = cfg.get('step', '60s')
        self.model_path = cfg.get('model_path', 'anomaly_model.joblib')
        self.slack_webhook = cfg.get('slack_webhook_url')
        self.model = None

    def fetch_data(self) -> pd.DataFrame:
        end = datetime.utcnow()
        start = end - self.window
        df = pd.DataFrame()
        for metric in self.metrics:
            series = self.prom.query_range(metric, start, end, self.step)
            df[metric] = series
        df = df.dropna()
        if df.empty:
            raise RuntimeError("No data fetched for metrics: {}".format(self.metrics))
        return df

    def preprocess(self, df: pd.DataFrame) -> np.ndarray:
        # Example: fill missing and scale; extendable for feature engineering
        df_ffill = df.ffill().bfill()
        return df_ffill.values

    def load_or_train(self, X: np.ndarray):
        try:
            self.model = joblib.load(self.model_path)
            logging.info("Loaded existing model from %s", self.model_path)
        except FileNotFoundError:
            logging.info("Training new model, saving to %s", self.model_path)
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X)
            joblib.dump(self.model, self.model_path)

    def detect(self, X: np.ndarray) -> np.ndarray:
        labels = self.model.predict(X)
        return labels

    def alert(self, anomalies: pd.DataFrame):
        # Send Slack alerts if webhook configured
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
        logging.info("Starting detection for metrics: %s", self.metrics)
        df = self.fetch_data()
        X = self.preprocess(df)
        self.load_or_train(X)
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


def main():
    parser = argparse.ArgumentParser(description="Enhanced anomaly detection with multimetric support and model persistence.")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to YAML config')
    args = parser.parse_args()

    cfg = ConfigLoader.load(args.config)
    detector = AnomalyDetector(cfg)
    results = detector.run()
    out_file = cfg.get('output_csv', 'anomaly_results.csv')
    results.to_csv(out_file)
    logging.info("Results written to %s", out_file)

if __name__ == '__main__':
    main()
