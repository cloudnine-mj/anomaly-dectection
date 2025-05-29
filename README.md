# 이상 탐지 시스템

Prometheus로 수집된 메트릭을 실시간으로 분석하는 Python 기반 이상 탐지 솔루션으로,  
확장 가능한 모델링·알림·배포 아키텍처를 제공합니다.

---

## 🔍 개요

- **PrometheusClient**  
  - Prometheus HTTP API의 `query_range`로 시계열 데이터를 조회  
  - 조회 기간(`window_minutes`)과 해상도(`step`) 설정 가능  
- **AnomalyDetector**  
  1. **fetch_data()**: 최근 _N_분 메트릭 로드  
  2. **preprocess()**: 전·후방 결측치 보간  
  3. **load_or_train()**: `joblib`으로 모델 저장/로드  
  4. **detect()**: IsolationForest로 이상치 예측  
  5. **alert()**: 로그 경고 및 Slack Webhook 전송  
- **옵션: 데이터 드리프트 감지**  
  - `drift_detection: true` 설정 시 `river.ADWIN` 기반 자동 재학습 트리거  
- **Kubernetes 연동 (k8s_manager.py)**  
  - CronJob, ConfigMap, Secret을 Python 코드로 생성/업데이트  
  - `create_or_update_cronjob()`, `create_or_update_configmap()`, `create_or_update_secret()` 제공  
- **Airflow 연동 (dags/dag_anomaly_detection.py)**  
  - `PythonOperator`로 스크립트를 스케줄링  
  - 환경변수로 스케줄(`ANOMALY_CRON`)·설정 경로(`CONFIG_PATH`) 제어  



## 프로젝트 구조

```
anomaly-detection/
├── anomaly_detection.py            # 메인 탐지 스크립트 (PrometheusClient, AnomalyDetector, 드리프트 감지 포함)
├── k8s_manager.py                  # Kubernetes 리소스 (CronJob/ConfigMap/Secret) 생성·업데이트 유틸
├── config.yaml                     # 애플리케이션 설정 (Prometheus URL, 메트릭, Webhook, 드리프트 등)
├── requirements.txt                # Python 의존성 목록
├── README.md                       # 프로젝트 설명 및 실행 가이드
├── LICENSE                         # 라이선스 파일
│
├── models/                         # 오프라인 배치 모델 모듈
│   ├── __init__.py
│   ├── deep_autoencoder.py         # 딥 오토인코더 이상 탐지
│   ├── vae_detector.py             # 변분 오토인코더(VAE) 탐지
│   └── lstm_detector.py            # LSTM 오토인코더 시계열 탐지
│
├── streaming/                      # 스트리밍 학습 모듈
│   └── online_iforest.py           # River HalfSpaceTrees 기반 온라인 IForest
│
├── dags/                           # Airflow 스케줄링
│   └── dag_anomaly_detection.py    # PythonOperator DAG
│
└── k8s/                            # Kubernetes 배포 매니페스트
    └── k8s_anomaly_manifest.yaml   # Namespace, ConfigMap, Secret, CronJob 통합 매니페스트
```


---

## ⚙️ 설정 파일 (`config.yaml`)

```yaml
# Prometheus URL
prometheus_url: "http://prometheus.company.local:9090"

# 모니터링할 PromQL 지표 리스트
metrics:
  - "node_cpu_seconds_total"
  - "node_memory_MemAvailable_bytes"

# 이상치 비율 (default: 0.01)
contamination: 0.01

# 조회 윈도우 (분)
window_minutes: 60

# 쿼리 해상도
step: "60s"

# 모델 파일 경로
model_path: "anomaly_model.joblib"

# Slack Webhook URL
slack_webhook_url: "https://hooks.slack.com/services/****"

# 결과 저장 CSV 파일명
output_csv: "anomaly_results.csv"

# 데이터 드리프트 감지 활성화 (river 라이브러리 필요)
drift_detection: true
```



## 🚀 고도화 방안

1. **모델 개선 및 고도화**
   - Autoencoder/VAE/LSTM 기반 딥러닝 시계열 이상 탐지
   - `river`·`scikit-multiflow` 스트리밍 학습
   - ADWIN/DDM 기반 데이터 드리프트 감지
2. **파이프라인 자동화 및 배포**
   - **Airflow DAG** (`dags/dag_anomaly_detection.py`)
   - **쿠버네티스 CronJob** (`k8s/k8s_anomaly_manifest.yaml`)
   - Docker 이미지 + Helm 차트 → GitHub Actions/GitLab CI 연동
3. **알림·운영 고도화**
   - Prometheus Alertmanager → Slack/PagerDuty/Email 라우팅
   - Flapping 필터링, 중복 뮤팅, 빈도 제어(예: 10분 내 3회 이하)
   - Grafana/Symphony A.I. 대시보드 + 주간·월간 리포트 자동 생성
4. **운영 모니터링 및 평가**
   - 모델 레이턴시·배치 처리 시간·오류율 모니터링 → Prometheus + Grafana
   - Precision/Recall/F1 주기적 백테스트(레이블링된 과거 이벤트 활용)
   - 이벤트 수·기간 기반 자동 재학습 및 성능 검증
5. **코드·구성 관리**
   - Config as Code (YAML/JSON, dev/stage/prod 프로파일)
   - 모듈화 & 테스트(`pytest`/`unittest`)
   - 구조화된 로깅(JSON), OpenTelemetry 연동

------

## 🚀 시작하기

1. **레포지토리 클론**

   ```
   git clone https://github.com/your-org/anomaly-detection.git
   cd anomaly-detection
   ```

2. **가상환경 생성 및 활성화**

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **의존성 설치**

   ```
   pip install -r requirements.txt
   ```

4. **설정 파일 수정**

   - `config.yaml`에서 Prometheus URL, 지표, Slack Webhook 등 업데이트

5. **스크립트 실행**

   ```
   python anomaly_detection.py --config config.yaml
   ```

6. **Airflow 배포 (선택)**

   ```
   cp dags/dag_anomaly_detection.py /path/to/airflow/dags/
   ```

7. **Kubernetes CronJob 배포 (선택)**

   ```
   kubectl apply -f k8s/k8s_anomaly_manifest.yaml
   ```