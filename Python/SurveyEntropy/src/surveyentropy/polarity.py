"""Criterion-based item polarity (scoring direction).

A Likert battery for a single construct usually mixes items worded *toward* the
construct and *against* it. Summing raw responses lets the two directions cancel
and compresses the total score, so items must be scored in a consistent
direction first.

Rather than reading polarity off the item wording (a manual judgement call, and
counter to the project's unsupervised spirit), we estimate each item's direction
from the sign of its Spearman correlation with a held-out construct *criterion*
(for the pilot, the 1-10 global self-rating ``ControlItem``). Items that increase
with the criterion are forward-keyed (+1); items that decrease are reverse-keyed
(-1) and get reflected within their scale, ``x -> (lo + hi) - x``.

The sign of a near-zero correlation is unstable at small N, so items below a
documented threshold are *flagged as borderline and left unflipped* rather than
silently reversed; their correlations are reported so they can be reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .dataset import SurveyData

DEFAULT_THRESHOLD = 0.2


@dataclass
class PolarityResult:
    """Per-item scoring direction estimated against the criterion.

    Attributes:
        polarity: applied sign per item (+1 forward, -1 reverse). Borderline
            items are left at +1 (unflipped).
        correlations: Spearman correlation of each item with the criterion.
        pvalues: two-sided p-value for each correlation.
        borderline: items whose ``|correlation|`` is below ``threshold`` (or
            undefined), left unflipped pending review.
        threshold: the ``|correlation|`` threshold used to decide flipping.
        corrected: sign-corrected response matrix (reverse items reflected).
        raw: the original response matrix.
        scales: per-item integer scale, carried through unchanged.
    """

    polarity: dict[str, int]
    correlations: dict[str, float]
    pvalues: dict[str, float]
    borderline: list[str]
    threshold: float
    corrected: pd.DataFrame
    raw: pd.DataFrame
    scales: dict[str, tuple[int, int]] = field(default_factory=dict)


def _criterion_correlation(
    item: pd.Series, criterion: pd.Series
) -> tuple[float, float]:
    """Spearman (r, p) over respondents present in both; NaN if too few/constant."""
    mask = item.notna() & criterion.notna()
    if int(mask.sum()) < 3:
        return float("nan"), float("nan")
    x = item[mask].astype(float).to_numpy()
    y = criterion[mask].astype(float).to_numpy()
    if np.unique(x).size < 2 or np.unique(y).size < 2:  # no variance -> undefined
        return float("nan"), float("nan")
    result = spearmanr(x, y)
    return float(result.statistic), float(result.pvalue)


def reflect_within_scale(column: pd.Series, scale: tuple[int, int]) -> pd.Series:
    """Reflect a column within its scale: ``x -> (lo + hi) - x`` (NA stays NA)."""
    lo, hi = scale
    return (lo + hi) - column


def estimate_polarity(
    data: SurveyData,
    *,
    criterion: pd.Series | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> PolarityResult:
    """Estimate item polarity from correlation with the criterion and sign-correct.

    Args:
        data: loaded survey with a response matrix and per-item scales.
        criterion: criterion values per respondent. Defaults to ``data.criterion``.
        threshold: items with ``|Spearman r| < threshold`` are flagged borderline
            and left unflipped.

    Raises:
        ValueError: if no criterion is available.
    """
    crit = criterion if criterion is not None else data.criterion
    if crit is None:
        raise ValueError("Polarity estimation requires a criterion (got None).")

    polarity: dict[str, int] = {}
    correlations: dict[str, float] = {}
    pvalues: dict[str, float] = {}
    borderline: list[str] = []
    corrected = {}

    for item in data.items:
        col = data.responses[item]
        r, p = _criterion_correlation(col, crit)
        correlations[item] = r
        pvalues[item] = p

        is_borderline = np.isnan(r) or abs(r) < threshold
        if is_borderline:
            borderline.append(item)
            sign = 1  # do not make a low-confidence flip
        else:
            sign = -1 if r < 0 else 1
        polarity[item] = sign

        scale = data.scales[item]
        corrected[item] = reflect_within_scale(col, scale) if sign == -1 else col.copy()

    corrected_df = pd.DataFrame(corrected, index=data.responses.index)

    return PolarityResult(
        polarity=polarity,
        correlations=correlations,
        pvalues=pvalues,
        borderline=borderline,
        threshold=threshold,
        corrected=corrected_df,
        raw=data.responses,
        scales=dict(data.scales),
    )
