"""Tests for the item-polarity capability."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from surveyentropy.dataset import SurveyData, load_survey
from surveyentropy.polarity import estimate_polarity, reflect_within_scale

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_CSV = PROJECT_ROOT / "sjalvskattning_data_clean.csv"


def make_synthetic(n: int = 200, seed: int = 0) -> SurveyData:
    """A battery with a known forward item, a known reverse item, and noise."""
    rng = np.random.default_rng(seed)
    crit = rng.integers(1, 11, size=n)  # 1-10 latent self-rating
    forward = np.clip(np.round(crit / 2).astype(int), 1, 5)  # rises with crit
    reverse = 6 - forward  # falls with crit
    noise = rng.integers(1, 6, size=n)  # ~uncorrelated with crit

    responses = pd.DataFrame(
        {"fwd": forward, "rev": reverse, "noise": noise}
    ).astype("Int64")
    scales = {"fwd": (1, 5), "rev": (1, 5), "noise": (1, 5)}
    return SurveyData(
        responses=responses, scales=scales, criterion=pd.Series(crit, name="crit")
    )


# --- reflection ------------------------------------------------------------


def test_reflect_maps_endpoints_and_stays_in_range():
    out = reflect_within_scale(pd.Series([1, 5, 3, 2, 4]), (1, 5))
    assert list(out) == [5, 1, 3, 4, 2]
    assert out.min() >= 1 and out.max() <= 5


def test_reflect_preserves_missing():
    out = reflect_within_scale(pd.Series([1, None, 5], dtype="Int64"), (1, 5))
    assert pd.isna(out.iloc[1])
    assert out.iloc[0] == 5 and out.iloc[2] == 1


# --- polarity recovery -----------------------------------------------------


def test_recovers_known_signs():
    res = estimate_polarity(make_synthetic(), threshold=0.2)
    assert res.polarity["fwd"] == 1
    assert res.polarity["rev"] == -1
    assert res.correlations["fwd"] > 0
    assert res.correlations["rev"] < 0


def test_noise_item_flagged_borderline_and_unflipped():
    res = estimate_polarity(make_synthetic(), threshold=0.2)
    assert "noise" in res.borderline
    assert res.polarity["noise"] == 1  # borderline items are not flipped
    assert res.threshold == 0.2


def test_forward_unchanged_reverse_reflected_to_match():
    res = estimate_polarity(make_synthetic(), threshold=0.2)
    # forward item is untouched
    pd.testing.assert_series_equal(
        res.corrected["fwd"], res.raw["fwd"], check_names=False
    )
    # reverse item, once reflected, lines up with the forward direction
    pd.testing.assert_series_equal(
        res.corrected["rev"], res.corrected["fwd"], check_names=False
    )
    # all corrected values remain on the 1-5 scale
    assert res.corrected.min().min() >= 1 and res.corrected.max().max() <= 5


def test_missing_criterion_raises():
    data = make_synthetic()
    data.criterion = None
    with pytest.raises(ValueError):
        estimate_polarity(data)


# --- pilot sanity ----------------------------------------------------------


@pytest.mark.skipif(not PILOT_CSV.exists(), reason="pilot CSV not present")
def test_pilot_reports_correlation_per_item_with_mixed_signs():
    data = load_survey(
        str(PILOT_CSV),
        criterion="ControlItem",
        demographics=["Sex", "Age"],
        id_columns=["time"],
        item_scale=(1, 5),
    )
    res = estimate_polarity(data, threshold=0.2)
    # every kept item gets a reported correlation
    assert set(res.correlations) == set(data.items)
    assert len(res.correlations) == 40
    # the patience battery is mixed-keyed: both forward and reverse items appear
    signs = {res.polarity[i] for i in data.items if i not in res.borderline}
    assert signs == {1, -1}
