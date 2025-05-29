import time
from retrain_scheduler import RetrainScheduler

def test_event_based_retrain(tmp_path):
    calls = []
    def retrain():
        calls.append(True)

    # No periodic, event threshold=1 within 1 minute
    sched = RetrainScheduler(
        retrain_func=retrain,
        periodic_interval_hours=None,
        event_threshold=1,
        event_window_minutes=1
    )
    sched.record_event()
    time.sleep(0.1)  # allow immediate retrain
    assert calls == [True]
    sched.shutdown()