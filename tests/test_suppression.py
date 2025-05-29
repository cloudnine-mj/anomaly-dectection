import time
from datetime import timedelta
from alerting.suppression import (
    FlappingSuppressor,
    Deduplicator,
    MuteList,
    filter_alerts
)

def test_flapping_suppressor():
    sup = FlappingSuppressor(window=timedelta(seconds=1), threshold=2)
    assert not sup.should_suppress("a")
    time.sleep(0.5)
    assert sup.should_suppress("a")
    time.sleep(1.1)
    assert not sup.should_suppress("a")

def test_deduplicator():
    ded = Deduplicator(dedup_window=timedelta(seconds=1))
    assert not ded.is_duplicate("x")
    assert ded.is_duplicate("x")
    time.sleep(1.1)
    assert not ded.is_duplicate("x")

def test_mute_list():
    mutes = MuteList(mutes=[{'alertname': 'foo', 'severity': 'high'}])
    assert mutes.is_muted({'alertname': 'foo', 'severity': 'high'})
    assert not mutes.is_muted({'alertname': 'foo', 'severity': 'low'})

def test_filter_alerts():
    sup = FlappingSuppressor(window=timedelta(seconds=10), threshold=10)
    ded = Deduplicator(dedup_window=timedelta(seconds=10))
    mutes = MuteList(mutes=[{'alertname': 'mute', 'severity': 'info'}])
    alerts = [
        {'labels': {'alertname': 'a', 'severity': 'warn'}},
        {'labels': {'alertname': 'mute', 'severity': 'info'}}
    ]
    filtered = filter_alerts(alerts, sup, ded, mutes)
    assert len(filtered) == 1
    assert filtered[0]['labels']['alertname'] == 'a'