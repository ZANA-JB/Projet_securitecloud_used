from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    value: float


class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PredictIn(BaseModel):
    """Entrée pour /predict pour EduScore (7 features éducation)."""

    # 0=Primaire,1=Collège,2=Lycée,3=Supérieur
    level: int = Field(..., ge=0, le=3)

    # main_subject as categorical index (0..n)
    main_subject: int = Field(..., ge=0)

    average_grade: float = Field(..., ge=0, le=20)
    attendance_rate: float = Field(..., ge=0, le=100)
    study_hours_per_week: int = Field(..., ge=0)
    resources_access: int = Field(..., ge=0, le=3)

    # 0=Réussi,1=Échoué,2=Non passé
    last_exam_result: int = Field(..., ge=0, le=2)

    applicant_name: str | None = None


class PredictOut(BaseModel):
    prediction: str | int | float
    proba: list[float] | None = None
    score: int | None = None
    id: int | None = None


class PredictionHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_name: str | None = None
    features: dict | list | None = None
    prediction: str
    score: int | None = None
    amount: float | None = None
    duration_months: int | None = None
    created_at: datetime


class StatsKpi(BaseModel):
    total: int
    accepted_rate: float
    avg_score: float
    this_week: int


class StatsDailyPoint(BaseModel):
    day: str
    count: int


class StatsScoreBin(BaseModel):
    bin: str
    n: int


class StatsStatusSlice(BaseModel):
    name: str
    value: int


class AdminStats(BaseModel):
    kpi: StatsKpi
    daily: list[StatsDailyPoint]
    score_distribution: list[StatsScoreBin]
    status_breakdown: list[StatsStatusSlice]
