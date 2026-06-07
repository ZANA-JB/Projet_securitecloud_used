"""Chargement du modèle ML.

Trois modes, dans l'ordre de priorité :

1. Si MODEL_S3_BUCKET est défini ou MODEL_PATH est un URI S3 → télécharger depuis S3.
2. Si un modèle local existe → charger depuis le disque.
3. Sinon → entraîner un modèle EduScore de démonstration à la volée.
"""

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import joblib

from app.ml.credit_model import EXPECTED_FEATURE_COUNT, LABELS, train_credit_model

logger = logging.getLogger(__name__)

MODEL_PATH_ENV = os.getenv("MODEL_PATH", "models/model.pkl")
MODEL_PATH_URL = urlparse(MODEL_PATH_ENV)
MODEL_LOCAL_PATH = Path(MODEL_PATH_ENV) if MODEL_PATH_URL.scheme in ("", "file") else Path("models/model.pkl")
MODEL_S3_BUCKET = os.getenv("MODEL_S3_BUCKET")
MODEL_S3_KEY = os.getenv("MODEL_S3_KEY", "model.pkl")
if not MODEL_S3_BUCKET and MODEL_PATH_URL.scheme == "s3":
    MODEL_S3_BUCKET = MODEL_PATH_URL.netloc
    MODEL_S3_KEY = MODEL_PATH_URL.path.lstrip("/")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")


def _download_from_s3() -> None:
    """Télécharge le modèle depuis S3 vers un chemin local temporaire."""
    import boto3

    logger.info("Téléchargement du modèle depuis s3://%s/%s", MODEL_S3_BUCKET, MODEL_S3_KEY)
    MODEL_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3.download_file(MODEL_S3_BUCKET, MODEL_S3_KEY, str(MODEL_LOCAL_PATH))
    logger.info("Modèle téléchargé vers %s", MODEL_LOCAL_PATH)


def _feature_count(model) -> int | None:
    return getattr(model, "n_features_in_", None)


def _class_count(model) -> int | None:
    classes = getattr(model, "classes_", None)
    return len(classes) if classes is not None else None


def _train_credit_fallback():
    """Entraîne un classifieur EduScore de démonstration et le sauvegarde en local si possible."""
    logger.warning("Aucun modèle compatible disponible, entraînement du fallback EduScore")
    clf = train_credit_model()
    MODEL_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_LOCAL_PATH)
    return clf


def load_model():
    """Charge le modèle selon le mode de priorité."""
    if MODEL_S3_BUCKET:
        try:
            _download_from_s3()
        except Exception as exc:
            logger.warning(
                "Impossible de télécharger le modèle depuis S3 (%s). Utilisation du fallback local.",
                exc,
            )

    if MODEL_LOCAL_PATH.exists():
        model = joblib.load(MODEL_LOCAL_PATH)
        n_features = _feature_count(model)
        n_classes = _class_count(model)

        if n_features in (None, EXPECTED_FEATURE_COUNT) and n_classes == len(LABELS):
            return model

        if MODEL_S3_BUCKET and n_features not in (None, EXPECTED_FEATURE_COUNT):
            raise ValueError(
                f"Le modèle S3 attend {n_features} features, "
                f"mais EduScore en fournit {EXPECTED_FEATURE_COUNT}."
            )

        logger.warning(
            "Modèle local incompatible (features=%s, classes=%s) ; régénération du fallback",
            n_features,
            n_classes,
        )

    return _train_credit_fallback()
