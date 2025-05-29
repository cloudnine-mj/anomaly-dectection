import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

class LSTMAutoencoderDetector:
    
    # LSTM Autoencoder 기반 시계열 이상 탐지 입력: (n_samples, timesteps, n_features)
    def __init__(self, timesteps: int, n_features: int, latent_dim: int = 64):
        self.timesteps = timesteps
        self.n_features = n_features
        self.latent_dim = latent_dim
        
        # 인코더
        inputs = layers.Input(shape=(timesteps, n_features))
        encoded = layers.LSTM(latent_dim, activation='tanh', return_sequences=False)(inputs)
        
        # RepeatVector를 통해 디코더 입력 크기 맞춤
        decoded_input = layers.RepeatVector(timesteps)(encoded)
        decoded = layers.LSTM(latent_dim, activation='tanh', return_sequences=True)(decoded_input)
        outputs = layers.TimeDistributed(layers.Dense(n_features))(decoded)

        # 모델 정의
        self.autoencoder = models.Model(inputs, outputs)
        self.autoencoder.compile(optimizer='adam', loss='mse')

    def fit(self, X: np.ndarray, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.1):
        # 모델 학습 - X: numpy array of shape (n_samples, timesteps, n_features)
        self.autoencoder.fit(
            X, X,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=1
        )

    def compute_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        # 입력 X에 대한 재구성 오차(MSE) 계산 / 반환값: shape (n_samples,) 재구성 평균 오차
        reconstructions = self.autoencoder.predict(X)
        # 샘플별 MSE 평균
        mse = np.mean(np.mean(np.square(X - reconstructions), axis=2), axis=1)
        return mse

    def detect(self, X: np.ndarray, threshold: float) -> np.ndarray:
        # 재구성 오차가 threshold 초과 시 이상치(1), 아니면 정상(0)
        errors = self.compute_reconstruction_error(X)
        return (errors > threshold).astype(int)

if __name__ == '__main__':
    # 가상 시계열 데이터 생성
    n_samples = 500
    timesteps = 30
    n_features = 5
    X = np.random.rand(n_samples, timesteps, n_features)

    detector = LSTMAutoencoderDetector(timesteps=timesteps, n_features=n_features, latent_dim=64)
    detector.fit(X, epochs=10, batch_size=32)

    errors = detector.compute_reconstruction_error(X)
    # 95 퍼센트 타일을 threshold로 사용
    thresh = np.percentile(errors, 95)
    labels = detector.detect(X, threshold=thresh)
    print(f"Detected {labels.sum()} anomalies out of {len(labels)} samples")
