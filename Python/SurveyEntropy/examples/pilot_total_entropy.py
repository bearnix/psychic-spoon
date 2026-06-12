"""End-to-end total-score entropy on the patience pilot (task 7.1).

Pipeline: load -> criterion-based polarity / sign-correction -> total-score
entropy efficiency, for a couple of example subsets. Prints H, eta, contributing
N and bin reporting, and contrasts raw (mixed-keyed) sums against sign-corrected
sums -- the corrected total score should spread respondents more (higher eta),
because mixed keying otherwise cancels and peaks the distribution.

Run: ``uv run python examples/pilot_total_entropy.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from surveyentropy.dataset import load_survey
from surveyentropy.entropy import entropy_efficiency
from surveyentropy.polarity import estimate_polarity
from surveyentropy.totalscore import score_distribution

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_CSV = PROJECT_ROOT / "sjalvskattning_data_clean.csv"


def report(name, responses, subset, scales, bin_width=1):
    dist = score_distribution(responses, subset, scales, bin_width=bin_width)
    res = entropy_efficiency(dist)
    lo, hi = dist.support_range
    print(
        f"  {name:24s} k={len(subset):2d}  eta={res.efficiency:.3f}  "
        f"H={res.entropy:.3f}  support=[{lo},{hi}] "
        f"occupied={res.occupied_bins:2d}/{len(dist.counts):2d}  N={res.contributing_n}"
    )
    return res.efficiency


def main() -> None:
    data = load_survey(
        str(PILOT_CSV),
        criterion="ControlItem",
        demographics=["Sex", "Age"],
        id_columns=["time"],
        item_scale=(1, 5),
    )
    pol = estimate_polarity(data, threshold=0.2)
    raw, corrected, scales = data.responses, pol.corrected, data.scales

    print(f"Loaded pilot: {data.n_respondents} respondents, {len(data.items)} items "
          f"({len(pol.borderline)} borderline at threshold {pol.threshold}).")

    confident = [i for i in data.items if i not in pol.borderline]
    strong = sorted(
        data.items, key=lambda i: abs(np.nan_to_num(pol.correlations[i])), reverse=True
    )[:8]

    subsets = {
        "strong-8 (|r| largest)": strong,
        "all-confident": confident,
        "all-confident bin_width=3": confident,
    }

    for label, subset in subsets.items():
        width = 3 if "bin_width=3" in label else 1
        print(f"\n{label}:")
        raw_eta = report("raw (mixed-keyed)", raw, subset, scales, width)
        cor_eta = report("sign-corrected", corrected, subset, scales, width)
        verdict = "OK" if cor_eta > raw_eta else "!! not higher"
        print(f"  -> sign-corrected spreads more than raw: {verdict} "
              f"(+{cor_eta - raw_eta:.3f})")


if __name__ == "__main__":
    main()
