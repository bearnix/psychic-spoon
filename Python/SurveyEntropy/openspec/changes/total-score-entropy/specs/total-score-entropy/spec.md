## ADDED Requirements

### Requirement: Compute total scores by per-respondent summation
For a given item subset `S`, the system SHALL compute each respondent's total score as the sum of that respondent's responses across the items in `S`. The system SHALL NOT compute the total-score distribution by convolving per-item marginal histograms, because convolution assumes inter-item independence that the design deliberately violates.

#### Scenario: Total score is a per-respondent row sum
- **WHEN** a subset `S` of items and the response matrix are provided
- **THEN** each respondent's total score equals the sum of that respondent's responses over the items in `S`

#### Scenario: Respondents with missing responses in the subset
- **WHEN** a respondent has a missing response for any item in `S`
- **THEN** that respondent is excluded from the total-score distribution for `S` (listwise on the subset)
- **AND** the number of respondents actually contributing is reported alongside the result

### Requirement: Build the total-score distribution over a defined support
The system SHALL bin total scores into a histogram whose support is derived from the per-item scales of `S` (theoretical support `[Σ lo_i, Σ hi_i]`), and SHALL normalize it to a probability distribution. The bin width SHALL be a parameter so that scores can be coarse-grained to combat sparsity, defaulting to one bin per integer total.

#### Scenario: Default integer binning
- **WHEN** the distribution is requested with default settings
- **THEN** there is one bin per integer value across the theoretical support `[Σ lo_i, Σ hi_i]`
- **AND** the binned counts sum to the number of contributing respondents and the probabilities sum to 1

#### Scenario: Coarse-grained binning
- **WHEN** a bin width greater than 1 is requested
- **THEN** total scores are grouped into wider bins spanning the support
- **AND** the resulting distribution still normalizes to 1

### Requirement: Estimate entropy with a bias correction
The system SHALL estimate the Shannon entropy `H(S) = −Σ p ln p` of the total-score distribution using a finite-sample bias correction, defaulting to the Miller–Madow correction. The entropy estimator SHALL be swappable through a common interface so that alternative estimators (e.g. NSB / Bayesian) can replace the default without changing calling code. The plug-in (uncorrected) estimator SHALL remain available for comparison.

#### Scenario: Default estimator is bias-corrected
- **WHEN** entropy is requested with default settings
- **THEN** the returned value uses the Miller–Madow correction, not the raw plug-in estimate

#### Scenario: Known-entropy correctness
- **WHEN** entropy is computed on a synthetic distribution with a known analytic value (e.g. a uniform distribution over `m` bins, entropy `ln m`)
- **THEN** the estimate matches the known value within a documented tolerance as sample size grows

#### Scenario: Estimator is swappable
- **WHEN** a different entropy estimator is supplied through the interface
- **THEN** the total-score-entropy computation uses it without other code changes

### Requirement: Report a size-comparable flatness efficiency
The system SHALL report a flatness efficiency `η(S) = H(S) / H_max ∈ [0, 1]`, where `H_max` is the maximum entropy achievable on the distribution's occupied support (a uniform distribution). `η` makes the measure comparable across subsets of different sizes and bounds it for later mixing into a combined objective.

#### Scenario: Efficiency bounds
- **WHEN** all respondents share a single total score (a spike)
- **THEN** `η(S)` is 0

#### Scenario: Flat distribution
- **WHEN** the total-score distribution is uniform over its support
- **THEN** `η(S)` is 1 (within estimator tolerance)

#### Scenario: Comparable across subset sizes
- **WHEN** `η` is computed for subsets of different sizes
- **THEN** the values lie on the same `[0, 1]` scale regardless of how wide each subset's support is
