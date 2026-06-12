# 01 — Framing, IRT parallels, and critique

Companion to [SurveysHistogram.md](SurveysHistogram.md). Compiled from the first round of scrutiny on the proposed Monte-Carlo / entropy-based survey design approach. Intended to be re-read before the next iteration.

## 1. Proposal as understood

From a candidate pool of Likert items (item *i* scored on `[0, N_i]`), select a subset *S* that simultaneously:

1. Makes the empirical distribution of total scores across respondents **as flat as possible** (high entropy `H(S) = −Σ p log p` on the total-score histogram), and
2. Keeps **item–total Spearman correlation** of each included item with the sum of the rest of *S* high (internal consistency).

Search method: Monte Carlo over subsets. Implementation aid: Python utilities for histograms of item responses and for adding histograms over `[0, N_i] + [0, N_j] → [0, N_i + N_j]`.

Pilot data: `sjalvskattning_data_clean` (Swedish self-assessment data already used in a course).

Initial scope: single construct. Multi-subscale design is explicitly deferred.

## 2. Critique of the proposal as stated

### 2.1 The two objectives are in genuine tension

Internal consistency means items co-vary strongly. Strong co-variation of additive components produces **peaked** total-score distributions (central-limit-ish, shifted by the correlation structure). Maximum entropy of total scores prefers items that are **less** mutually informative. So `H(S)` and `C(S)` (consistency) pull in opposite directions. This is not a fatal flaw — it is the trade-off the design *is*. But it should be made explicit in any objective function, ideally exposed as a tunable weight `λ` and reported as a Pareto front.

### 2.2 The histogram-convolution idea bakes in an independence assumption

The statement "extend addition of histograms over `[0, N_i]` and `[0, N_j]` to `[0, N_i + N_j]`" is only correct about the **support** (the set of achievable sums). The **distribution on that support** under convolution of marginal item-histograms equals the distribution of `X_i + X_j` *only if* `X_i ⊥ X_j`. In an internally consistent survey, items are correlated by construction — that is the whole point of measuring a shared construct. So convolving marginal histograms gives the wrong total-score distribution.

Practical consequence: for any candidate subset *S* on pilot data, compute the empirical total-score distribution by summing per respondent and binning the result. Do not iterate convolutions of marginal item-histograms.

### 2.3 Item–rest correlation is a moving target during selection

Item–rest correlation for item *i* is defined against the rest of *the currently included set*. Every time the set *S* changes, every remaining item's rest-score changes definition. Greedy forward/backward selection is therefore biased by selection order. Monte Carlo over subsets handles this cleanly at the cost of redundant computation; with `|pool| < a few hundred`, this is cheap.

### 2.4 Spearman vs. Pearson

Item–total correlations in classical test theory are usually Pearson or polyserial. The user's choice of Spearman is reasonable for ordinal Likert (monotone, not necessarily linear) but is a deliberate departure worth noting in any write-up.

## 3. A short IRT primer in physics language

Each respondent has a hidden coordinate **θ** ("latent trait", real-valued — think of it as an unobserved reaction coordinate). Each item has parameters describing how the probability of each response category depends on θ.

For ordinal Likert the standard model is the **Graded Response Model (Samejima)**: `P(X_i ≥ k | θ)` is a logistic function of θ with category-threshold locations.

The **Fisher information** of item *i* at θ, `I_i(θ)`, measures how sharply the conditional distribution of `X_i | θ` depends on θ — i.e. how much an observation of item *i* pins down θ locally. **Test information** is additive across items:

> `I(θ) = Σ_i I_i(θ)`

and its reciprocal is the squared standard error of the maximum-likelihood estimate θ̂. Optimal test design picks items so that `I(θ)` is roughly **flat and high** across the θ range of interest.

## 4. Parallels with the proposal

| Proposal | IRT counterpart |
|---|---|
| "Even signal over the whole range" | Flat Test Information Function `I(θ)` |
| "Different items resolve different parts of the scale" | Items with thresholds spread across θ |
| Item–total correlation (Spearman) | Discrimination parameter `a_i` (slope of P vs. θ) |
| Entropy of total scores on pilot data | Marginal, population-weighted shadow of `I(θ)` flatness |

