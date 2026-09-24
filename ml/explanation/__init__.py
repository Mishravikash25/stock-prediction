"""
ML Explanation Package
======================
Schema-constrained LLM dual-thesis generation (Bull Case, Bear Case, Uncertainty Analysis)
and local SHAP feature attribution translation.
"""

from ml.explanation.schemas import DriverSummary, ExplanationReportSchema
from ml.explanation.thesis_generator import (
    BaseThesisGenerator,
    ExplanationEngine,
    LLMThesisGenerator,
    MockRuleBasedThesisGenerator,
)

__all__ = [
    "BaseThesisGenerator",
    "DriverSummary",
    "ExplanationEngine",
    "ExplanationReportSchema",
    "LLMThesisGenerator",
    "MockRuleBasedThesisGenerator",
]
