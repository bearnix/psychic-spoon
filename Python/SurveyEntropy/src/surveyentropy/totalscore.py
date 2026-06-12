"""Total-score distribution for an item subset.

The total score of a subset ``S`` is computed by **summing each respondent's
responses** across the items in ``S`` and binning the result -- never by
convolving per-item marginal histograms. Convolution would assume the items are
independent, but an internally consistent survey makes them correlated by
construction, so it gives the wrong distribution. (See design D3.)

The histogram support is the *theoretical* range ``[sum lo_i, sum hi_i]`` derived
from each item's scale, so the distribution is a property of the survey design
and population rather than of which scores happened to occur in a small sample.
Bin width is exposed (default 1, one bin per integer total) because coarse-
graining is the main lever against sparsity at small N.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TotalScoreDistribution:
    """Binned, normalized distribution of subset total scores.

    Attributes:
        probabilities: probability per bin (sums to 1).
        counts: respondent count per bin (sums to ``contributing_n``).
        bin_edges: histogram bin edges (length ``len(counts) + 1``).
        bin_centers: representative score at each bin center.
        support_range: theoretical ``(sum lo_i, sum hi_i)`` for the subset.
        bin_width: width of each bin in score units.
        contributing_n: respondents with no missing item in the subset.
        occupied_bins: number of bins with at least one respondent.
    """

    probabilities: np.ndarray
    counts: np.ndarray
    bin_edges: np.ndarray
    bin_centers: np.ndarray
    support_range: tuple[int, int]
    bin_width: int
    contributing_n: int
    occupied_bins: int


def total_scores(
    responses: pd.DataFrame, subset: Sequence[str]
) -> tuple[np.ndarray, int]:
    """Per-respondent total scores over ``subset`` by summation.

    Respondents missing any item in the subset are dropped (listwise on the
    subset). Returns the scores and the number of contributing respondents.
    """
    subset = list(subset)
    if not subset:
        raise ValueError("subset must contain at least one item")
    sub = responses[subset]
    mask = sub.notna().all(axis=1)
    scores = sub[mask].astype("int64").sum(axis=1).to_numpy()
    return scores, int(mask.sum())


def score_distribution(
    responses: pd.DataFrame,
    subset: Sequence[str],
    scales: dict[str, tuple[int, int]],
    bin_width: int = 1,
) -> TotalScoreDistribution:
    """Build the normalized total-score distribution for ``subset``.

    Args:
        responses: respondents x items matrix (nullable integers).
        subset: items to include in the total score.
        scales: per-item integer scale ``{item: (lo, hi)}``.
        bin_width: score units per bin (>= 1). 1 means one bin per integer total.

    Raises:
        ValueError: empty subset, ``bin_width < 1``, or no contributing respondents.
    """
    if bin_width < 1:
        raise ValueError("bin_width must be >= 1")
    subset = list(subset)

    lo_s = sum(scales[i][0] for i in subset)
    hi_s = sum(scales[i][1] for i in subset)

    scores, contributing_n = total_scores(responses, subset)
    if contributing_n == 0:
        raise ValueError("no respondents have complete responses for this subset")

    span = hi_s - lo_s + 1  # number of distinct integer totals
    n_bins = math.ceil(span / bin_width)
    # Half-integer edges so each integer total lands cleanly inside one bin.
    bin_edges = (lo_s - 0.5) + bin_width * np.arange(n_bins + 1)
    counts, _ = np.histogram(scores, bins=bin_edges)
    bin_centers = bin_edges[:-1] + bin_width / 2.0

    probabilities = counts / counts.sum()
    occupied_bins = int((counts > 0).sum())

    return TotalScoreDistribution(
        probabilities=probabilities,
        counts=counts,
        bin_edges=bin_edges,
        bin_centers=bin_centers,
        support_range=(lo_s, hi_s),
        bin_width=bin_width,
        contributing_n=contributing_n,
        occupied_bins=occupied_bins,
    )
