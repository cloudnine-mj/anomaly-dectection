import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from typing import Callable, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class RetrainScheduler:
    """
    자동 재학습 스케줄러

    - 주기적 재학습: 일정 시간 간격으로 retrain 함수를 호출
    - 이벤트 기반 재학습: 최근 window 내 anomaly 이벤트 수가 threshold 초과 시 retrain
    """
    def __init__(self,
                 retrain_func: Callable,
                 periodic_interval_hours: float = None,
                 event_threshold: int = None,
                 event_window_minutes: int = None):
        """
        retrain_func: 모델 재학습을 수행하는 함수
        periodic_interval_hours: 주기적 재학습 주기 (시간 단위)
        event_threshold: 이벤트 기반 재학습 임계치 (이상탐지 이벤트 수)
        event_window_minutes: 이벤트 기반 윈도우 크기 (분 단위)
        """
        self.retrain_func = retrain_func
        self.scheduler = BackgroundScheduler()
        self.events: List[datetime] = []
        self.event_threshold = event_threshold
        self.event_window = timedelta(minutes=event_window_minutes) if event_window_minutes else None

        # 주기적 스케줄 설정
        if periodic_interval_hours and periodic_interval_hours > 0:
            self.scheduler.add_job(
                self._trigger_retrain,
                'interval',
                hours=periodic_interval_hours,
                id='periodic_retrain'
            )
            logging.info(f"Scheduled periodic retrain every {periodic_interval_hours} hours")

        self.scheduler.start()
        logging.info("RetrainScheduler started")

    def record_event(self):
        """
        이상탐지 이벤트 발생 시 호출하여 기록
        이벤트 기반 재학습 임계치 검사 후 즉시 retrain 가능
        """
        now = datetime.utcnow()
        self.events.append(now)
        # 윈도우 내 이벤트만 남김
        if self.event_window:
            cutoff = now - self.event_window
            self.events = [t for t in self.events if t >= cutoff]
            if self.event_threshold and len(self.events) >= self.event_threshold:
                logging.info(
                    f"Event-based retrain triggered: {len(self.events)} events in last {self.event_window}"  
                )
                self._trigger_retrain()
                # 초기화
                self.events.clear()

    def _trigger_retrain(self):
        try:
            logging.info("Starting model retraining...")
            self.retrain_func()
            logging.info("Model retraining completed")
        except Exception as e:
            logging.error(f"Retraining failed: {e}")

    def shutdown(self):
        """
        스케줄러 종료
        """
        self.scheduler.shutdown()
        logging.info("RetrainScheduler stopped")


if __name__ == '__main__':
    from anomaly_detection import AnomalyDetector, ConfigLoader
    import time

    cfg = ConfigLoader.load('config.yaml')
    detector = AnomalyDetector(cfg)

    # 재학습 함수: 모델 피팅 로직
    def retrain_model():
        df = detector.fetch_data()
        X = detector.preprocess(df)
        # 강제 재학습
        detector.model = None  # 기존 모델 버림
        detector.load_or_train(X)

    # RetrainScheduler 설정 (매 24시간, 10분 window에 5회 이상 이벤트 시)
    scheduler = RetrainScheduler(
        retrain_func=retrain_model,
        periodic_interval_hours=24,
        event_threshold=5,
        event_window_minutes=10
    )

    try:
        # 주기 실행 및 이벤트 기록 데모
        while True:
            results = detector.run()
            # 이벤트 기록: 이상 탐지된 경우
            anomalies = results[results['anomaly'] == -1]
            for _ in anomalies.iterrows():
                scheduler.record_event()
            time.sleep(cfg.get('run_interval_seconds', 3600))  # 기본 1시간 주기
    except KeyboardInterrupt:
        scheduler.shutdown()