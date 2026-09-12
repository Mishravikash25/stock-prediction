"""
SHAP TreeExplainer & Feature Attribution Engine
================================================
Calculates exact local Shapley feature contributions for XGBoost tree models.
Provides structured feature attributions and base values as the raw, deterministic
input for the explanation layer.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

from ml.scoring.schemas import CompanyScoringFeatures, FeatureAttribution

logger = logging.getLogger(__name__)


class ShapExplainer:
    """Computes exact local Shapley feature attributions on XGBoost models."""

    def __init__(
        self,
        model: Any,
        feature_names: Optional[List[str]] = None
    ) -> None:
        self.model = model
        self.feature_names = feature_names or CompanyScoringFeatures.feature_names()
        self._explainer = shap.TreeExplainer(model)
        
        # Handle scalar vs array expected_value
        exp_val = self._explainer.expected_value
        if isinstance(exp_val, (list, np.ndarray)):
            self.base_value = float(exp_val[0])
        else:
            self.base_value = float(exp_val)

    @property
    def expected_value(self) -> float:
        """Return the model's base expected value."""
        return self.base_value

    def explain_instance(
        self,
        features: Union[CompanyScoringFeatures, List[float], np.ndarray, pd.Series],
        top_k: int = 3
    ) -> Tuple[List[FeatureAttribution], List[FeatureAttribution], List[FeatureAttribution]]:
        """
        Explain a single company feature vector.
        Returns:
            (all_attributions, top_bullish_drivers, top_bearish_drivers)
        """
        if isinstance(features, CompanyScoringFeatures):
            feat_vals = features.to_feature_vector()
        elif isinstance(features, (pd.Series, dict)):
            feat_vals = [float(features[col]) for col in self.feature_names]
        elif isinstance(features, (list, np.ndarray)):
            feat_vals = [float(v) for v in np.array(features).flatten()]
        else:
            raise TypeError(f"Unsupported features type: {type(features)}")

        X = np.array(feat_vals).reshape(1, -1)
        shap_values_raw = self._explainer.shap_values(X)

        if isinstance(shap_values_raw, list):
            shap_vector = np.array(shap_values_raw[0]).flatten()
        else:
            shap_vector = np.array(shap_values_raw).flatten()

        raw_triplets = []
        for name, val, sv in zip(self.feature_names, feat_vals, shap_vector):
            raw_triplets.append((name, float(val), float(sv)))

        # Sort by absolute SHAP value descending
        sorted_triplets = sorted(raw_triplets, key=lambda t: abs(t[2]), reverse=True)

        attributions_sorted: List[FeatureAttribution] = []
        for rank_idx, (name, val, sv) in enumerate(sorted_triplets, 1):
            dir_inf = "BULLISH" if sv > 0 else ("BEARISH" if sv < 0 else "NEUTRAL")
            attributions_sorted.append(
                FeatureAttribution(
                    feature_name=name,
                    feature_value=round(val, 6),
                    shap_value=round(sv, 6),
                    rank=rank_idx,
                    direction_influence=dir_inf
                )
            )

        # Extract top bullish and bearish drivers
        bullish_drivers = [a for a in attributions_sorted if a.shap_value > 0][:top_k]
        bearish_drivers = [a for a in attributions_sorted if a.shap_value < 0][:top_k]

        return attributions_sorted, bullish_drivers, bearish_drivers

    def explain_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute SHAP values across an entire evaluation DataFrame."""
        X = df[self.feature_names].values
        shap_matrix = self._explainer.shap_values(X)
        if isinstance(shap_matrix, list):
            shap_matrix = shap_matrix[0]

        shap_df = pd.DataFrame(
            shap_matrix,
            columns=[f"shap_{col}" for col in self.feature_names],
            index=df.index
        )
        return shap_df
