"""Tests for the total-score distribution (total-score-entropy capability)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from surveyentropy.totalscore import score_distribution, total_scores


def df(data: dict) -> pd.DataFrame:
    return pd.DataFrame(data).astype("Int64")


# --- summation -------------------------------------------------------------


def test_total_scores_are_row_sums():
    responses = df({"a": [1, 2, 3], "b": [5, 4, 3]})
    scores, n = total_scores(responses, ["a", "b"])
    assert list(scores) == [6, 6, 6]
    assert n == 3


def test_listwise_drop_on_subset_reports_contributing_n():
    responses = df({"a": [1, None, 3], "b": [5, 4, 3]})
    scores, n = total_scores(responses, ["a", "b"])
    assert list(scores) == [6, 6]  # middle respondent dropped (missing a)
    assert n == 2


def test_empty_subset_raises():
    with pytest.raises(ValueError):
        total_scores(df({"a": [1, 2]}), [])


# --- distribution ----------------------------------------------------------


def test_distribution_support_and_normalization():
    responses = df({"a": [1, 3, 5], "b": [1, 3, 5]})
    scales = {"a": (1, 5), "b": (1, 5)}
    dist = score_distribution(responses, ["a", "b"], scales)
    assert dist.support_range == (2, 10)  # sum lo .. sum hi
    assert len(dist.counts) == 9  # integers 2..10
    assert dist.counts.sum() == 3
    assert np.isclose(dist.probabilities.sum(), 1.0)
    assert dist.contributing_n == 3


def test_coarse_binning_still_normalizes():
    responses = df({"a": [1, 2, 3, 4, 5], "b": [1, 2, 3, 4, 5]})
    scales = {"a": (1, 5), "b": (1, 5)}
    dist = score_distribution(responses, ["a", "b"], scales, bin_width=3)
    assert dist.bin_width == 3
    assert np.isclose(dist.probabilities.sum(), 1.0)
    assert dist.counts.sum() == 5
    assert len(dist.counts) < 9  # fewer, wider bins than the integer support


def test_bad_bin_width_raises():
    responses = df({"a": [1, 2]})
    with pytest.raises(ValueError):
        score_distribution(responses, ["a"], {"a": (1, 5)}, bin_width=0)


# --- the distribution is the empirical row-sum, NOT the convolution --------


def test_distribution_is_summation_not_convolution_of_marginals():
    # Two perfectly correlated items: b == a. The true total is 2*a, which only
    # ever lands on even totals. The convolution of the two identical marginals
    # would spread mass onto odd totals too -- so the two must disagree.
    a = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    responses = df({"a": a, "b": a})
    scales = {"a": (1, 5), "b": (1, 5)}
    dist = score_distribution(responses, ["a", "b"], scales)

    # Our distribution: totals are 2,4,6,8,10 only (centers at those integers).
    centers = dist.bin_centers
    odd_mass = dist.probabilities[(centers.astype(int) % 2) == 1].sum()
    assert np.isclose(odd_mass, 0.0)  # no mass on odd totals

    # Convolution of the (identical) marginals, assuming independence.
    marginal = np.array([a.count(v) for v in range(1, 6)], dtype=float)
    marginal /= marginal.sum()
    conv = np.convolve(marginal, marginal)  # support 2..10
    # The independence assumption puts real mass on odd totals (e.g. total 3).
    assert conv[1] > 0  # total == 3 has mass under convolution
    # ... which our empirical distribution does not -> they genuinely differ.
    empirical = dist.probabilities
    assert not np.allclose(empirical, conv)