Where they part ways:

- IRT **separates** *where* an item is informative (location) from *how much* (discrimination). The scalar entropy criterion conflates these.
- IRT commits to a **parametric** form for `P(X_i | θ)`. The empirical/entropy approach is non-parametric and does not assume any latent-variable model exists.

The intuition behind the proposal coincides with the most important design principle in IRT, arrived at from first principles. That is a positive sign for the framing.

## 5. Monte Carlo vs. existing IRT frameworks — clarification

These do not really compete:

- **MC is a search method** (over subsets of items).
- **IRT is a model** (of how responses depend on a latent trait).

You can run MC on an IRT-derived objective, and indeed Computerized Adaptive Testing (CAT) does something close to this online. The thing to choose carefully is the **objective function**, not the search procedure.

Two candidate objectives, both compatible with MC search:

1. **Empirical / CTT objective** (matches the original proposal): combination of `H(S)` and item–rest Spearman, computed directly on the pilot data. No model, no latent θ.
2. **IRT objective**: flatness of `I(θ)` on a chosen θ grid. Requires fitting a Graded Response Model first (e.g. `mirt` in R, or `girth` / `py-irt` in Python).

Feasibility: with at most a few hundred candidate items, the subset space `2^N` is small by molecular-simulation standards. Metropolis MC with single-item swap moves and a cheap objective (histogram + rank correlation) will converge fast. The user's intuition that MC is suitable here is correct.

## 6. Why this direction is worthwhile

1. **The intuition is right.** The proposal is a CTT-flavoured cousin of IRT optimal test design, arrived at independently. The framing is sound.
2. **Transparency.** Applied researchers often experience IRT as a black box. "We picked items so the total-score histogram is flat and items still hang together" is communicable in one sentence. Useful pedagogically and in applied collaborations.
3. **No parametric commitment.** The empirical approach does not require fitting a logistic model, does not assume a latent normal θ, and does not depend on model convergence. For exploratory and teaching use this is a feature.
4. **MC makes the trade-off legible.** Sweeping `λ` between `H(S)` and `C(S)` produces a Pareto front. That front *is* a result — it visualises the price of demanding internal consistency.
5. **Composable with IRT later.** A working MC pipeline on the empirical objective swaps to an IRT-based objective with a one-function change. The decision can be deferred.

## 7. Suggested phased framing

### Phase 1 — Empirical / CTT, Monte Carlo, on the pilot data

- Scope: single construct.
- Candidate pool: items in `sjalvskattning_data_clean`.
- For each subset *S*: compute
  - `H(S)` = entropy of the empirical total-score histogram on the pilot respondents,
  - `C(S)` = mean (or min) item–rest Spearman correlation.
- Combined objective with tunable weight `λ`; report the Pareto front over a sweep of `λ`.
- Metropolis MC with item-swap moves.
- Output: family of "good" subsets along the trade-off front, characterised by `(|S|, H(S), C(S))`.

### Phase 2 (optional, later) — IRT comparison

- Fit a Graded Response Model to the same pilot data.
- Inspect item parameters (location, discrimination).
- Check whether MC-selected items correspond to high-discrimination items with thresholds spread across θ. Agreement validates the empirical approach; disagreement is itself informative.

### Out of scope for now

- Multi-subscale / multi-construct surveys.
- Adaptive / online item selection (CAT-style).

## 8. Open questions to revisit

1. Should `C(S)` be **mean** or **min** item–rest Spearman? Min is more conservative (no weak items allowed); mean tolerates a few weak items if the average is high. Choice affects which subsets win.
2. Is the entropy of the total-score distribution the right entropy? Alternatives:
   - Sum of per-item response entropies (rewards items individually using their full scale).
   - Entropy of the joint response distribution (intractable for large *S*; conceptually closest to "information content of the survey").
