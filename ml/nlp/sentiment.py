"""
Financial Sentiment Analyzer (FinBERT & Rule-Based Fallback)
============================================================
Computes polarized sentiment scores in range [-1.0, 1.0] for financial text.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Core financial polarity lexicon for fast/offline deterministic scoring
POSITIVE_FINANCIAL_TOKENS = {
    "surge", "surged", "surging", "growth", "profit", "profits", "profitable",
    "expansion", "expanding", "rebound", "rebounded", "gain", "gains",
    "rally", "rallied", "dividend", "upgrade", "upgraded", "relief", "boost"
}

NEGATIVE_FINANCIAL_TOKENS = {
    "plunge", "plunged", "plunging", "slump", "slumped", "loss", "losses",
    "contraction", "contracted", "hike", "hikes", "hiked", "disrupt", "disruption",
    "shortage", "halt", "halts", "halted", "default", "downgrade", "downgraded",
    "inflation", "pressure", "severe", "curb", "shut", "shutdown", "drop", "drops"
}


class SentimentAnalyzer:
    """Computes sentiment polarization for market headlines and announcements."""

    def __init__(self, use_transformers: bool = False) -> None:
        self.use_transformers = use_transformers
        self._pipeline = None
        if self.use_transformers:
            try:
                from transformers import pipeline
                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert",
                    tokenizer="ProsusAI/finbert"
                )
            except Exception as err:
                logger.info("FinBERT transformer weights not pre-cached; using fast deterministic financial lexicon: %s", err)
                self._pipeline = None

    def score(self, text: str) -> float:
        """Compute sentiment score in range [-1.0, 1.0]."""
        if not text or not text.strip():
            return 0.0

        if self._pipeline:
            try:
                res = self._pipeline(text[:512])[0]
                label = res["label"].lower()
                conf = float(res["score"])
                if label == "positive":
                    return round(conf, 4)
                elif label == "negative":
                    return round(-conf, 4)
                return 0.0
            except Exception as err:
                logger.warning("FinBERT inference exception, falling back to lexicon: %s", err)

        # Lexicon scoring
        tokens = text.lower().split()
        pos_count = sum(1 for t in tokens if t.strip(".,;:\"'!?()") in POSITIVE_FINANCIAL_TOKENS)
        neg_count = sum(1 for t in tokens if t.strip(".,;:\"'!?()") in NEGATIVE_FINANCIAL_TOKENS)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        raw_score = (pos_count - neg_count) / total
        return round(float(raw_score), 4)
