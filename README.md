# 이상 탐지 시스템

Prometheus로 수집된 메트릭을 실시간으로 분석하는 Python 기반 이상 탐지 솔루션으로,  
완전 자동화된 파이프라인과 다채로운 모델·알림·모니터링·배포 기능을 제공합니다.

---

## 🔍 개요

- **Core 탐지 엔진** (`anomaly_detection.py`)  
  - Prometheus HTTP API `query_range` → 전·후방 결측치 보간 → IsolationForest 학습·탐지 → Slack/Alertmanager 알림  
  - `drift_detection: true` 설정 시 River ADWIN 기반 데이터 드리프트 감지 후 자동 재학습  

- **모델 모듈** (`models/`)  
  - `deep_autoencoder.py` : Keras 오토인코더  
  - `vae_detector.py`      : 변분 오토인코더(VAE)  
  - `lstm_detector.py`     : LSTM 오토인코더 시계열 이상 탐지  

- **스트리밍 학습** (`streaming/online_iforest.py`)  
  - River `HalfSpaceTrees` 활용 온라인 IForest 이상 점수·학습  

- **알림·억제** (`alerting/`)  
  - `alertmanager.py`   : Prometheus Alertmanager HTTP API 연동  
  - `suppression.py`    : Flapping 필터링·중복 제거·뮤팅 로직  

- **대시보드·리포팅** (`reporting/dashboard_and_reporting.py`)  
  - Grafana Dashboard 자동 생성/업데이트  
  - 일별 이상치 시계열 플롯(PNG) 및 HTML 리포트  

- **성능 모니터링** (`monitoring/metrics_exporter.py`)  
  - Prometheus exporter: 실행 지연(Histogram), 오류(Counter), 탐지 수(Counter), 마지막 실행(Gauge)  

- **정확도 백테스트** (`evaluation/evaluator.py`)  
  - 레이블링된 과거 데이터로 Precision·Recall·F1 계산 및 분류 리포트  

- **자동 재학습 스케줄러** (`retrain_scheduler.py`)  
  - APScheduler 기반 주기적·이벤트 기반 재학습 트리거  

- **Airflow 통합** (`dags/dag_anomaly_detection.py`)  
  - `PythonOperator`로 매일/환경변수 스케줄링  

- **Kubernetes 배포** (`k8s_manager.py` & `k8s/k8s_anomaly_manifest.yaml`)  
  - CronJob·ConfigMap·Secret 자동 생성/업데이트  

- **CI/CD** (`.github/workflows/ci.yml`)  
  - GitHub Actions: pytest·flake8 멀티파이썬 지원  

- **테스트 스위트** (`tests/`)  
  - `pytest`로 모델·억제·스트리밍·평가·재학습 모듈 검증  

---

## ⚙️ 설정 파일 (`config.yaml`)

```yaml
# Prometheus URL
prometheus_url: "http://prometheus.company.local:9090"

# PromQL 지표 리스트
metrics:
  - "node_cpu_seconds_total"
  - "node_memory_MemAvailable_bytes"

# 이상치 비율
contamination: 0.01

# 조회 윈도우 (분)
window_minutes: 60

# 쿼리 해상도
step: "60s"

# 모델 파일 경로
model_path: "anomaly_model.joblib"

# Slack Webhook URL (또는 빈 문자열)
slack_webhook_url: "https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"

# Alertmanager URL (optional)
alertmanager_url: "http://alertmanager.company.local:9093"

# 결과 CSV 파일명
output_csv: "anomaly_results.csv"

# 드리프트 감지 활성화
drift_detection: true

# (옵션) 자동 재학습 설정
run_interval_seconds: 3600
```
---

## 프로젝트 구조

