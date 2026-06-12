"""Compatibilité pour l'ancien chemin d'import du modèle EduScore.

Plusieurs modules du backend importent encore `app.ml.credit_model`. Le code
réel vit dans `decrochage_model.py`; ce module réexporte simplement l'API.
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