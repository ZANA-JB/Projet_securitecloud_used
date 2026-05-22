"""Modèle de scoring crédit utilisé par le fallback et le script de training."""

from random import Random

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "age",
    "situation_familiale",
    "profession",
    "revenu_mensuel_kfcfa",
    "montant_demande_kfcfa",
    "duree_mois",
    "historique_credit",
]
EXPECTED_FEATURE_COUNT = len(FEATURE_NAMES)
LABELS = ["refusé", "accordé"]


def _decision_score(features: list[float], noise: float) -> float:
    age, situation, profession, revenu, montant, duree, historique = features
    mensualite = montant / max(duree, 1)
    taux_effort = mensualite / max(revenu, 1)

    score = 0.0
    score += min(revenu / 650, 1.5) * 1.2
    score += 0.7 if 25 <= age <= 55 else -0.25
    score += {0: 0.15, 1: 0.25, 2: -0.05, 3: 0.0}.get(int(situation), 0.0)
    score += {0: 0.65, 1: 0.35, 2: 0.2, 3: -0.45, 4: -0.9}.get(int(profession), -0.2)
    score += {0: -0.1, 1: -0.35, 2: 0.85, 3: -1.1}.get(int(historique), -0.1)
    score -= max(taux_effort - 0.28, 0) * 3.8
    score -= max(montant / max(revenu * 10, 1) - 1, 0) * 0.6
    score += noise
    return score


def generate_training_data(n_samples: int = 900, seed: int = 42) -> tuple[list[list[float]], list[int]]:
    """Génère un jeu d'exemple pour la démo MicroScore."""
    rng = Random(seed)
    X: list[list[float]] = []
    y: list[int] = []

    for _ in range(n_samples):
        age = rng.randint(18, 70)
        situation = rng.choices([0, 1, 2, 3], weights=[25, 55, 12, 8])[0]
        profession = rng.choices([0, 1, 2, 3, 4], weights=[38, 25, 18, 7, 12])[0]
        revenu = round(rng.uniform(45, 950), 1)
        montant = round(rng.uniform(50, 2500), 1)
        duree = rng.choice([3, 6, 9, 12, 18, 24, 36, 48, 60])
        historique = rng.choices([0, 1, 2, 3], weights=[28, 22, 38, 12])[0]

        features = [age, situation, profession, revenu, montant, duree, historique]
        accepted = 1 if _decision_score(features, rng.uniform(-0.35, 0.35)) >= 0.65 else 0
        X.append(features)
        y.append(accepted)

    return X, y


def train_credit_model(n_samples: int = 900, seed: int = 42):
    """Entraîne un classifieur simple et déterministe pour le template."""
    X, y = generate_training_data(n_samples=n_samples, seed=seed)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=seed),
    )
    model.fit(X, y)
    return model
