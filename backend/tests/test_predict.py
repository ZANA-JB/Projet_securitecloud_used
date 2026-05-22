from fastapi.testclient import TestClient

from app.auth import create_jwt
from app.db import SessionLocal
from app.main import app
from app.models.user import User

FEATURES = [30, 1, 0, 200, 500, 12, 0]


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
        r = client.post("/api/predict", json={"features": FEATURES})
        assert r.status_code == 401


def test_predict_credit_fallback():
    """Vérifie le fallback MicroScore avec les 7 features du formulaire."""
    with TestClient(app) as client:
        r = client.post("/api/predict", json={"features": FEATURES}, headers=auth_headers())
        assert r.status_code == 200
        body = r.json()
        assert body["prediction"] in {"refusé", "accordé"}
        assert len(body["proba"]) == 2


def test_predict_rejects_wrong_feature_count():
    """Le backend renvoie 400 si le modèle refuse l'input (mauvaise shape)."""
    with TestClient(app) as client:
        r = client.post("/api/predict", json={"features": [1.0, 2.0, 3.0]}, headers=auth_headers())
        assert r.status_code == 400


def test_predict_rejects_empty_features():
    """Schéma Pydantic : features non vide."""
    with TestClient(app) as client:
        r = client.post("/api/predict", json={"features": []}, headers=auth_headers())
        assert r.status_code == 422


def test_predict_rate_limit():
    """Au-delà de 20 requêtes/minute depuis la même IP, le endpoint renvoie 429.

    Mesure anti model stealing : limite le clonage du modèle par requêtes massives.
    """
    with TestClient(app) as client:
        headers = auth_headers()
        statuses = [client.post("/api/predict", json={"features": FEATURES}, headers=headers).status_code for _ in range(25)]
        assert 429 in statuses, "Le rate limit aurait dû déclencher un 429"
