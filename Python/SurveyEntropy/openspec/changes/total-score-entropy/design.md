## Context

This is the first real code in SurveyEntropy. The objective at the heart of the project is the entropy of the **total-score distribution** for a subset of Likert items, `H(S) = −Σ p ln p`. Everything downstream — the consistency term `C(S)`, the `F(S) = −H + λ(1−C)` trade-off, and the Monte Carlo search — depends on this measure being trustworthy.

Current state: only superseded notebook prototypes exist, and the one entropy they compute (`Σ_i H(X_i)`, sum of per-item entropies) is the *wrong object* — it is blind to inter-item correlation and so cannot express the H-vs-consistency tension. Pilot data is `sjalvskattning_data_clean.csv`: 51 respondents, single construct (**patience/impatience**), Likert 1–5. Per `sjalvskattning_keys.csv` the columns are a timestamp, a `ControlItem` global self-rating ("rate your own patience 1–10"), `Sex`, `Age`, then `Item1`–`Item41`. `Item40` is a multi-select social-media column (non-Likert, rejected). The battery is **mixed-keyed** — some items worded toward patience, some toward impatience — so a raw sum lets the directions cancel and artificially flattens the construct signal.

Two constraints dominate the design, both consequences of small `N`:
- With ~51 respondents and a `k`-item subset over scale 1–5, the total-score support is `4k+1` values; by `k≈12` there is ~1 respondent per bin. The plug-in entropy estimator is then noise-dominated and **biased downward** by ~`(bins−1)/(2N)`.
- That bias *varies with subset size*, so it directly corrupts cross-subset comparison — the operation the eventual search performs millions of times.

Physics framing (for the author): this is the small-sample entropy-estimation problem familiar from computing configurational entropy of a coarse-grained coordinate from a short trajectory — undersampled bins systematically under-count entropy, and the bias scales with grid fineness.

## Goals / Non-Goals

**Goals:**
- A `survey-dataset` module that loads the response matrix, rejects non-Likert columns, records each item's integer scale, and holds out the construct criterion (`ControlItem`) and demographics as metadata.
- An `item-polarity` module that estimates each item's scoring direction from its correlation with the criterion and produces a sign-corrected response matrix.
- A `total-score-entropy` module that computes the total-score distribution (by summation), a bias-corrected entropy estimate, and a size-comparable efficiency `η(S) ∈ [0,1]`.
- A swappable entropy-estimator interface (Miller–Madow now; NSB/Bayesian later).
- A uv-managed project (`pyproject.toml` + `uv.lock`) with a `src/` package and tests, including known-entropy synthetic checks.

**Non-Goals:**
- Item-rest consistency `C(S)`, the λ trade-off, and the Monte Carlo search (separate later changes).
- Multi-subscale designs and adaptive/online (CAT) selection.
- Choosing a *final* estimator or bin-width policy — the design only commits to making them swappable and exposed. The empirical comparison that picks defaults is itself a task here, not a prerequisite.

## Decisions

**D1 — Efficiency `η = H/H_max` as the primary reported number, not raw `H`.**
Raw `H` lives on a support that grows with subset size, so it is not comparable across subsets. `η = H / ln(occupied bins) ∈ [0,1]` normalizes that out and is already bounded for later mixing into `F = −H + λ(1−C)`. Raw `H` and `H_max` remain available for inspection. *Alternative considered:* fixing `|S|` to keep supports equal — rejected because the search must compare subsets of different sizes.

**D2 — Miller–Madow as the default bias correction, behind a `EntropyEstimator` interface.**
Miller–Madow adds `(K̂−1)/(2N)` (with `K̂` the number of occupied bins) to the plug-in estimate — one line, no tuning, strictly better than plug-in at this `N`. The interface keeps plug-in available for comparison and lets NSB/Bayesian estimators drop in later without touching callers. *Alternatives considered:* plug-in only (rejected: biased exactly where it hurts); jumping straight to NSB (rejected: more dependency and complexity than the first measure warrants, but explicitly left as a swap-in).

