import requests
import logging
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 로깅 Configure 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class GrafanaClient:
    """
    Client for creating/updating dashboards and panels in Grafana via HTTP API.
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def create_or_update_dashboard(self, dashboard_payload: dict):
        """
        Create or update a Grafana dashboard.
        """
        url = f"{self.base_url}/api/dashboards/db"
        logging.info("Posting dashboard to %s", url)
        resp = requests.post(url, headers=self.headers, json=dashboard_payload)
        resp.raise_for_status()
        slug = resp.json().get('slug')
        logging.info("Dashboard created/updated: %s", slug)
        return slug

    def get_dashboard(self, uid: str):
        """
        Fetch an existing dashboard by UID.
        """
        url = f"{self.base_url}/api/dashboards/uid/{uid}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

class ReportGenerator:
    """
    Generate and save anomaly detection reports (plots + HTML summary).
    """
    def __init__(self, results_df: pd.DataFrame):
        self.results = results_df.copy()
        # Ensure timestamp index
        if not isinstance(self.results.index, pd.DatetimeIndex):
            self.results.index = pd.to_datetime(self.results.index)

    def generate_time_series_plot(self, output_path: str):
        """
        Plot anomaly count per time interval and save as PNG.
        """
        counts = self.results['anomaly'].resample('D').sum()
        plt.figure()
        counts.plot()
        plt.title('Daily Anomaly Count')
        plt.ylabel('Anomalies')
        plt.xlabel('Date')
        plt.tight_layout()
        plt.savefig(output_path)
        logging.info("Time series plot saved to %s", output_path)

    def generate_summary_html(self, plot_path: str, output_path: str):
        """
        Generate an HTML summary embedding the plot and basic stats.
        """
        total = len(self.results)
        anomalies = int(self.results['anomaly'].sum())
        anomaly_rate = anomalies / total * 100 if total > 0 else 0
        html = f"""
        <html>
          <head><title>Anomaly Detection Report</title></head>
          <body>
            <h1>Anomaly Detection Report</h1>
            <p>Total samples: {total}</p>
            <p>Total anomalies: {anomalies} ({anomaly_rate:.2f}%)</p>
            <h2>Daily Anomaly Count</h2>
            <img src='{plot_path}' alt='Daily Anomaly Count' />
          </body>
        </html>
        """
        with open(output_path, 'w') as f:
            f.write(html)
        logging.info("Summary HTML report saved to %s", output_path)

# Example usage
if __name__ == '__main__':
    # 예시 DataFrame 로딩
    df = pd.read_csv('anomaly_results.csv', index_col=0, parse_dates=True)
    # Grafana 대시보드 예시
    grafana = GrafanaClient('http://grafana.company.local:3000', api_key='YOUR_API_KEY')
    dashboard_payload = {
        'dashboard': {
            'uid': 'anomaly-dashboard',
            'title': 'Anomaly Detection Dashboard',
            'panels': [
                # grafana panel JSON here
            ]
        },
        'overwrite': True
    }
    grafana.create_or_update_dashboard(dashboard_payload)

    # 리포트 생성
    rg = ReportGenerator(df)
    plot_file = 'daily_anomaly_count.png'
    html_file = 'anomaly_report.html'
    rg.generate_time_series_plot(plot_file)
    rg.generate_summary_html(plot_file, html_file)
