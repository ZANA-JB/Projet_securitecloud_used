"""Alias du modèle EduScore.

Ce module expose la même API que `app.ml.decrochage_model` sans dupliquer
la logique métier. Il est utilisé par les imports existants dans le backend
et les scripts de training.
"""

from app.ml.decrochage_model import (
    EXPECTED_FEATURE_COUNT,
    FEATURE_NAMES,
    LABELS,
    generate_training_data,
    train_credit_model,
)

__all__ = [
    "EXPECTED_FEATURE_COUNT",
    "FEATURE_NAMES",
    "LABELS",
    "generate_training_data",
    "train_credit_model",
]
