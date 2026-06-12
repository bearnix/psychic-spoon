"""Loading and item identification for survey response data.

A "valid Likert item" is a column whose non-missing values are all integers
inside a single contiguous integer scale ``[lo, hi]``. Columns that are not
items -- an index, a timestamp, the construct criterion, demographics, or
free-text / multi-select columns -- are kept out of the candidate item matrix.
The criterion and demographics are retained as respondent-level metadata rather
than discarded, because later steps (polarity estimation, validation) need them.

Missing responses are represented explicitly with pandas' nullable ``Int64``
(``pd.NA``); they are never coerced to a scale value such as the lowest category.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

import pandas as pd

_UNNAMED_INDEX = re.compile(r"^Unnamed: \d+$")


@dataclass
class SurveyData:
    """Result of loading a survey.

    Attributes:
        responses: respondents x items matrix of nullable integers (``Int64``).
        scales: per-item integer scale ``{item: (lo, hi)}``.
        criterion: held-out construct criterion, one value per respondent
            (e.g. a global self-rating), or ``None`` if not provided.
        demographics: respondent-level demographic columns.
        rejected: candidate columns that failed Likert validation
            (e.g. free-text / multi-select), mapped to a short reason.
    """

    responses: pd.DataFrame
    scales: dict[str, tuple[int, int]]
    criterion: pd.Series | None = None
    demographics: pd.DataFrame = field(default_factory=pd.DataFrame)
    rejected: dict[str, str] = field(default_factory=dict)

    @property
    def items(self) -> list[str]:
        return list(self.responses.columns)

    @property
    def n_respondents(self) -> int:
        return len(self.responses)


def identify_likert(
    column: pd.Series, scale: tuple[int, int] | None = None
) -> tuple[int, int] | None:
    """Return the integer scale ``(lo, hi)`` if ``column`` is a valid Likert item.

    A column qualifies when every non-missing value is an integer and, if
    ``scale`` is given, lies within ``[lo, hi]``. When ``scale`` is ``None`` the
    scale is inferred from the observed min/max. Returns ``None`` (reject) for
    free-text, multi-select, or non-integer columns.
    """
    non_missing = column.dropna()
    if non_missing.empty:
        return None

    numeric = pd.to_numeric(non_missing, errors="coerce")
    if numeric.isna().any():  # at least one value is not numeric at all
        return None
    if not (numeric == numeric.round()).all():  # non-integer numeric values
        return None

    values = numeric.astype("int64")
    if scale is None:
        lo, hi = int(values.min()), int(values.max())
    else:
        lo, hi = int(scale[0]), int(scale[1])
        if (values < lo).any() or (values > hi).any():
            return None
    if hi < lo:
        return None
    return lo, hi


def _to_nullable_int(column: pd.Series) -> pd.Series:
    """Coerce a validated item column to nullable Int64, preserving missing."""
    return pd.to_numeric(column, errors="coerce").astype("Int64")


def load_survey(
    path: str,
    *,
    criterion: str | None = None,
    demographics: Sequence[str] = (),
    id_columns: Sequence[str] = (),
    item_columns: Iterable[str] | None = None,
    item_scale: tuple[int, int] | None = None,
    drop_unnamed_index: bool = True,
) -> SurveyData:
    """Load survey data from a CSV into a :class:`SurveyData`.

    Args:
        path: CSV file path.
        criterion: column name to hold out as the construct criterion.
        demographics: column names to retain as respondent metadata.
        id_columns: non-item bookkeeping columns to exclude (e.g. a timestamp).
        item_columns: explicit candidate item columns. If ``None``, every column
            that is not the index, criterion, a demographic, or an id column is
            treated as a candidate and then validated.
        item_scale: shared integer scale ``(lo, hi)`` applied to all items
            (e.g. ``(1, 5)`` for the pilot). If ``None``, each item's scale is
            inferred from its observed values.
        drop_unnamed_index: drop saved ``Unnamed: N`` index columns.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if the file has no respondent rows.
    """
    try:
        df = pd.read_csv(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Survey file not found: {path}") from exc

    if len(df) == 0:
        raise ValueError(f"Survey file has no respondent rows: {path}")

    if drop_unnamed_index:
        df = df.drop(columns=[c for c in df.columns if _UNNAMED_INDEX.match(str(c))])

    non_items = set(id_columns) | set(demographics)
    if criterion is not None:
        non_items.add(criterion)

    if item_columns is None:
        candidates = [c for c in df.columns if c not in non_items]
    else:
        candidates = list(item_columns)

    scales: dict[str, tuple[int, int]] = {}
    rejected: dict[str, str] = {}
    accepted: list[str] = []
    for col in candidates:
        result = identify_likert(df[col], scale=item_scale)
        if result is None:
            rejected[col] = "not a contiguous-integer Likert column"
        else:
            scales[col] = result
            accepted.append(col)

    responses = pd.DataFrame(
        {col: _to_nullable_int(df[col]) for col in accepted}, index=df.index
    )

    criterion_series = df[criterion].copy() if criterion is not None else None
    demo_cols = [c for c in demographics if c in df.columns]
    demographics_df = df[demo_cols].copy()

    return SurveyData(
        responses=responses,
        scales=scales,
        criterion=criterion_series,
        demographics=demographics_df,
        rejected=rejected,
    )
