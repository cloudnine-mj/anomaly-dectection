import logging
import requests
from typing import List, Dict

class AlertmanagerClient:
    """
    Simple client for sending alerts to Prometheus Alertmanager.
    """
    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logging.info(f"AlertmanagerClient initialized with URL: {self.base_url}")

    def send_alerts(self, alerts: List[Dict]):
        """
        Send a list of alerts to Alertmanager.
        Each alert dict should follow Alertmanager API spec, e.g.:
          {
            'labels': {'alertname': 'AnomalyDetected', ...},
            'annotations': {'description': '...'},
            'startsAt': '2025-05-30T02:00:00Z',
            'endsAt': '0001-01-01T00:00:00Z'
          }
        """
        url = f"{self.base_url}/api/v1/alerts"
        try:
            resp = requests.post(url, json=alerts, timeout=self.timeout)
            resp.raise_for_status()
            logging.info(f"Sent {len(alerts)} alerts to Alertmanager")
        except Exception as e:
            logging.error(f"Failed to send alerts to Alertmanager: {e}")
            raise


if __name__ == '__main__':
    client = AlertmanagerClient('http://alertmanager.company.local:9093')
    alert = {
        'labels': {
            'alertname': 'AnomalyDetected',
            'severity': 'warning',
            'instance': 'node01'
        },
        'annotations': {
            'summary': 'Resource usage anomaly',
            'description': 'CPU usage > 90% for more than 5 minutes'
        },
        'startsAt': datetime.utcnow().isoformat() + 'Z',
        'endsAt': '0001-01-01T00:00:00Z'
    }
    client.send_alerts([alert])
