"""Endpoint d'inférence générique pour EduScore.

Construit la liste de features à partir des champs nommés du schéma `PredictIn`.
Persiste chaque prédiction en base pour l'admin dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.ml.credit_model import FEATURE_NAMES, LABELS
from app.models.prediction import Prediction
from app.models.user import User
from app.ratelimit import limiter
from app.schemas import PredictIn, PredictOut

router = APIRouter(prefix="/predict", tags=["ml"])


@router.post("", response_model=PredictOut)
@limiter.limit("20/minute")
def predict(
    payload: PredictIn,
    request: Request,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> PredictOut:
    model = request.app.state.model

    try:
        # Construire automatiquement la liste de features dans l'ordre FEATURE_NAMES
        features = [float(getattr(payload, name)) for name in FEATURE_NAMES]
        X = [features]
        proba_list: list[float] | None = None
        score: int | None = None

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            idx = int(proba.argmax())
            label = LABELS[idx] if idx < len(LABELS) else str(idx)
            proba_list = proba.tolist()
            # Score = probabilité maximale entre 0 et 100
            score = int(max(proba_list) * 100)
            prediction_str = label
        else:
            pred = model.predict(X)[0]
            prediction_str = str(float(pred))

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Le modèle a refusé l'input : {exc}. Vérifiez les champs envoyés.",
        ) from exc

    record = Prediction(
        applicant_name=payload.applicant_name,
        features=payload.model_dump(),
        prediction=prediction_str,
        score=score,
        proba=proba_list,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictOut(
        prediction=prediction_str,
        proba=proba_list,
        score=score,
        id=record.id,
    )
