from streaming.online_iforest import OnlineIsolationForestDetector

def test_online_iforest_detect_type():
    det = OnlineIsolationForestDetector(n_trees=10, height=4, seed=0)
    x = {'cpu': 0.1, 'mem': 0.2}
    result = det.detect(x, threshold=1.0)
    assert isinstance(result, bool)