3. How to handle items with different `N_i`? Should they be normalised, or does using the raw sum on heterogeneous ranges produce useful bandwidth?
4. Population dependence. The empirical total-score histogram depends on the pilot population. A subset that looks "flat" on this population may not be flat on another. IRT's `I(θ)` is population-free in that sense. Worth keeping in mind as a limitation of Phase 1.
5. Validation. Is there a hold-out / cross-validation strategy that makes sense here? (E.g. select on half the respondents, evaluate `H` and `C` on the other half.)

## 9. References worth checking before serious implementation

- Samejima's Graded Response Model (original IRT model for ordinal Likert).
- `mirt` (R) — reference implementation, widely used.
- `girth`, `py-irt` (Python) — leaner alternatives.
- Literature on **maximum-entropy test construction** and **optimal test design** in psychometrics (the latter has a substantial older literature).

## 10. Prior art — what is already in the project folder

Survey of the PDFs in the SurveyEntropy root, ordered by relevance to this project.

### 10.1 Orsoni, Benassi & Scutari (2025) — *Psychological Methods* — most directly comparable

Modern, peer-reviewed, with open code (OSF). Pipeline:

1. **Item ranking** by **Jensen–Shannon divergence distance (JSDd)** between the two groups' response distributions on each item.
2. **Iterative pruning**: drop the bottom 5 % of items by JSDd, repeat, evaluate the surviving subset with ML classifiers (CART / Random Forest / SVM) on a held-out test set.
3. **Structure learning** of item–item conditional dependencies via **Bayesian Networks** (PC-Stable, tabu-search), positioned as an alternative to factor analysis / SEM.
4. Real-data demonstration on the Test of Manifest Anxiety Scale (50 items, split at the 80th percentile).

**Key distinction from this project.** Their approach is **supervised** — known group labels (high vs low anxiety) drive item ranking. The framing in [SurveysHistogram.md](SurveysHistogram.md) is **unsupervised** — flatness of the total-score histogram and item-rest consistency, no group labels. The toolset (JSD, BN, ML validation) is reusable; the objective is genuinely different.

Sits in the broader **"network psychometrics"** tradition (Borsboom, Fried, McNally) that treats constructs as emergent properties of item networks rather than reflections of latent traits.

### 10.2 Brockett, Haaland & Levine (1981) — *IEEE Trans. Information Theory* — foundational ancestor

The originating paper for the information-theoretic-item-selection family. Cited by Orsoni 2025.

- **D-value** of a question: `D = (n/2) · Σ (p_i − q_i) ln(p_i / q_i)` — empirical KL/J-divergence between high-scorers (Q4) and low-scorers (Q1), where the quartile assignment uses total score *excluding* the question being assessed (the item-rest trick, predating its widespread use).
- **Sequential selection**: pick the first question by minimum p-value of D; add subsequent questions by maximum *additional* divergence given items already in.
- **DIG** (Discrimination using Information Gain): score each response by `ln(p_ti / q_ti)`, sum to get a per-respondent classifier score. Outperforms Fisher's LDF when items are non-ordinal.
- Real applications: Iranian psychiatric screening (46 → 22 items with zero apparent error), PAHO child-mortality survey, WHO contraceptive acceptability study.

Relevance: closest historical analogue to the proposed MC + information criterion approach. Worth reading in full.

### 10.3 Paninski (2003) — *NIPS* — asymptotic theory for information-maximization

Bayesian adaptive design. On each trial pick the next stimulus *x* to maximize `I(y; θ | x)`. Proves a Bernstein–von Mises theorem: under smoothness + identifiability + compactness, posteriors are consistent and asymptotically normal, with variance `(N · max_x I_θ(x))⁻¹` instead of the i.i.d. rate `(N · ⟨I_θ(x)⟩)⁻¹` — **max** beats **average** whenever Fisher information is non-constant in *x*.

Side results worth knowing:

- Exactly one psychometric function makes i.i.d. sampling match adaptive: `f*(t) = (sin(c·t) + 1)/2` on `[−π/2c, π/2c]`. For all others, adaptive strictly wins.
- A negative example where information-maximization fails: if expected information from one coordinate of `θ` stays bounded above information from another (e.g. piecewise-constant likelihoods), the algorithm fixates and never learns the other coordinate. Useful cautionary tale for greedy entropy-maximizing search.

