from fastapi import APIRouter

from app.ml import credit_model

router = APIRouter(tags=["meta"])


@router.get("/fields")
def get_fields():
    """Retourne la définition canonique des champs et options du formulaire."""
    subjects = [
        {"label": "Mathématiques", "value": 0},
        {"label": "Français", "value": 1},
        {"label": "Anglais", "value": 2},
        {"label": "Sciences", "value": 3},
        {"label": "Histoire", "value": 4},
        {"label": "Informatique", "value": 5},
    ]
    return {
        "feature_names": credit_model.FEATURE_NAMES,
        "labels": credit_model.LABELS,
        "main_subjects": subjects,
    }
