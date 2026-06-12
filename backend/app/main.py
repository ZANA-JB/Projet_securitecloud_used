"""Point d'entrée de l'API.

`load_dotenv()` charge le fichier .env s'il est trouvé en remontant l'arborescence.
En conteneur (Docker / ECS), il n'y a pas de .env : c'est un no-op, les variables
viennent de l'environnement.
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from slowapi import _rate_limit_exceeded_handler
# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded

from app.db import init_db
from app.ml.model import load_model
from app.ratelimit import limiter
from app.routes import admin, auth, health, items, predict
from app.routes import fields as fields_router

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as exc:
        logger.warning("Initialisation de la base ignorée au démarrage: %s", exc)
    app.state.model = load_model()
    yield


app = FastAPI(title="Projet Cloud - EduScore", version="0.2.0", lifespan=lifespan)

# Rate limiting (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /health expose a la racine pour le healthcheck du load balancer (ALB).
# Tout le reste de l'API est servi sous /api/*. Le frontend (nginx) ne
# fait plus de rewrite : il proxie /api/... tel quel vers le backend.
app.include_router(health.router)

app.include_router(health.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(fields_router.router, prefix="/api")