Relevance: theoretical underpinning for the max-information school. Indirect for this project because the setting is online/adaptive, not offline subset selection from a finite pool, but the math is transferable and the "max vs average" intuition is the same.

### 10.4 Golden, Brockett & Zimmer (1990) — *Multivariate Behavioral Research* — multivariate info-theoretic toolkit

Extends the Brockett line to redundancy and asymmetry among variables. Defines univariate / bivariate / trivariate entropies, conditional entropies, mutual information, "percent of information" `= 100 · I(Y|X)/H(Y)`, and significance via `2nI ~ χ²` with `(k_X−1)(k_Y−1)` df.

Relevance: provides the vocabulary and a significance test if you want to replace item-rest Spearman with an **information-theoretic association measure** (mutual information between an item and the rest-score). Symmetric construct case doesn't need the asymmetry machinery, but it's there if needed later.

### 10.5 Duncan (1975) — *Operations Research* — branching questionnaires (out of scope but adjacent)

Tree-structured *adaptive* questionnaires: sequential questioning where each question partitions the remaining state space, optimized to identify the true state with minimum average cost. Dynamic-programming / shortest-route formulation; combinatorics linked to Catalan numbers. Shannon entropy of the prior bounds the optimal average charge from below; a Huffman-style construction achieves the bound + 1 in the homogeneous case.

