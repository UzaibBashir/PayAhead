"""Optional PyTorch expense-description classifier."""
from functools import lru_cache
from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).parents[1] / "app" / "ml" / "expense_mlp.pt"


@lru_cache(maxsize=1)
def _load():
    import torch
    from torch import nn

    artifact = torch.load(MODEL_PATH, map_location="cpu")
    vocabulary = artifact["vocab"]
    classes = artifact["classes"]
    model = nn.Sequential(
        nn.Linear(len(vocabulary), 64), nn.ReLU(), nn.Dropout(.15),
        nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, len(classes)),
    )
    model.load_state_dict(artifact["state_dict"])
    model.eval()
    return torch, model, vocabulary, classes


def predict(description: str) -> str:
    """Predict a category; caller handles unavailable optional dependencies."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    torch, model, vocabulary, classes = _load()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), vocabulary=vocabulary)
    vectorizer.fit([""])
    features = vectorizer.transform([description]).toarray().astype(np.float32)
    with torch.no_grad():
        category_index = int(model(torch.from_numpy(features)).argmax(1).item())
    return classes[category_index]
