"""Entropy estimators and the flatness efficiency of a total-score distribution.

At the pilot's sample size (~51 respondents) the total-score histogram is sparse,
and the naive plug-in entropy is biased downward by roughly ``(K - 1) / (2N)``
(K occupied bins, N respondents) -- the same small-sample bias that under-counts
configurational entropy from a short trajectory. The Miller-Madow estimator adds
that term back and is the default; the plug-in is kept for comparison, and the
estimator is swappable so a Bayesian/NSB estimator can drop in later.

Raw entropy ``H`` lives on a support that grows with subset size, so it is not
comparable across subsets. The reported **efficiency** ``eta = H / H_max`` in
``[0, 1]`` normalizes that out (``H_max`` = the same estimator on a uniform
distribution over the same occupied bins), giving a bounded "how flat is it"
number ready to mix into a later combined objective.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from .totalscore import TotalScoreDistribution


@runtime_checkable
class EntropyEstimator(Protocol):
    """Maps integer bin counts to an entropy estimate in nats."""

    name: str

    def __call__(self, counts: np.ndarray) -> float: ...


def _plugin_entropy(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    n = counts.sum()
    if n <= 0:
        return 0.0
    p = counts[counts > 0] / n
    return float(-(p * np.log(p)).sum())


class PlugIn:
    """Maximum-likelihood (plug-in) entropy ``-sum p ln p``. Biased low at small N."""

    name = "plug-in"

    def __call__(self, counts: np.ndarray) -> float:
        return _plugin_entropy(counts)


class MillerMadow:
    """Plug-in entropy plus the ``(K - 1) / (2N)`` first-order bias correction."""

    name = "miller-madow"

    def __call__(self, counts: np.ndarray) -> float:
        counts = np.asarray(counts, dtype=float)
        n = counts.sum()
        if n <= 0:
            return 0.0
        k = int((counts > 0).sum())
        return _plugin_entropy(counts) + (k - 1) / (2.0 * n)


PLUG_IN = PlugIn()
MILLER_MADOW = MillerMadow()


@dataclass
class EntropyResult:
    """Entropy and flatness efficiency of a total-score distribution.

    Attributes:
        entropy: estimated Shannon entropy ``H`` (nats).
        max_entropy: ``H_max``, the estimator on a uniform distribution over the
            same number of occupied bins and respondents.
        efficiency: ``eta = H / H_max`` in ``[0, 1]`` (0 when <= 1 bin occupied).
        contributing_n: respondents backing the estimate.
        occupied_bins: bins with at least one respondent.
        estimator: name of the estimator used.
    """

    entropy: float
    max_entropy: float
    efficiency: float
    contributing_n: int
    occupied_bins: int
    estimator: str


def _uniform_counts(n: int, k: int) -> np.ndarray:
    """``n`` respondents spread as evenly as possible over ``k`` bins."""
    base, rem = divmod(n, k)
    return np.array([base + 1] * rem + [base] * (k - rem), dtype=float)


def entropy_efficiency(
    dist: TotalScoreDistribution, estimator: EntropyEstimator = MILLER_MADOW
) -> EntropyResult:
    """Estimate entropy and the flatness efficiency of ``dist``.

    Reports ``H``, ``H_max``, ``eta``, the contributing N, and the occupied-bin
    count together, so a high ``eta`` backed by few respondents is never read in
    isolation.
    """
    k = dist.occupied_bins
    h = estimator(dist.counts)
    if k <= 1:
        return EntropyResult(h, 0.0, 0.0, dist.contributing_n, k, estimator.name)

    h_max = estimator(_uniform_counts(dist.contributing_n, k))
    eta = h / h_max if h_max > 0 else 0.0
    return EntropyResult(
        entropy=h,
        max_entropy=h_max,
        efficiency=eta,
        contributing_n=dist.contributing_n,
        occupied_bins=k,
        estimator=estimator.name,
    )