**D3 — Total scores by per-respondent summation; bin width is a parameter.**
Sum each respondent's responses over `S` and histogram the result. Never convolve marginal item histograms — that bakes in independence the design violates. Bin width defaults to 1 (one bin per integer total) but is exposed, because coarse-graining is the main lever against sparsity and we want to study its effect rather than hard-code it.

**D4 — Support from item scales, not from observed values.**
The histogram support is the theoretical `[Σ lo_i, Σ hi_i]` derived from per-item scales, so the measure is a property of the survey design and population, not an artifact of which scores happened to occur in a small sample. `H_max` for `η` uses occupied bins (so `η=1` is achievable in-sample), while the support framing keeps subsets comparable.

**D5 — Listwise deletion on the working subset; report contributing N.**
A respondent missing any item in `S` is dropped for that `S`, and the contributing count is returned with the result so the caller can see how thin the estimate is. Missing values are represented explicitly at load time and never coerced to a scale value. *Alternative considered:* imputation — deferred; it changes the distribution and deserves its own decision.

**D6 — uv + `src/` package, no notebook code.**
`pyproject.toml` + `uv.lock`, run via `uv run`. The capabilities become separate modules so the objective function stays decoupled from data handling, polarity, and the future search, matching the project rule that the objective must be swappable without touching search machinery.

**D7 — Criterion-based item polarity, not wording-based.**
Each item's scoring direction is estimated from the sign of its Spearman correlation with the held-out `ControlItem` self-rating; reverse-keyed items are reflected within scale (`x → (lo+hi)−x`). This keeps the project unsupervised — the data, anchored on the criterion, decides direction — rather than importing a hand-coded key from item wording. The polarity step sits between `survey-dataset` and `total-score-entropy`: it consumes the criterion and emits a sign-corrected matrix, and `total-score-entropy` stays agnostic to how the matrix was scored (it works on raw or corrected input). *Alternatives considered:* wording-based keying (rejected — a manual judgment call on 41 Swedish items, and counter to the unsupervised framing); deferring keying to raw sums (rejected for the pilot run because mixed-keying makes raw-sum `H(S)` uninterpretable — but raw `H` remains computable for comparison). Reflection within scale (rather than negation) is chosen so recoded values stay on the original integer support, keeping the total-score support well defined.

## Risks / Trade-offs

- **Miller–Madow is still biased at `k≈12`, N≈51.** → Keep the estimator swappable (D2) and include a synthetic small-N task that measures residual bias of plug-in vs Miller–Madow, so we know how far to trust it before relying on it in search.
- **`η` can hide how few respondents back a value.** → Always return contributing N and `H_max`/occupied-bin count alongside `η`, never `η` alone.
- **Population dependence.** `H(S)` is a property of this pilot population; a "flat" subset may not generalize. → Out of scope to solve here, but documented as a known limitation; a hold-out / cross-validation story is deferred to a later change.
- **Coarse-graining changes the answer.** Wider bins raise apparent flatness. → Bin width is explicit and reported with every result; no silent default beyond width 1.
- **Criterion-based polarity is noisy at N≈51.** A near-zero item–criterion correlation has an unstable sign, so a confident flip could be wrong. → Flag borderline items (correlation below a documented threshold / not significant) and report every item's correlation rather than silently flipping; keep the raw matrix and polarity available so scoring can be reviewed or overridden.
- **The criterion is itself a single self-report.** `ControlItem` may be biased or noisy, so anchoring polarity on it inherits that noise. → Acceptable as the unsupervised anchor for Phase 1 and documented as such; the criterion is also earmarked for later external validation, where its limitations get revisited.

## Open Questions

- Final entropy estimator: is Miller–Madow enough for the search, or do we need NSB? (Resolved empirically by the synthetic small-N task in this change; the *decision* may still be deferred.)
- Bin-width policy: fixed width 1, or adaptive to keep bins ≪ N? (Left exposed here; policy chosen in a later change once the search exists to evaluate it.)
- Heterogeneous item scales (mixing different `N_i`, e.g. combining the 1–5 pilot with the 0/1 `prestation` data): raw sum vs per-item normalization. Pilot is uniform 1–5, so deferred.
