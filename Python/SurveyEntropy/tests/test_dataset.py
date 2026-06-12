"""Tests for the survey-dataset capability."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from surveyentropy.dataset import SurveyData, identify_likert, load_survey

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_CSV = PROJECT_ROOT / "sjalvskattning_data_clean.csv"

# Roles for the patience pilot (per sjalvskattning_keys.csv).
PILOT_KW = dict(
    criterion="ControlItem",
    demographics=["Sex", "Age"],
    id_columns=["time"],
    item_scale=(1, 5),
)


def load_pilot() -> SurveyData:
    return load_survey(str(PILOT_CSV), **PILOT_KW)


# --- identify_likert -------------------------------------------------------


def test_identify_accepts_integer_column_and_records_scale():
    col = pd.Series([1, 2, 3, 4, 5, 3, 2])
    assert identify_likert(col) == (1, 5)


def test_identify_uses_supplied_scale():
    col = pd.Series([2, 3, 4])  # observed 2..4 but the scale is 1..5
    assert identify_likert(col, scale=(1, 5)) == (1, 5)


def test_identify_rejects_value_outside_supplied_scale():
    col = pd.Series([1, 2, 9])
    assert identify_likert(col, scale=(1, 5)) is None


def test_identify_rejects_multiselect_text():
    col = pd.Series(["Instagram;Facebook", "Inget", "Instagram"])
    assert identify_likert(col) is None


def test_identify_ignores_missing_values():
    col = pd.Series([1.0, 2.0, None, 5.0])  # NaN forces float but values are integral
    assert identify_likert(col, scale=(1, 5)) == (1, 5)


# --- load_survey on the pilot ---------------------------------------------


@pytest.mark.skipif(not PILOT_CSV.exists(), reason="pilot CSV not present")
def test_pilot_respondent_count():
    assert load_pilot().n_respondents == 51


@pytest.mark.skipif(not PILOT_CSV.exists(), reason="pilot CSV not present")
def test_pilot_rejects_multiselect_item():
    data = load_pilot()
    assert "Item40" in data.rejected
    assert "Item40" not in data.items


@pytest.mark.skipif(not PILOT_CSV.exists(), reason="pilot CSV not present")
def test_pilot_items_kept_on_scale_1_to_5():
    data = load_pilot()
    # 41 candidate items minus the rejected multi-select column.
    assert len(data.items) == 40
    assert all(scale == (1, 5) for scale in data.scales.values())


@pytest.mark.skipif(not PILOT_CSV.exists(), reason="pilot CSV not present")
def test_pilot_criterion_and_demographics_held_out():
    data = load_pilot()
    assert data.criterion is not None
    assert len(data.criterion) == 51
    for meta in ("ControlItem", "Sex", "Age"):
        assert meta not in data.items
    assert list(data.demographics.columns) == ["Sex", "Age"]


# --- missing values are not coerced ---------------------------------------


def test_blank_cell_is_missing_not_low_value(tmp_path):
    csv = tmp_path / "tiny.csv"
    csv.write_text("Item1,Item2\n1,5\n,3\n4,2\n")
    data = load_survey(str(csv), item_scale=(1, 5))
    item1 = data.responses["Item1"]
    assert item1.isna().sum() == 1  # the blank stays missing, not coerced to a value
    assert pd.isna(item1.iloc[1])  # specifically the blank row
    # the other rows kept their real values (so the column wasn't zero-filled)
    assert item1.iloc[0] == 1 and item1.iloc[2] == 4


# --- error handling --------------------------------------------------------


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_survey("does_not_exist_12345.csv")


def test_empty_file_raises(tmp_path):
    csv = tmp_path / "empty.csv"
    csv.write_text("Item1,Item2\n")  # header only, no rows
    with pytest.raises(ValueError):
        load_survey(str(csv))
