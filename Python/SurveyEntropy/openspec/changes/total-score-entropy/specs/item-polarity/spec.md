## ADDED Requirements

### Requirement: Estimate item scoring direction from the criterion
The system SHALL estimate each item's scoring direction (polarity) from the sign of its rank correlation (Spearman) with the held-out construct criterion, computed over respondents with both values present. An item whose responses increase with the criterion is forward-keyed (+1); an item whose responses decrease with the criterion is reverse-keyed (−1). Polarity SHALL be data-driven from the criterion, not assigned from item wording.

#### Scenario: Forward-keyed item
- **WHEN** an item's responses correlate positively with the criterion
- **THEN** its estimated polarity is +1

#### Scenario: Reverse-keyed item
- **WHEN** an item's responses correlate negatively with the criterion
- **THEN** its estimated polarity is −1

#### Scenario: Per-item correlation is reported
- **WHEN** polarity is estimated
- **THEN** each item's criterion correlation value is retrievable alongside its estimated polarity

### Requirement: Flag borderline items rather than silently flipping
The system SHALL flag items whose criterion correlation is near zero or not statistically distinguishable from zero (below a documented threshold) as borderline, because their estimated sign is unstable at small N. Borderline items SHALL be reported so the author can review them; the system SHALL NOT hide a near-zero flip as if it were a confident decision.

#### Scenario: Borderline item is flagged
- **WHEN** an item's criterion correlation magnitude is below the configured threshold
- **THEN** the item is reported as borderline with its correlation value
- **AND** the threshold used is part of the reported result

### Requirement: Produce a sign-corrected response matrix
The system SHALL produce a response matrix in which reverse-keyed items have been recoded to the same direction as forward-keyed items, using a scale-preserving reflection `x → (lo_i + hi_i) − x` so the recoded values stay within each item's original integer scale `[lo_i, hi_i]`. The original (raw) response matrix and the per-item polarity SHALL remain available so scoring can be inspected or undone.

#### Scenario: Reverse-keyed item is reflected within its scale
- **WHEN** an item on scale 1–5 is reverse-keyed and a respondent answered 1
- **THEN** the sign-corrected value is 5 (and a 5 becomes 1)
- **AND** all sign-corrected values remain within `[lo_i, hi_i]`

#### Scenario: Forward-keyed item is unchanged
- **WHEN** an item is forward-keyed
- **THEN** its sign-corrected values equal its raw values

#### Scenario: Raw matrix and polarity remain available
- **WHEN** the sign-corrected matrix is produced
- **THEN** the raw response matrix and the per-item polarity are both still retrievable
