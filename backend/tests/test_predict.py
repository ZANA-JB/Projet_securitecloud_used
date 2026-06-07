from fastapi.testclient import TestClient

from app.auth import create_jwt
from app.db import SessionLocal
from app.main import app
from app.models.user import User

VALID_PAYLOAD = {
    "level": 2,
    "main_subject": 1,
    "average_grade": 14.5,
    "attendance_rate": 92.0,
    "study_hours_per_week": 10,
    "resources_access": 2,
    "last_exam_result": 0,
    "applicant_name": "Élève Test",
}


def auth_headers() -> dict[str, str]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "agent@example.test").first()
        if user is None:
            user = User(
                google_sub="agent-test-sub",
                email="agent@example.test",
                name="Agent Test",
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return {"Authorization": f"Bearer {create_jwt(user)}"}
    finally:
        db.close()


def test_predict_requires_authentication():
    """Le formulaire de scoring est privé : un JWT applicatif est requis."""
    with TestClient(app) as client:
        r = client.post("/api/predict", json=VALID_PAYLOAD)
        assert r.status_code == 401


def test_predict_eduscore_fallback():
    """Vérifie le fallback EduScore avec le schéma de prédiction éducation."""
    with TestClient(app) as client:
        r = client.post("/api/predict", json=VALID_PAYLOAD, headers=auth_headers())
        assert r.status_code == 200
        body = r.json()
        assert body["prediction"] in {"En réussite", "À surveiller", "À risque de décrochage"}
        assert len(body["proba"]) == 3


def test_predict_rejects_wrong_schema():
    """Le backend renvoie 422 si le schéma de prédiction n'est pas respecté."""
    invalid_payload = VALID_PAYLOAD.copy()
    invalid_payload["last_exam_result"] = 5
    with TestClient(app) as client:
        r = client.post("/api/predict", json=invalid_payload, headers=auth_headers())
        assert r.status_code == 422


def test_predict_rejects_missing_required_fields():
    """Schéma Pydantic : les champs requis doivent être fournis."""
    payload = {"applicant_name": "Élève Test"}
    with TestClient(app) as client:
        r = client.post("/api/predict", json=payload, headers=auth_headers())
        assert r.status_code == 422


def test_predict_rate_limit():
    """Au-delà de 20 requêtes/minute depuis la même IP, le endpoint renvoie 429.

    Mesure anti model stealing : limite le clonage du modèle par requêtes massives.
    """
    with TestClient(app) as client:
        headers = auth_headers()
        statuses = [client.post("/api/predict", json=VALID_PAYLOAD, headers=headers).status_code for _ in range(25)]
        assert 429 in statuses, "Le rate limit aurait dû déclencher un 429"
