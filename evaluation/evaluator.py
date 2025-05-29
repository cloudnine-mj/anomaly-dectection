import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class AccuracyEvaluator:
    def __init__(self, df: pd.DataFrame, label_col: str = 'true_label', score_col: str = 'anomaly'):
        self.df = df.dropna(subset=[label_col, score_col])
        self.y_true = self.df[label_col].astype(int)
        self.y_pred = self.df[score_col].astype(int)

    def compute_metrics(self):
        precision = precision_score(self.y_true, self.y_pred)
        recall = recall_score(self.y_true, self.y_pred)
        f1 = f1_score(self.y_true, self.y_pred)
        logging.info(f"Precision: {precision:.4f}")
        logging.info(f"Recall:    {recall:.4f}")
        logging.info(f"F1 Score:  {f1:.4f}")
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }

    def report(self) -> str:
        report_str = classification_report(self.y_true, self.y_pred, target_names=['normal','anomaly'])
        logging.info("Classification Report:\n%s", report_str)
        return report_str


if __name__ == '__main__':
    # 가상 라벨링 데이터 로드
    df = pd.read_csv('anomaly_results_with_labels.csv')
    evaluator = AccuracyEvaluator(df, label_col='true_label', score_col='anomaly')
    metrics = evaluator.compute_metrics()
    report = evaluator.report()
    print(report)
