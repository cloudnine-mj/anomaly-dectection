from river import anomaly

class OnlineIsolationForestDetector:
    """
    River 기반 스트리밍 이상 탐지용 IsolationForest 유사 모델
    - HalfSpaceTrees 알고리즘을 사용
    """
    def __init__(self, n_trees: int = 100, height: int = 8, seed: int = 42):
        self.model = anomaly.HalfSpaceTrees(
            n_trees=n_trees,
            height=height,
            seed=seed
        )

    def score(self, x: dict) -> float:
        """
        단일 샘플 x에 대한 이상 점수 반환
        x: {feature_name: feature_value, ...}
        """
        return self.model.score_one(x)

    def learn(self, x: dict):
        """
        모델에 단일 샘플 x 학습
        """
        self.model.learn_one(x)

    def detect(self, x: dict, threshold: float) -> bool:
        """
        스트리밍 샘플 x가 threshold 이상 점수일 때 이상치로 간주
        학습(learn_one)도 함께 수행
        """
        score = self.score(x)
        self.learn(x)
        return score > threshold

# Example usage
if __name__ == '__main__':
    # 예시: 2차원 피쳐 스트림
    data_stream = [
        {'cpu': 0.5, 'mem': 0.7},
        {'cpu': 0.6, 'mem': 0.8},
        {'cpu': 0.1, 'mem': 0.2},
        # ...
    ]
    detector = OnlineIsolationForestDetector(n_trees=50, height=6)
    threshold = 0.8
    for x in data_stream:
        is_anomaly = detector.detect(x, threshold)
        print(f"Sample {x}, score > {threshold}? {is_anomaly}")
