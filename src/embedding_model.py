import numpy as np
from sklearn.neural_network import MLPRegressor

class EmbeddingModel:
    def __init__(self):
        # Initialize the model
        self.model = MLPRegressor(hidden_layer_sizes=(128, 64), max_iter=500)

    def train(self, X, y):
        """
        Train the model to learn embeddings.
        X: feature attributes (e.g., sensor readings)
        y: target values (e.g., actual embeddings)
        """
        self.model.fit(X, y)

    def predict(self, features):
        """
        Generate embeddings for new data.
        features: New input features
        """
        return self.model.predict(features)

    def save_model(self, filename):
        """Save the trained model to a file."""
        import joblib
        joblib.dump(self.model, filename)

    def load_model(self, filename):
        """Load a model from a file."""
        import joblib
        self.model = joblib.load(filename)
        
# Example usage:
# To train: embedding_model.train(X_train, y_train)
# To predict: embedding_model.predict(X_new)
