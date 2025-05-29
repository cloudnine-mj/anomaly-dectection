import tensorflow as tf
from tensorflow.keras import layers, models

class DeepAutoencoderDetector:
    """
    Keras 기반 다변량 이상 탐지용 오토인코더 모델
    """
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        # 입력 레이어
        input_layer = layers.Input(shape=(input_dim,))
        # 인코딩 레이어
        encoded = layers.Dense(encoding_dim, activation='relu')(input_layer)
        # 디코딩 레이어
        decoded = layers.Dense(input_dim, activation='sigmoid')(encoded)

        # 모델 생성
        self.autoencoder = models.Model(inputs=input_layer, outputs=decoded)
        self.encoder = models.Model(inputs=input_layer, outputs=encoded)

        # 컴파일 설정
        self.autoencoder.compile(optimizer='adam', loss='mse')

    def fit(self, X, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.1):
        """
        모델 학습
        - X: numpy array of shape (n_samples, input_dim)
        """
        self.autoencoder.fit(
            X, X,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=1
        )

    def compute_reconstruction_error(self, X) -> tf.Tensor:
        """
        입력 X에 대한 재구성 오차(MSE) 계산
        """
        reconstructions = self.autoencoder.predict(X)
        mse = tf.keras.losses.mse(X, reconstructions)
        return mse

    def detect(self, X, threshold: float):
        """
        이상치 감지
        - threshold 이상인 샘플은 1, 아니면 0 반환
        """
        mse = self.compute_reconstruction_error(X)
        anomalies = (mse.numpy() > threshold).astype(int)
        return anomalies

# Example usage
if __name__ == '__main__':
    import numpy as np
    # 가상 데이터 (1000 samples, 10 features)
    X = np.random.rand(1000, 10)
    detector = DeepAutoencoderDetector(input_dim=10, encoding_dim=32)
    detector.fit(X, epochs=10, batch_size=64)
    errors = detector.compute_reconstruction_error(X)
    thresh = np.percentile(errors, 95)
    labels = detector.detect(X, threshold=thresh)
    print(f"Detected {labels.sum()} anomalies out of {len(labels)} samples")
