# SurveyEntropy

Empirical, model-free design of Likert surveys. Phase 1 selects item subsets by
the flatness of the **total-score distribution** (entropy efficiency) — a
CTT-flavored, unsupervised cousin of IRT optimal test design.

See `src/01_Framing_IRT_and_Critique.md` and `src/SurveysHistogram.md` for the
project framing, and `openspec/changes/` for the active design.

## Develop

```bash
uv sync            # create env + install deps
uv run pytest      # run the test suite
```

## Pipeline (Phase 1)

`load -> criterion-based polarity / sign-correction -> total-score entropy`:

```python
from surveyentropy.dataset import load_survey
from surveyentropy.polarity import estimate_polarity
from surveyentropy.totalscore import score_distribution
from surveyentropy.entropy import entropy_efficiency

data = load_survey(
    "sjalvskattning_data_clean.csv",
    criterion="ControlItem", demographics=["Sex", "Age"],
    id_columns=["time"], item_scale=(1, 5),
)
pol = estimate_polarity(data, threshold=0.2)        # flip reverse-keyed items
dist = score_distribution(pol.corrected, data.items, data.scales)
res = entropy_efficiency(dist)                       # H, H_max, eta, N, occupied bins
print(res.efficiency, res.contributing_n, res.occupied_bins)
```

- **`eta` is reported with `contributing_n` and `occupied_bins` on purpose.** At
  small N it is measured against the *occupied* bins, so it saturates near 1
  while `occupied / len(counts)` reveals how little of the theoretical support is
  actually covered. Read them together.
- Modules are decoupled so the objective (`entropy.py`) is independent of data
  handling and can later be swapped/extended without touching the rest.

## Scripts

```bash
uv run python examples/pilot_total_entropy.py          # end-to-end on the pilot
uv run --extra plot python studies/small_n_estimator_bias.py   # estimator bias study
```

See `studies/small_n_estimator_bias.md` for the small-N estimator characterization.
