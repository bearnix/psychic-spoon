# Toy example — three binary items, uniform latent trait

Companion to [SurveysHistogram.md](SurveysHistogram.md) and [01_Framing_IRT_and_Critique.md](01_Framing_IRT_and_Critique.md). Sketches the entropy-vs-consistency trade-off in closed form on the smallest non-trivial case.

## 1. Model

Hidden θ ~ Uniform[0, 1]. Three binary items with thresholds τ₁ ≤ τ₂ ≤ τ₃:

> X_i = 1 if θ > τ_i, else 0

This is the simplest IRT-style construction — each item is a step function of the latent trait. Total score S = X₁ + X₂ + X₃ takes values in {0, 1, 2, 3}.

## 2. Closed-form marginals and covariances

These follow directly from the uniformity of θ:

- P(X_i = 1) = 1 − τ_i
- P(X_i = 1, X_j = 1) = P(θ > max(τ_i, τ_j)) = 1 − max(τ_i, τ_j)
- cov(X_i, X_j) = (1 − max(τ_i, τ_j)) − (1 − τ_i)(1 − τ_j)
- var(X_i) = τ_i(1 − τ_i)

## 3. Total-score distribution

Order θ against the thresholds:

> P(S = k) = τ_{k+1} − τ_k

with τ_0 = 0 and τ_4 = 1. The histogram of S over {0, 1, 2, 3} is just the four gaps between consecutive thresholds (including the two endpoints).

## 4. One-parameter family

Parametrize with a single spread `a ∈ [0, 0.5]`:

> τ = (0.5 − a, 0.5, 0.5 + a)

- `a = 0`: all thresholds at 0.5. Items are identical. S ∈ {0, 3} each with prob 0.5. Max consistency, low entropy.
- `a = 0.25`: thresholds at (0.25, 0.5, 0.75). Equal gaps. S ~ Uniform on {0,1,2,3}. Max entropy.
- `a = 0.5`: thresholds at (0, 0.5, 1). Two items become degenerate.

## 5. Computed objectives

H(S) is the entropy of the gap-histogram. C(S) is the mean item-rest correlation (Pearson, since items are binary):

| a    | P(S=0,1,2,3)            | H(S)  | mean item-rest ρ |
|------|-------------------------|-------|------------------|
| 0.00 | (0.5, 0.0, 0.0, 0.5)    | 0.693 | 1.000            |
| 0.10 | (0.4, 0.1, 0.1, 0.4)    | 1.194 | 0.816            |
| 0.20 | (0.3, 0.2, 0.2, 0.3)    | 1.366 | 0.671            |
| 0.25 | (0.25, 0.25, 0.25, 0.25)| 1.386 | 0.577            |
| 0.30 | (0.2, 0.3, 0.3, 0.2)    | 1.366 | 0.500            |
| 0.40 | (0.1, 0.4, 0.4, 0.1)    | 1.194 | 0.301            |
| 0.50 | (0.0, 0.5, 0.5, 0.0)    | 0.693 | 0.000            |

Entropies in nats. Item-rest correlations computed from the closed-form covariances in §2. Symmetry around `a = 0.25` in the histogram shape (and therefore in H) is exact; in ρ it is not.

## 6. What the table shows

1. **The trade-off is real but not symmetric.** Sweeping `a` from 0 to 0.25, H rises monotonically (0.693 → 1.386) while item-rest correlation falls monotonically (1.0 → 0.58). This is the regime where the two objectives compete.

2. **There is a regime where the trade-off disappears — both decline together.** For `a > 0.25`, H falls *and* ρ falls. Pushing items past the uniform-spacing point makes the test simultaneously less informative and less internally consistent. The right tail of the parameter sweep is dominated; no point there is on the Pareto front.

3. **The Pareto front in this family is the segment `a ∈ [0, 0.25]`.** Endpoints:
   - `a = 0`: max consistency (ρ = 1), minimum entropy among Pareto points. The "redundant items" extreme.
   - `a = 0.25`: max entropy, minimum consistency among Pareto points. The "spread items" extreme.

4. **The intuition behind the proposal lands at `a = 0.25`.** Uniformly spaced thresholds give the flat total-score distribution. This is also exactly what IRT optimal test design recommends — flat Test Information Function across θ — so the two framings agree on the toy.

## 7. The free-energy reading

Define

> F(a; λ) = − H(S; a) + λ · (1 − ρ(a))

with λ ≥ 0 the inverse temperature on the consistency constraint. Minimize F over a:

- λ = 0: pure entropy maximization. Optimum at `a = 0.25`.
- λ → ∞: pure consistency maximization. Optimum at `a = 0`.
- Intermediate λ: optimum slides along the Pareto front.

Sweeping λ traces the entire interesting curve. This is what the Phase-1 MC would discover empirically, with the search space being subsets-of-items rather than a single continuous parameter.

## 8. Caveats specific to this toy

- **Binary items.** Likert items (0..N_i) have richer per-item entropies and the trade-off is quantitatively different, but qualitatively the same.
- **Single latent θ.** With multiple constructs, item-rest correlation within a subscale is the right consistency measure and the trade-off becomes per-subscale.
- **Deterministic thresholds, no measurement noise.** The Graded Response Model is the logistic-smoothed version; the trade-off remains, with softer edges.
- **Continuous parameter, not subset selection.** The real problem is combinatorial — pick a subset of items from a fixed pool. The continuous sweep here is a stand-in to make the trade-off visible analytically. The MC search over subsets will trace a Pareto front in the same shape, with more structure.

## 9. Takeaway

The trade-off **bites only in the under-spread regime**. Once items are too spread, both objectives collapse together — over-spreading is strictly worse and the Pareto front cleanly excludes it. So the MC search should naturally concentrate around configurations where item locations cover the trait range without going past it, which is exactly the optimal-test-design ballpark. The interesting tuning happens between the redundant-items limit and the uniform-spacing point; everything beyond the uniform point is dominated.