Relevance: explicitly **out of scope** for this project (you've committed to a fixed, non-branching questionnaire). Included here for completeness — it's the other major branch of information-theory-in-questionnaires.

### 10.6 Linder & Kromhout (1993) — *J. Mathematical Chemistry* — not about surveys

Statistical mechanics of nematic liquid crystals: Gibbs/Helmholtz free energy as functionals of the single-particle distribution `ρ(x)`, perturbative expansion of correlation functions of the ordered phase around the disordered reference.

Why it might be in this folder anyway. There is a structural analogy worth naming explicitly: equilibrium minimizes `A = U − TS`, i.e. trades internal energy against entropy. The proposed survey objective `F(S) = −H(S) + λ · (1 − C(S))` has the same shape — entropy against a coupling/consistency term, with `λ` playing the role of inverse temperature. Treating Phase 1 as a free-energy minimization with Metropolis MC is the stat-mech translation of the design problem. If that mapping was the private inspiration for the project, this paper belongs in the bibliography as a *methodological* analogue, not a content reference. If it's a leftover from another project, ignore.

### 10.7 Lineage summary

```
                    Brockett, Haaland & Levine (1981)
                                |
              ┌─────────────────┴─────────────────┐
              ↓                                   ↓
   Golden, Brockett & Zimmer (1990)        Goldstein & Dillon (1978)
   (multivariate redundancy)                (discrete discriminant analysis)
              |                                   |
              └─────────────┬─────────────────────┘
                            ↓
                  Orsoni, Benassi & Scutari (2025)
                  (JSD + ML + Bayesian Networks)

  Parallel adaptive / online branch:
   Duncan (1975) ──→ Watson & Pelli (1983, QUEST) ──→ Paninski (2003)
```

All of this thread is **supervised** (known groups, or known target parameter). The unsupervised "flatness + consistency" framing of this project sits next to the thread but is not within it.

## 11. Suggested follow-up references to investigate

Pulled from the bibliographies of the PDFs above. Tiered by likely value to this project.

### Tier 1 — read first

1. **Wang, Song, Wang, Gao & Xiong (2020).** *A note on the relationship of the Shannon entropy procedure and the Jensen–Shannon divergence in cognitive diagnostic computerized adaptive testing.* SAGE Open, 10(1). Cited by Orsoni 2025. Directly connects entropy-based item selection to JSD in an adaptive-testing setting.
2. **Borsboom, D. (2017).** *A network theory of mental disorders.* World Psychiatry 16(1), 5–13. The manifesto for the network framework — the alternative to latent-trait psychometrics that the unsupervised framing of this project most naturally sits within.
3. **Epskamp, Rhemtulla & Borsboom (2017).** *Generalized network psychometrics: Combining network and latent variable models.* Psychometrika 82(4), 904–927. Bridges the two paradigms — directly relevant for the Phase 1/Phase 2 design.
4. **Watson & Pelli (1983).** *QUEST: a Bayesian adaptive psychophysical method.* Perception and Psychophysics 33, 113–120. The classic adaptive-testing reference. Read alongside **Kontsevich & Tyler (1999)** *Bayesian adaptive estimation of psychometric slope and threshold,* Vision Research 39, which adds joint slope+threshold estimation.
5. **Hambleton & Cook (1977).** *Latent trait models and their use in the analysis of educational test data.* Journal of Educational Measurement 14, 75–96. Cited by Brockett 1981 as the IRT reference of the era. A modern textbook (e.g. de Ayala, *Theory and Practice of IRT*) would be a more efficient way in — the Hambleton & Cook paper is mainly here for context.

### Tier 2 — useful once Phase 1 is concrete

6. **Briganti, Scutari & McNally (2023).** *A tutorial on Bayesian networks for psychopathology researchers.* Psychological Methods 28(4), 947–961. Companion to Orsoni 2025; how to actually fit BNs to psychometric data.
7. **Rosellini & Brown (2021).** *Developing and validating clinical questionnaires.* Annual Review of Clinical Psychology 17, 55–81. Modern overview of the questionnaire-validation landscape — sets the baseline against which an unsupervised entropy-based method should justify itself.
8. **Kullback, S. (1959).** *Information Theory and Statistics.* Wiley / Dover. The source for the divergence measures used by every paper in this folder. Good to have on the shelf rather than read cover to cover.
9. **Lin, J. (1991).** *Divergence measures based on the Shannon entropy.* IEEE Trans. Information Theory 37(1), 145–151. The original treatment of Jensen–Shannon divergence and its metric properties — relevant if you adopt JSD-based item ranking from Orsoni 2025.
10. **Gokhale & Kullback (1978).** *The Information in Contingency Tables.* Marcel Dekker. The technical reference for handling categorical/ordinal items with information-theoretic methods (chi-squared limits, zero-marginal handling).

### Tier 3 — adjacent / historical context

11. **Goldstein & Dillon (1978).** *Discrete Discriminant Analysis.* Wiley. The CTT-side companion to the IRT literature for binary/categorical items.
12. **Theil & Fiebig (1984).** *Exploiting Continuity: Maximum Entropy Estimation of Continuous Distributions.* Ballinger. Max-entropy methods generalized — worth a glance if the unsupervised flatness criterion is the project's spine.
13. **Berger, Bernardo & Mendoza (1989).** *On priors that maximize expected information.* Bayesian Statistics 4, Oxford University Press, 35–60. Foundational reference for the Bayesian-design school cited by Paninski.

### Tier 4 — probably skip unless going deep

14. **Picard, C. F. (1965, 1972).** *Théorie des Questionnaires* / *Graphes et Questionnaires.* Gauthier-Villars, Paris. The branching-questionnaire literature. Out of scope for this project.
15. **Csiszár & Körner (forthcoming at time of Brockett 1981).** *Information Theory: Coding Theorems for Discrete Memoryless Systems.* Cited heavily by Brockett 1981; mostly relevant if dipping into information-theoretic asymptotics.

### Outside the folder but probably worth adding

- **Samejima, F. (1969).** *Estimation of latent ability using a response pattern of graded scores.* Psychometrika Monograph 17. The Graded Response Model paper itself.
- **van der Linden, W. (Ed., 2016).** *Handbook of Item Response Theory.* CRC Press, 3 volumes. The modern IRT reference, covers optimal test design and the Test Information Function explicitly.
- **Chalmers, R. P. (2012).** *mirt: A multidimensional item response theory package for the R environment.* Journal of Statistical Software 48(6). The `mirt` reference paper.
