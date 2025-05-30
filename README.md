# 이상 탐지 시스템

Prometheus로 수집된 메트릭을 실시간으로 분석하는 Python 기반 이상 탐지 솔루션으로,  
자동화된 파이프라인과 다채로운 모델·알림·모니터링·배포 기능을 제공합니다.

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

## 📄 프로젝트 구조

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

<details>
<summary>프로젝트 구조 상세 설명</summary>

- **`anomaly_detection.py`**  
  - 메인 탐지 스크립트  
  	- `PrometheusClient`: `query_range`로 메트릭 수집  
  	- `AnomalyDetector`: 전처리 → IsolationForest 학습·탐지  
  	- River ADWIN 기반 드리프트 감지 → Slack/Alertmanager 알림  

- **`k8s_manager.py`**  
  - Kubernetes 리소스 관리 유틸리티  
  	- CronJob, ConfigMap, Secret 생성·패치 메서드 제공  

- **`config.yaml`**  
  - 애플리케이션 설정 파일  
  	- Prometheus URL, 모니터링 지표 리스트  
  	- Slack Webhook, Alertmanager URL, 모델 경로, 드리프트 옵션 등  

- **`requirements.txt`**  
  - Python 의존성 목록  

- **`README.md`**  
  - 프로젝트 개요 및 실행 가이드  

- **`models/`** (배치 모델)   
  - **`deep_autoencoder.py`**: `DeepAutoencoderDetector` (Keras 오토인코더)  
  - **`vae_detector.py`**: `VariationalAutoencoderDetector` (VAE)  
  - **`lstm_detector.py`**: `LSTMAutoencoderDetector` (LSTM 오토인코더)  

- **`streaming/online_iforest.py`**  
  - `OnlineIsolationForestDetector` (River HalfSpaceTrees 기반 온라인 이상 탐지)  

- **`alerting/`**  
  - **`alertmanager.py`**: `AlertmanagerClient` (Alertmanager API 연동)  
  - **`suppression.py`**: `FlappingSuppressor`, `Deduplicator`, `MuteList` (필터링·중복 억제·뮤팅)  

- **`reporting/dashboard_and_reporting.py`**  
  - `GrafanaClient`:  
    - `create_or_update_dashboard()`, `get_dashboard()`  
  - `ReportGenerator`:  
    - `generate_time_series_plot()`, `generate_summary_html()`  

- **`monitoring/metrics_exporter.py`**  
  - `run_metrics_server()` (메트릭 HTTP 서버 기동)  
  - `instrumented_run()` (지연·오류·이상치 수·마지막 실행 시각 메트릭 업데이트)  

- **`evaluation/evaluator.py`**  
  - `AccuracyEvaluator` (Precision·Recall·F1 계산, 분류 리포트 생성)  

- **`retrain_scheduler.py`**  
  - APScheduler 기반 자동 재학습 스케줄러  

- **`dags/dag_anomaly_detection.py`**  
  - Airflow PythonOperator DAG (환경변수로 스케줄·설정 경로 제어)  

- **`k8s/k8s_anomaly_manifest.yaml`**  
  - Kubernetes 매니페스트 (Namespace, ConfigMap, Secret, CronJob)  

- **`.github/workflows/ci.yml`**  
  - GitHub Actions CI (pytest·flake8 멀티파이썬)  

- **`tests/`**  
  - pytest 유닛·통합 테스트 (`test_models.py`, `test_suppression.py`, `test_streaming.py`, `test_evaluator.py`, `test_retrain_scheduler.py`) 
  </details>

---

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


## 프로젝트 초기 구현 및 최종 구현 내역

### 1. 초기 구현

| 고도화 항목                  | 구현 여부 | 비고                                                    |
|----------------------------|----------|--------------------------------------------------------|
| 다변량 딥러닝 모델             | ❌ 미구현 | Autoencoder/VAE/LSTM 직접 적용 필요                         |
| 스트리밍 학습                | ❌ 미구현 | `river`·`scikit-multiflow` 연동 필요                      |
| 데이터 드리프트 감지           | ✅ 구현   | River ADWIN 기반 자동 재학습 트리거 포함                   |
| Airflow 자동화 (DAG)         | ✅ 구현   | `dags/dag_anomaly_detection.py`로 `PythonOperator` 처리     |
| Kubernetes CronJob          | ✅ 구현   | `k8s/k8s_anomaly_manifest.yaml` 매니페스트 제공             |
| Alertmanager 연동           | ❌ 미구현 | `requests.post` Slack Webhook만 처리                      |
| Alert 억제·중복 제거          | ❌ 미구현 | Flapping 필터링·뮤팅 로직 추가 필요                        |
| 대시보드·리포팅               | ❌ 미구현 | Grafana/Symphony A.I. 연동 필요                            |
| 성능 모니터링                | ❌ 미구현 | 자체 메트릭 수집(exporter), Prometheus 연동 필요            |
| 정확도 백테스트              | ❌ 미구현 | 레이블링된 과거 데이터 기반 평가 로직 필요                 |
| 자동 재학습 스케줄링           | ❌ 미구현 | 주기별·이벤트별 재학습 워크플로우 추가 필요                 |
| CI/CD 파이프라인             | ❌ 미구현 | GitHub Actions/GitLab CI 설정 파일 필요                   |
| 모듈화·테스트 (`pytest`/`unittest`) | ❌ 미구현 | 유닛/통합 테스트 코드 작성 필요                           |
| 구조화된 로깅·Tracing          | ❌ 미구현 | JSON 로깅, OpenTelemetry 연동 필요                        |


