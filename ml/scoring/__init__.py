"""
ML Scoring & Feature Attribution Package
=========================================
Point-in-time multi-factor feature building, chronological time-series splitting,
XGBoost primary model with LightGBM benchmark, and SHAP TreeExplainer feature attributions.
"""

from ml.scoring.explainers import ShapExplainer
from ml.scoring.feature_builder import FeatureBuilder
from ml.scoring.model_trainer import CompanyScoringModelTrainer
from ml.scoring.schemas import (
    CompanyPredictionOutput,
    CompanyScoringFeatures,
    FeatureAttribution,
    ModelBenchmarkComparison,
    PredictionDirection,
    RiskLabel,
)
from ml.scoring.split_utils import ChronologicalSplitIndices, ChronologicalSplitter, DataLeakageError

__all__ = [
    "ChronologicalSplitIndices",
    "ChronologicalSplitter",
    "CompanyPredictionOutput",
    "CompanyScoringFeatures",
    "CompanyScoringModelTrainer",
    "DataLeakageError",
    "FeatureAttribution",
    "FeatureBuilder",
    "ModelBenchmarkComparison",
    "PredictionDirection",
    "RiskLabel",
    "ShapExplainer",
]
