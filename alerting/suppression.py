import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

class FlappingSuppressor:
    # Flapping(진동) 필터링: 동일 alert_id가 short window 내에 반복 발생할 때 억제
    def __init__(self, window: timedelta, threshold: int):
        self.window = window
        self.threshold = threshold
        # 각 alert_id별 발생 시각 기록
        self.history: Dict[str, List[datetime]] = {}

    def should_suppress(self, alert_id: str) -> bool:
        now = datetime.utcnow()
        times = self.history.get(alert_id, [])
        # window 내 기록만 유지
        times = [t for t in times if now - t <= self.window]
        times.append(now)
        self.history[alert_id] = times
        if len(times) >= self.threshold:
            logging.warning(f"Suppressing flapping alert '{alert_id}': {len(times)} occurrences within {self.window}")
            return True
        return False

class Deduplicator:
    # 중복 제거: 동일 alert_id가 dedup_window 내에 다시 들어오면 억제
    def __init__(self, dedup_window: timedelta):
        self.dedup_window = dedup_window
        self.last_seen: Dict[str, datetime] = {}

    def is_duplicate(self, alert_id: str) -> bool:
        now = datetime.utcnow()
        last = self.last_seen.get(alert_id)
        if last and now - last <= self.dedup_window:
            logging.info(f"Duplicate alert '{alert_id}' suppressed (last at {last})")
            return True
        self.last_seen[alert_id] = now
        return False

class MuteList:
    # 뮤팅: 특정 라벨 조합이 매치되면 완전 억제 -> mutes: List of label dicts to mute
    def __init__(self, mutes: List[Dict[str, Any]]):
        self.mutes = mutes

    def is_muted(self, labels: Dict[str, Any]) -> bool:
        for mute in self.mutes:
            if all(labels.get(k) == v for k, v in mute.items()):
                logging.info(f"Muted alert with labels {labels}")
                return True
        return False


def filter_alerts(
    alerts: List[Dict[str, Any]],
    flapping: FlappingSuppressor,
    deduplicator: Deduplicator,
    mute_list: MuteList
) -> List[Dict[str, Any]]:
    
    #flapping, deduplication, muting을 순차 적용하여 최종 전송할 alerts 반환
    
    filtered = []
    for alert in alerts:
        alert_id = alert.get('labels', {}).get('alertname', '')
        # 뮤팅
        if mute_list.is_muted(alert.get('labels', {})):
            continue
        # 중복 제거
        if deduplicator.is_duplicate(alert_id):
            continue
        # flapping 억제
        if flapping.should_suppress(alert_id):
            continue
        filtered.append(alert)
    return filtered

if __name__ == '__main__':
    from datetime import timedelta

    # 설정: 5분 window 내 3회 이상은 flapping
    flapper = FlappingSuppressor(window=timedelta(minutes=5), threshold=3)
    deduper = Deduplicator(dedup_window=timedelta(minutes=10))
    mutes = MuteList(mutes=[{'alertname': 'Heartbeat', 'severity': 'info'}])

    # alert list
    alerts = [
        {'labels': {'alertname': 'AnomalyDetected', 'severity': 'warning'}},
        {'labels': {'alertname': 'Heartbeat', 'severity': 'info'}},
    ]
    result = filter_alerts(alerts, flapper, deduper, mutes)
    print(f"Filtered alerts: {result}")