### 2. 최종 구현

| 항목                             | 구현 모듈/파일                                                      |
|---------------------------------|--------------------------------------------------------------------|
| 모델 개선 및 고도화              | `models/deep_autoencoder.py`<br>`models/vae_detector.py`<br>`models/lstm_detector.py`   |
| 스트리밍 학습                    | `streaming/online_iforest.py`                                      |
| 데이터 드리프트 감지             | `anomaly_detection.py` 내 ADWIN 트리거 (River)                    |
| Airflow DAG                     | `dags/dag_anomaly_detection.py`                                    |
| 쿠버네티스 CronJob               | `k8s/k8s_anomaly_manifest.yaml` + `k8s_manager.py`                |
| Alertmanager 연동               | `alerting/alertmanager.py`                                         |
| Flapping·중복·뮤팅 억제           | `alerting/suppression.py`                                          |
| 대시보드·리포팅                  | `reporting/dashboard_and_reporting.py`                             |
| 성능 모니터링 (Exporter)         | `monitoring/metrics_exporter.py`                                   |
| 정확도 백테스트                  | `evaluation/evaluator.py`                                          |
| 자동 재학습 스케줄러             | `retrain_scheduler.py`                                             |
| CI/CD (GitHub Actions)          | `.github/workflows/ci.yml`                                         |
| 유닛/통합 테스트                 | `tests/` 디렉터리의 `test_*.py`                                    |
| 구조화된 로깅·Tracing            | Python `logging` 전 모듈 적용 (JSON 포맷·OpenTelemetry 연동은 추가 구현) |

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
   
---

## 📝 프로젝트 회고

### 1. 프로젝트 배경  
- 기존 ELK(Logstash→Elasticsearch→Kibana) 배치 수집 구조의 한계  
  - 실시간 탐지 불가로 지연된 대응  
  - 데이터 증가에 따른 인덱싱 부하 및 운영 부담  
  - AI·자동화 기능 부재로 수동 대응 비효율  

- **목표**: SYMPHONY A.I. 기반 실시간 이상탐지·자동화·최적화를 통해 AIOps·MLOps 파이프라인 고도화  


### 2. 주요 이슈 및 원인 분석  
1. **정확도 부족**  
   - 룰 기반 탐지로 복잡한 트래픽 변화·단기 피크 감지 어려움 → false positive 잦음  
2. **수작업 의존**  
   - 리소스 최적화·알림·대시보드 생성 전부 수동  
   - 운영 효율성 저하, 담당자 의존도 증가  



### 3. 기술적 접근 및 최적화 과정  
1. **AI 기반 이상탐지 구조 운영**  
   - SYMPHONY A.I. → CPU/Memory 비정상 패턴 점수화 및 자동 알림  
2. **Prometheus + Exporter 체계 구축**  
   - 다양한 인프라 메트릭 수집 → SYMPHONY A.I. 연동  
3. **Airflow 기반 MLops 파이프라인**  
   - 수집→전처리→탐지→저장 DAG 자동화  
   - 스케줄링, 에러 핸들링, 재시도 통합 관리  
4. **Kubernetes 환경 운영 최적화**  
   - Helm 배포, PVC·리소스쿼터 설정, Pod 상태 모니터링  
   - false positive 추적·모델 피드백 개선  



### 4. 프로젝트 성과  
- **정확도 향상 & 경보 체계 고도화**  
  - AI 모델 적용으로 false positive 감소  
  - 세분화된 알림 기준으로 노이즈 감소  
- **운영 자동화 & 안정성 강화**  
  - Airflow DAG 완전 자동화로 생산성↑  
  - 오류 시 자동 알림·재시도로 운영 안정성 확보  
- **Kubernetes 환경 최적화**  
  - 반복 배포 자동화(Helm), 로그·모니터링 통합  
  - 리소스 과다 사용 탐지 및 스케일링 전략 개선  
- **기술 내재화 및 역량 확보**  
  - AIOps·MLOps·Kubernetes 통합 운영 경험 축적  
  - 실무 중심의 AI 이상탐지 모델 운영·튜닝 역량 강화  


### 5. 활용 기술  
- **이상탐지·AIOps**: SYMPHONY A.I., Prometheus, Exporter
- **데이터 파이프라인·자동화**: Apache Airflow, Shell Script, REST API  
- **컨테이너 인프라**: Kubernetes(Deployment·Scaling·PVC), Helm, Resource Quota  
