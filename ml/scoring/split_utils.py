"""
Chronological Time Series Split Utility
========================================
Shared split utility used by every model and evaluation pipeline in the project.
Strictly enforces chronological boundaries (Train < Validation < Test) with
explicit embargo buffers and overlap purging to eliminate autocorrelation leakage.

Random k-fold splitting on time series is strictly prohibited per .antigravity/rules.md.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataLeakageError(ValueError):
    """Raised when chronological ordering or embargo boundaries are violated."""
    pass


@dataclass(frozen=True)
class ChronologicalSplitIndices:
    """Explicit row indices for train, validation, and test partitions."""
    train_indices: np.ndarray
    val_indices: np.ndarray
    test_indices: np.ndarray
    train_range: Tuple[pd.Timestamp, pd.Timestamp]
    val_range: Tuple[pd.Timestamp, pd.Timestamp]
    test_range: Tuple[pd.Timestamp, pd.Timestamp]
    embargo_days: int
    purged_count: int


class ChronologicalSplitter:
    """
    Splits point-in-time time series datasets with non-overlapping chronological boundaries,
    configurable embargo buffer windows, and overlap purging.
    """

    def __init__(
        self,
        date_column: str = "as_of_date",
        embargo_days: int = 7,
        purged: bool = True
    ) -> None:
        self.date_column = date_column
        self.embargo_days = max(0, int(embargo_days))
        self.purged = bool(purged)

    def validate_chronological_boundaries(
        self,
        train_start: Union[str, date, datetime, pd.Timestamp],
        train_end: Union[str, date, datetime, pd.Timestamp],
        val_start: Union[str, date, datetime, pd.Timestamp],
        val_end: Union[str, date, datetime, pd.Timestamp],
        test_start: Union[str, date, datetime, pd.Timestamp],
        test_end: Union[str, date, datetime, pd.Timestamp]
    ) -> None:
        """
        Verify strict chronological ordering:
        train_start < train_end <= val_start < val_end <= test_start < test_end
        """
        t_start = pd.to_datetime(train_start)
        t_end = pd.to_datetime(train_end)
        v_start = pd.to_datetime(val_start)
        v_end = pd.to_datetime(val_end)
        te_start = pd.to_datetime(test_start)
        te_end = pd.to_datetime(test_end)

        if not (t_start < t_end):
            raise DataLeakageError(f"Train start ({t_start}) must be before train end ({t_end})")
        if not (t_end <= v_start):
            raise DataLeakageError(f"Train end ({t_end}) overlaps with validation start ({v_start})")
        if not (v_start < v_end):
            raise DataLeakageError(f"Val start ({v_start}) must be before val end ({v_end})")
        if not (v_end <= te_start):
            raise DataLeakageError(f"Val end ({v_end}) overlaps with test start ({te_start})")
        if not (te_start < te_end):
            raise DataLeakageError(f"Test start ({te_start}) must be before test end ({te_end})")

    def split_by_dates(
        self,
        df: pd.DataFrame,
        train_start: Union[str, date, datetime, pd.Timestamp],
        train_end: Union[str, date, datetime, pd.Timestamp],
        val_start: Union[str, date, datetime, pd.Timestamp],
        val_end: Union[str, date, datetime, pd.Timestamp],
        test_start: Union[str, date, datetime, pd.Timestamp],
        test_end: Union[str, date, datetime, pd.Timestamp],
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split a DataFrame into Train, Validation, and Test partitions based on explicit dates.
        Applies embargo window to buffer autocorrelation leakage between splits.
        """
        if self.date_column not in df.columns:
            raise KeyError(f"Date column '{self.date_column}' not found in DataFrame columns: {list(df.columns)}")

        self.validate_chronological_boundaries(
            train_start, train_end, val_start, val_end, test_start, test_end
        )

        dates = pd.to_datetime(df[self.date_column])
        t_start = pd.to_datetime(train_start)
        t_end = pd.to_datetime(train_end)
        v_start = pd.to_datetime(val_start)
        v_end = pd.to_datetime(val_end)
        te_start = pd.to_datetime(test_start)
        te_end = pd.to_datetime(test_end)

        # Apply embargo offset to validation and test starting points if requested
        embargo_delta = pd.Timedelta(days=self.embargo_days)
        effective_val_start = max(v_start, t_end + embargo_delta)
        effective_test_start = max(te_start, v_end + embargo_delta)

        train_mask = (dates >= t_start) & (dates <= t_end)
        val_mask = (dates >= effective_val_start) & (dates <= v_end)
        test_mask = (dates >= effective_test_start) & (dates <= te_end)

        train_df = df[train_mask].copy()
        val_df = df[val_mask].copy()
        test_df = df[test_mask].copy()

        purged_records = len(df) - (len(train_df) + len(val_df) + len(test_df))
        logger.info(
            "Chronological split complete: Train=%d, Val=%d, Test=%d (Purged/Embargoed=%d records)",
            len(train_df), len(val_df), len(test_df), purged_records
        )

        return train_df, val_df, test_df

    def walk_forward_splits(
        self,
        df: pd.DataFrame,
        n_splits: int = 3,
        min_train_days: int = 365,
        val_days: int = 90,
        test_days: int = 90,
    ) -> Iterator[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        Generate expanding walk-forward chronological folds.
        Train window expands over time while Val and Test windows slide forward.
        """
        if self.date_column not in df.columns:
            raise KeyError(f"Date column '{self.date_column}' not found in DataFrame")

        dates = pd.to_datetime(df[self.date_column]).sort_values()
        min_date = dates.min()
        max_date = dates.max()

        total_days = (max_date - min_date).days
        needed_days = min_train_days + self.embargo_days + val_days + self.embargo_days + test_days

        if total_days < needed_days:
            raise ValueError(
                f"Total date range ({total_days} days) is insufficient for walk-forward setup "
                f"requiring at least {needed_days} days."
            )

        step_days = (total_days - needed_days) // max(1, n_splits - 1) if n_splits > 1 else 0

        for i in range(n_splits):
            offset = i * step_days
            t_start = min_date
            t_end = min_date + pd.Timedelta(days=min_train_days + offset)

            v_start = t_end + pd.Timedelta(days=self.embargo_days)
            v_end = v_start + pd.Timedelta(days=val_days)

            te_start = v_end + pd.Timedelta(days=self.embargo_days)
            te_end = te_start + pd.Timedelta(days=test_days)

            if te_end > max_date:
                te_end = max_date

            train_df, val_df, test_df = self.split_by_dates(
                df,
                train_start=t_start,
                train_end=t_end,
                val_start=v_start,
                val_end=v_end,
                test_start=te_start,
                test_end=te_end
            )
            yield train_df, val_df, test_df
