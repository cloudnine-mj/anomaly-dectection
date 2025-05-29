import tensorflow as tf
from tensorflow.keras import layers, models, backend as K

class VariationalAutoencoderDetector:
    """
    TensorFlow Keras 기반 변분 오토인코더(VAE)로 이상 탐지 구현
    """
    def __init__(self, input_dim: int, latent_dim: int = 16):
        # 인코더
        inputs = layers.Input(shape=(input_dim,))
        x = layers.Dense(64, activation='relu')(inputs)
        z_mean = layers.Dense(latent_dim, name='z_mean')(x)
        z_log_var = layers.Dense(latent_dim, name='z_log_var')(x)

        # 샘플링 레이어
        def sampling(args):
            mean, log_var = args
            epsilon = K.random_normal(shape=K.shape(mean), mean=0., stddev=1.)
            return mean + K.exp(0.5 * log_var) * epsilon

        z = layers.Lambda(sampling, output_shape=(latent_dim,), name='z')([z_mean, z_log_var])

        # 디코더
        decoder_input = layers.Input(shape=(latent_dim,))
        x_dec = layers.Dense(64, activation='relu')(decoder_input)
        outputs = layers.Dense(input_dim, activation='sigmoid')(x_dec)
        decoder = models.Model(decoder_input, outputs, name='decoder')

        # VAE 모델
        vae_outputs = decoder(z)
        self.vae = models.Model(inputs, vae_outputs, name='vae')

        # VAE 손실: 재구성 손실 + KL Divergence
        reconstruction_loss = tf.keras.losses.mse(inputs, vae_outputs)
        reconstruction_loss *= input_dim
        kl_loss = 1 + z_log_var - K.square(z_mean) - K.exp(z_log_var)
        kl_loss = -0.5 * K.sum(kl_loss, axis=-1)
        vae_loss = K.mean(reconstruction_loss + kl_loss)
        self.vae.add_loss(vae_loss)
        self.vae.compile(optimizer='adam')

    def fit(self, X, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.1):
        """
        VAE 모델 학습
        """
        self.vae.fit(
            X, None,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )

    def compute_reconstruction_error(self, X) -> tf.Tensor:
        """
        입력 X에 대한 재구성 오차(MSE) 계산
        """
        reconstructions = self.vae.predict(X)
        mse = tf.keras.losses.mse(X, reconstructions)
        return mse

    def detect(self, X, threshold: float):
        """
        재구성 오차가 threshold 초과 시 이상치(1), 아니면 정상(0)
        """
        mse = self.compute_reconstruction_error(X)
        anomalies = (mse.numpy() > threshold).astype(int)
        return anomalies

# Example usage
if __name__ == '__main__':
    import numpy as np
    X = np.random.rand(1000, 10)
    detector = VariationalAutoencoderDetector(input_dim=10, latent_dim=16)
    detector.fit(X, epochs=10, batch_size=64)
    errors = detector.compute_reconstruction_error(X)
    thresh = np.percentile(errors, 95)
    labels = detector.detect(X, threshold=thresh)
    print(f"Detected {labels.sum()} anomalies out of {len(labels)} samples")
