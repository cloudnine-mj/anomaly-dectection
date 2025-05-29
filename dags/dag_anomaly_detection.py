import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')
from anomaly_detection import main as run_detection

default_args = {
    'owner': 'dataplatform_team',
    'depends_on_past': False,
    'email': ['alerts@company.com'], # 주소는 임의로 작성됨. (개인정보유출 방지)
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=15),
}


dag = DAG(
    dag_id='anomaly_detection_pipeline',
    default_args=default_args,
    description='Daily anomaly detection using Prometheus metrics and IsolationForest',
    schedule_interval=os.getenv('ANOMALY_CRON', '0 2 * * *'),  # Default: every day at 02:00
    start_date=datetime(2025, 5, 1),
    catchup=False,
    max_active_runs=1,
)

run_task = PythonOperator(
    task_id='run_anomaly_detection',
    python_callable=run_detection,
    op_kwargs={
        'config_path': os.getenv('CONFIG_PATH', '/opt/airflow/config/config.yaml')
    },
    dag=dag,
)

run_task