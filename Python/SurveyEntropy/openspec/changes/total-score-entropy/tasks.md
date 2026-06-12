# Tasks

> Definition of Done for every task below: the code plus a check that actually exercises it both pass, the result is confirmed settled, then commit and push to `origin` (one commit per task — do not batch).

## 1. Project setup (uv + package skeleton)

- [x] 1.1 Initialize a uv project at the repo root: `pyproject.toml` (name, Python version, runtime deps numpy/pandas/scipy, dev dep pytest) and generate `uv.lock`. Add a `.gitignore` for `.venv/` and caches.
- [x] 1.2 Create the `src/` package layout (e.g. `src/surveyentropy/__init__.py`) and a `tests/` directory; confirm `uv run python -c "import surveyentropy"` and `uv run pytest` (no tests yet) both succeed.

## 2. survey-dataset capability

- [x] 2.1 Implement item identification: classify a column as a Likert item only if all non-missing values are integers in a single contiguous range; record its scale `[lo_i, hi_i]`. Reject free-text / multi-select columns.
- [x] 2.2 Implement the dataset loader: read a CSV into a respondents × items numeric matrix with explicit missing values (no coercion to zero), excluding non-item metadata columns and rejected columns; hold out the construct criterion (`ControlItem`) and demographics (`Sex`, `Age`) as retrievable respondent metadata; expose per-item scale metadata.
- [x] 2.3 Tests: on `sjalvskattning_data_clean.csv`, assert `Item40` (multi-select) is excluded, the Likert items are kept with scale 1–5, respondent count is 51, and `ControlItem`/`Sex`/`Age` are retrievable as metadata but absent from the item matrix; assert a blank cell is represented as missing, not as the low scale value.

## 3. item-polarity capability

- [x] 3.1 Implement criterion-based polarity: per item, Spearman correlation with the held-out criterion over jointly-present respondents → polarity sign (+1/−1) and the correlation value; flag items below a documented threshold as borderline.
- [x] 3.2 Implement sign correction: reflect reverse-keyed items within scale (`x → (lo_i+hi_i)−x`), leave forward-keyed items unchanged, and keep the raw matrix and per-item polarity available.
- [x] 3.3 Tests: on a synthetic battery with known polarity, recover the signs; a reverse item on 1–5 maps 1↔5 and stays in range; forward items are unchanged; a near-zero-correlation item is flagged borderline; on the pilot, report each item's criterion correlation (sanity-review the patience/impatience split).

## 4. total-score-entropy capability — distribution

- [x] 4.1 Implement per-respondent total-score computation for a subset `S` by row summation (on the sign-corrected matrix); drop respondents missing any item in `S` (listwise on the subset) and report the contributing N.
- [x] 4.2 Implement total-score histogram/distribution over the theoretical support `[Σ lo_i, Σ hi_i]` with a `bin_width` parameter (default 1), normalized to a probability distribution.
- [x] 4.3 Tests: a hand-built tiny matrix gives the expected total scores and normalized distribution; convolution of marginals is NOT used (verify on a correlated synthetic case that the result equals the empirical row-sum distribution, not the convolution); coarse `bin_width>1` still normalizes to 1.

## 5. total-score-entropy capability — entropy & efficiency

- [x] 5.1 Define an `EntropyEstimator` interface; implement plug-in and Miller–Madow estimators; make Miller–Madow the default.
- [x] 5.2 Implement entropy `H(S)` and efficiency `η(S) = H(S)/H_max ∈ [0,1]` on the total-score distribution; return `H`, `H_max`, `η`, contributing N, and occupied-bin count together (never `η` alone).
- [x] 5.3 Tests: uniform-over-`m`-bins gives `H ≈ ln m` and `η ≈ 1` within tolerance; a single-spike distribution gives `η = 0`; supplying a custom estimator through the interface is used without other code changes.

## 6. Small-N estimator characterization (decision support)

- [x] 6.1 Synthetic study: at N≈51 and a 1–5 scale, sweep subset size `k` and compare plug-in vs Miller–Madow entropy against a known/large-sample ground truth; quantify residual bias as a function of `k`. Record results (short note + a figure or table) to inform whether Miller–Madow suffices before the search relies on it.

## 7. Wrap-up

- [x] 7.1 Run the full pipeline end-to-end on the pilot (load → polarity/sign-correct → total-score entropy) for a couple of example subsets; sanity-check `η`, contributing N, and bin reporting, and confirm sign-corrected sums spread more than raw sums; update `src/` notes (or a short README) with how to run via `uv run`.