```
anomaly-detection/
├── anomaly_detection.py               # 메인 탐지 스크립트
├── k8s_manager.py                     # Kubernetes 리소스 관리 유틸리티
├── config.yaml                        # 애플리케이션 설정 파일
├── requirements.txt                   # Python 의존성 목록
├── LICENSE                            # 라이선스 파일
├── README.md                          # 프로젝트 설명 및 실행 가이드
│
├── models/                            # 배치 모델 모듈
│   ├── __init__.py
│   ├── deep_autoencoder.py            # 딥 오토인코더
│   ├── vae_detector.py                # 변분 오토인코더(VAE)
│   └── lstm_detector.py               # LSTM 오토인코더
│
├── streaming/                         # 스트리밍 학습 모듈
│   └── online_iforest.py              # River HalfSpaceTrees 기반 이상 탐지
│
├── alerting/                          # 알림 관련 모듈
│   ├── alertmanager.py                # Prometheus Alertmanager 연동
│   └── suppression.py                 # Flapping·중복·뮤팅 억제 로직
│
├── reporting/                         # 대시보드 & 리포팅
│   └── dashboard_and_reporting.py     # Grafana 대시보드 + HTML 리포터
│
├── monitoring/                        # 성능 모니터링 (Prometheus exporter)
│   └── metrics_exporter.py            # 자체 메트릭 수집 및 HTTP 서버
│
├── evaluation/                        # 정확도 백테스트
│   └── evaluator.py                   # Precision/Recall/F1 평가 도구
│
├── retrain_scheduler.py               # 자동 재학습 스케줄러 (APScheduler)
│
├── dags/                              # Airflow 스케줄링
│   └── dag_anomaly_detection.py       # PythonOperator 기반 DAG
│
├── k8s/                               # Kubernetes 매니페스트
│   └── k8s_anomaly_manifest.yaml      # Namespace, ConfigMap, Secret, CronJob
│
├── .github/                           # GitHub Actions 설정
│   └── workflows/
│       └── ci.yml                     # CI 파이프라인 설정
│
└── tests/                             # pytest 유닛/통합 테스트
    ├── test_models.py
    ├── test_suppression.py
    ├── test_streaming.py
    ├── test_evaluator.py
    └── test_retrain_scheduler.py
```

## 🚀 프로젝트 고도화 내역

1. **모델 개선 및 고도화**
   - Autoencoder/VAE/LSTM 기반 딥러닝 시계열 이상 탐지  
   - `river`·`scikit-multiflow` 스트리밍 학습  
   - ADWIN/DDM 기반 데이터 드리프트 감지  

2. **파이프라인 자동화 및 배포**
   - Airflow DAG (`dags/dag_anomaly_detection.py`)  
   - 쿠버네티스 CronJob (`k8s/k8s_anomaly_manifest.yaml`)  
   - Docker 이미지 + Helm 차트 → GitHub Actions/GitLab CI 연동  

3. **알림·운영 고도화**
   - Prometheus Alertmanager → Slack/PagerDuty/Email 라우팅  
   - Flapping 필터링·중복 뮤팅·빈도 제어  
   - Grafana / Symphony A.I. 대시보드 + 주간·월간 리포트 자동 생성  

4. **운영 모니터링 및 평가**
   - 모델 레이턴시·배치 처리 시간·오류율 모니터링 → Prometheus + Grafana  
   - Precision·Recall·F1 주기적 백테스트 (레이블링된 과거 이벤트 활용)  
   - 이벤트 수·기간 기반 자동 재학습 및 성능 검증  

5. **코드·구성 관리**
   - Config as Code (YAML/JSON, dev/stage/prod 프로파일)  
   - 모듈화 & 테스트 (`pytest`/`unittest`)  
   - 구조화된 로깅 (JSON), OpenTelemetry 연동  

---

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
   pip install -r requirements.txt
   ```

3. **설정 파일 수정**
   - `config.yaml`에서 Prometheus URL, 지표, Slack Webhook 등 업데이트
   
4. **탐지 스크립트 실행**

   ```
   python anomaly_detection.py --config config.yaml
   ```

4. **Airflow 배포**

   ```
   cp dags/dag_anomaly_detection.py /path/to/airflow/dags/
   ```

5. **스크립트 실행**

   ```
   python anomaly_detection.py --config config.yaml
   ```

6. **Airflow 배포 (선택)**

   ```
   cp dags/dag_anomaly_detection.py /path/to/airflow/dags/
   ```

7. **Kubernetes CronJob 배포**

   ```
   kubectl apply -f k8s/k8s_anomaly_manifest.yaml
   ```
   
8. **CI 테스트**

   ```
   pytest -q
   ```