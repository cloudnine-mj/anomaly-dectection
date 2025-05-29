import numpy as np
from models.deep_autoencoder import DeepAutoencoderDetector
from models.vae_detector import VariationalAutoencoderDetector
from models.lstm_detector import LSTMAutoencoderDetector

def test_deep_autoencoder_detect():
    X = np.random.rand(100, 10)
    det = DeepAutoencoderDetector(input_dim=10, encoding_dim=5)
    det.fit(X, epochs=1, batch_size=10)
    errors = det.compute_reconstruction_error(X)
    assert errors.shape == (100,)
    labels = det.detect(X, threshold=np.percentile(errors, 90))
    assert labels.shape == (100,)
    assert set(labels.tolist()) <= {0, 1}

def test_vae_detector_detect():
    X = np.random.rand(100, 10)
    det = VariationalAutoencoderDetector(input_dim=10, latent_dim=3)
    det.fit(X, epochs=1, batch_size=10)
    errors = det.compute_reconstruction_error(X)
    assert errors.shape == (100,)
    labels = det.detect(X, threshold=np.percentile(errors, 90))
    assert labels.shape == (100,)
    assert set(labels.tolist()) <= {0, 1}

def test_lstm_autoencoder_detect():
    X = np.random.rand(50, 5, 3)  # 50 samples, 5 timesteps, 3 features
    det = LSTMAutoencoderDetector(timesteps=5, n_features=3, latent_dim=2)
    det.fit(X, epochs=1, batch_size=10)
    errors = det.compute_reconstruction_error(X)
    assert errors.shape == (50,)
    labels = det.detect(X, threshold=np.percentile(errors, 90))
    assert labels.shape == (50,)
    assert set(labels.tolist()) <= {0, 1}