"""Tests for entropy estimators and the flatness efficiency."""

from __future__ import annotations

import numpy as np

from surveyentropy.entropy import (
    MILLER_MADOW,
    PLUG_IN,
    EntropyResult,
    entropy_efficiency,
)
from surveyentropy.totalscore import TotalScoreDistribution


def make_dist(counts: list[int], bin_width: int = 1) -> TotalScoreDistribution:
    counts = np.asarray(counts, dtype=int)
    n = int(counts.sum())
    edges = np.arange(len(counts) + 1) - 0.5
    return TotalScoreDistribution(
        probabilities=counts / n if n else counts.astype(float),
        counts=counts,
        bin_edges=edges,
        bin_centers=edges[:-1] + 0.5,
        support_range=(0, len(counts) - 1),
        bin_width=bin_width,
        contributing_n=n,
        occupied_bins=int((counts > 0).sum()),
    )


# --- estimators on a known distribution ------------------------------------


def test_plugin_uniform_equals_log_m():
    m = 10
    counts = [10] * m  # exactly uniform, n = 100
    assert np.isclose(PLUG_IN(np.array(counts)), np.log(m))


def test_miller_madow_adds_bias_term():
    m = 10
    counts = np.array([10] * m)
    n = counts.sum()
    expected = np.log(m) + (m - 1) / (2 * n)
    assert np.isclose(MILLER_MADOW(counts), expected)
    assert MILLER_MADOW(counts) > PLUG_IN(counts)  # correction is positive


# --- efficiency bounds -----------------------------------------------------


def test_uniform_distribution_has_efficiency_one():
    dist = make_dist([10] * 8)  # flat over 8 bins
    res = entropy_efficiency(dist, estimator=MILLER_MADOW)
    assert np.isclose(res.efficiency, 1.0, atol=1e-9)
    assert np.isclose(res.entropy, np.log(8) + 7 / (2 * 80), atol=1e-9)


def test_uniform_efficiency_one_with_plugin_too():
    dist = make_dist([7] * 5)
    res = entropy_efficiency(dist, estimator=PLUG_IN)
    assert np.isclose(res.efficiency, 1.0)
    assert np.isclose(res.entropy, np.log(5))


def test_single_spike_has_efficiency_zero():
    dist = make_dist([0, 0, 12, 0, 0])  # everyone on one score
    res = entropy_efficiency(dist)
    assert res.occupied_bins == 1
    assert res.efficiency == 0.0
    assert res.max_entropy == 0.0


def test_result_reports_all_fields_together():
    dist = make_dist([5, 3, 2])
    res = entropy_efficiency(dist)
    assert isinstance(res, EntropyResult)
    assert res.contributing_n == 10
    assert res.occupied_bins == 3
    assert res.estimator == "miller-madow"
    assert 0.0 <= res.efficiency <= 1.0


# --- estimator is swappable through the interface --------------------------


def test_custom_estimator_is_used():
    class Sentinel:
        name = "sentinel"

        def __call__(self, counts: np.ndarray) -> float:
            return 42.0

    dist = make_dist([4, 4, 4, 4])  # uniform -> H_max also 42 -> eta = 1
    res = entropy_efficiency(dist, estimator=Sentinel())
    assert res.estimator == "sentinel"
    assert res.entropy == 42.0
    assert np.isclose(res.efficiency, 1.0)
