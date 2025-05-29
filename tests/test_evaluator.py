import pandas as pd
from evaluation.evaluator import AccuracyEvaluator

def test_accuracy_evaluator_metrics_and_report():
    df = pd.DataFrame({
        'true_label': [0, 1, 0, 1],
        'anomaly':    [0, 1, 1, 0]
    })
    ev = AccuracyEvaluator(df, label_col='true_label', score_col='anomaly')
    metrics = ev.compute_metrics()
    assert all(k in metrics for k in ('precision', 'recall', 'f1_score'))
    report = ev.report()
    assert 'precision' in report.lower() and 'recall' in report.lower()