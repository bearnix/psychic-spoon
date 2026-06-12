## Why

The project's central design objective is the **entropy of the total-score distribution**, `H(S) = −Σ p ln p` over the histogram of per-respondent total scores for a candidate item subset `S`. A flat (high-entropy) total-score distribution means the survey spreads respondents evenly across its range instead of bunching them — the empirical, model-free shadow of a flat Test Information Function in IRT. ([Test Information Function](../../../src/01_Framing_IRT_and_Critique.md): in IRT, how precisely the test measures across the latent trait; the stat-mech analogue is wanting a measurement that resolves the whole reaction coordinate evenly rather than only near one value.)

Nothing in the repository computes this yet. The prototype `Survey.entropy()` in the old notebooks computes `Σ_i H(X_i)` — the *sum of per-item entropies* — which is a different object that is blind to inter-item correlation and therefore cannot express the H-vs-consistency tension the whole design rests on. Those notebooks predate the current goals and are treated as superseded scratch work.

The pilot measures a single construct — **patience/impatience** (tålamod). Its columns (per `sjalvskattning_keys.csv`) are: a timestamp; a `ControlItem` ("rate your own patience 1–10") that is a single global self-rating of the construct; `Sex` and `Age`; then `Item1`–`Item41`, the candidate battery (of which `Item40` is a multi-select "which social media do you use" column that is not Likert).

Three facts about this data make a naive implementation actively misleading, so they must be designed for from the start:

1. **Small N.** With ~51 respondents and a total-score support of `4k+1` values for a `k`-item subset, by `k≈12` there is roughly one respondent per possible score. The plug-in entropy estimator is then dominated by sampling noise and carries a downward bias of order `(bins−1)/(2N)` that *changes with subset size* — corrupting exactly the cross-subset comparison the search will rely on. (Same small-sample entropy bias that under-counts configurational entropy from a short MD trajectory.)
2. **Support grows with `k`.** Raw `H(S)` lives on `[k, 5k]`, so larger subsets can score higher entropy merely by having more bins. Raw `H` is not comparable across subset sizes.
3. **Items are mixed-keyed.** The battery contains both patience-worded and impatience-worded items. Summing raw responses lets the two directions *cancel*, compressing total scores toward the middle and artificially lowering `H(S)`. The total score only measures the construct once items are scored in a consistent direction.

This change resolves the keying problem in the project's own unsupervised spirit: rather than assigning item polarity by hand from wording, it **detects each item's sign empirically from its correlation with the `ControlItem` global self-rating** and flips the negatively-correlated items. The `ControlItem` is held out as a criterion, never placed in the candidate pool.

This change builds the honest, size-comparable, bias-aware total-score flatness measure that the λ-sweep and Monte Carlo search will later optimize. It is Phase 1, single-construct, empirical/CTT only.

## What Changes

- Stand up the Python project with **uv** (`pyproject.toml` + `uv.lock`) and a `src/` package; the old notebooks are not migrated.
- Add a **survey-dataset** capability: load a respondent×item table, identify which columns are valid Likert items with a known integer scale `[lo_i, hi_i]`, and exclude non-Likert columns (the pilot file has free-text / multi-select columns named `ItemN`). Hold out the construct criterion (`ControlItem`) and demographics (`Sex`, `Age`) as separate respondent metadata rather than discarding them. Expose a respondent×item numeric matrix plus per-item scale metadata.
- Add an **item-polarity** capability: estimate each item's scoring direction from the sign of its (Spearman) correlation with the held-out criterion, flip negatively-correlated items, and produce a sign-corrected response matrix. Report each item's criterion correlation and flag borderline (near-zero) items rather than silently flipping them.
- Add a **total-score-entropy** capability: for a given item subset `S`, compute per-respondent total scores **by summing per respondent** (never by convolving marginal item histograms — that assumes independence the design deliberately violates), histogram them, and return:
  - the total-score distribution,
  - a Shannon entropy estimate with a **bias correction** (Miller–Madow as the default, behind a swappable estimator interface so NSB/Bayesian can drop in later),
  - a **flatness efficiency** `η(S) = H(S) / H_max ∈ [0,1]` so values are comparable across subset sizes and ready to mix into `F(S) = −H + λ(1−C)` later,
  - exposed **bin width** so coarse-graining can be used to fight sparsity.
- Establish the per-task Definition of Done (verified check + settle + commit & push to `origin`).

## Capabilities

### New Capabilities
- `survey-dataset`: Load respondent×item data, identify valid Likert items and their integer scales, exclude non-Likert columns, and hold out the construct criterion and demographics as respondent metadata. Expose a clean numeric response matrix with per-item scale metadata.
- `item-polarity`: Estimate per-item scoring direction from each item's correlation with the held-out criterion and produce a sign-corrected response matrix, reporting correlations and flagging borderline items.
- `total-score-entropy`: Compute the total-score distribution of an item subset and a bias-aware, size-comparable measure of its flatness (entropy and efficiency η).

### Modified Capabilities
- None (first specs in the project).

## Impact

- **New dependency tooling:** uv-managed `pyproject.toml` / `uv.lock`; runtime deps numpy, pandas, scipy (initially). Run via `uv run`.
- **New code:** a `src/` package containing the dataset loader, the criterion-based polarity step, and the total-score-entropy measure, with tests that exercise them on the pilot CSV and on synthetic cases with known entropy and known polarity.
- **Criterion usage:** `ControlItem` is consumed only as a held-out anchor for polarity (and earmarked for later validation); it is never a candidate item.
- **Superseded:** `DevelTest.ipynb`, `Psy2-5_*.ipynb` `Item`/`Survey` prototypes (left in place, not imported).
- **Out of scope / non-goals:** item-rest consistency `C(S)`, the λ trade-off, the Monte Carlo search, multi-subscale designs, and adaptive/online (CAT-style) selection. This change delivers only the `H(S)`/`η(S)` measure and the data plumbing it needs.
