"""Modèle EduScore pour le cas d'usage ÉDUCATION.

Fournit :
- FEATURE_NAMES : noms des features dans l'ordre attendu
- generate_training_data(...) : génération synthétique cohérente
- train_credit_model(...) : retourne un classifieur multi-classes
"""

from random import Random

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "level",
    "main_subject",
    "average_grade",
    "attendance_rate",
    "study_hours_per_week",
    "resources_access",
    "last_exam_result",
]
EXPECTED_FEATURE_COUNT = len(FEATURE_NAMES)
LABELS = ["En réussite", "À surveiller", "À risque de décrochage"]


def _decision_score(features: list[float], noise: float) -> float:
    """Calcul heuristique du score à partir des features éducation."""
    (
        level,
        main_subject,
        average_grade,
        attendance_rate,
        study_hours,
        resources_access,
        last_exam,
    ) = features

    score = 0.0
    # Importance de la note moyenne
    score += (average_grade / 20.0) * 5.0
    # Présence et qualité des ressources
    score += (resources_access / 3.0) * 1.0
    # Assiduité très importante
    score += (attendance_rate / 100.0) * 3.0
    # Heures d'étude
    score += min(study_hours / 20.0, 1.0) * 1.5
    # Niveau scolaire : on favorise le supérieur/lycée légèrement
    score += {0: -0.2, 1: 0.0, 2: 0.2, 3: 0.35}.get(int(level), 0.0)
    # Dernier examen : réussi aide, échoué pénalise
    score += {0: 0.6, 1: -0.6, 2: 0.0}.get(int(last_exam), 0.0)
    # Subject bias (not strong)
    score += {0: 0.1, 1: 0.0, 2: 0.15, 3: 0.05, 4: 0.0, 5: 0.05}.get(int(main_subject), 0.0)
    # Noise
    score += noise
    return score


def generate_training_data(n_samples: int = 900, seed: int = 42) -> tuple[list[list[float]], list[int]]:
    """Génère des exemples synthétiques pour l'usage ÉDUCATION.

    Labels : 0=En réussite, 1=À surveiller, 2=À risque de décrochage
    """
    rng = Random(seed)
    X: list[list[float]] = []
    y: list[int] = []

    for _ in range(n_samples):
        level = rng.choices([0, 1, 2, 3], weights=[30, 30, 25, 15])[0]
        main_subject = rng.choices(list(range(6)), weights=[25, 20, 20, 15, 10, 10])[0]
        average_grade = round(rng.uniform(5.0, 20.0), 1)
        attendance_rate = round(rng.uniform(50.0, 100.0), 1)
        study_hours = int(rng.choice([0, 1, 2, 3, 5, 7, 10, 12, 15, 20]))
        resources_access = rng.choices([0, 1, 2, 3], weights=[40, 30, 20, 10])[0]
        last_exam = rng.choices([0, 1, 2], weights=[60, 20, 20])[0]

        features = [
            level,
            main_subject,
            average_grade,
            attendance_rate,
            study_hours,
            resources_access,
            last_exam,
        ]

        base = _decision_score(features, rng.uniform(-0.5, 0.5))
        # convert base to class by thresholds
        if base >= 4.0:
            label = 0
        elif base >= 2.5:
            label = 1
        else:
            label = 2

        X.append(features)
        y.append(label)

    # Ensure all three risk classes appear in the training set.
    missing_labels = set(range(len(LABELS))) - set(y)
    for label in missing_labels:
        if label == 0:
            example = [3, 2, 18.0, 98.0, 15, 3, 0]
        elif label == 1:
            example = [2, 1, 12.0, 85.0, 8, 2, 1]
        else:
            example = [1, 4, 8.0, 62.0, 2, 0, 1]
        X.append(example)
        y.append(label)

    return X, y


def train_credit_model(n_samples: int = 900, seed: int = 42):
    """Entraîne un classifieur multi-classe pour le template EduScore."""
    X, y = generate_training_data(n_samples=n_samples, seed=seed)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=seed, multi_class='multinomial', solver='lbfgs'),
    )
    model.fit(X, y)
    return model
