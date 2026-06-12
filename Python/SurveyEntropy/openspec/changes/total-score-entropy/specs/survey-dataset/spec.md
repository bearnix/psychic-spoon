## ADDED Requirements

### Requirement: Load respondent-by-item response data
The system SHALL load survey response data from a CSV file into a structure that exposes a respondents × items numeric matrix together with per-item metadata. Non-response metadata columns (e.g. index, timestamp, demographic columns) SHALL NOT be treated as items.

#### Scenario: Load the pilot CSV
- **WHEN** the pilot file `sjalvskattning_data_clean.csv` is loaded
- **THEN** the result exposes one row per respondent and one column per item that survives item identification
- **AND** columns that are not survey items (index, timestamp, demographics) are excluded from the response matrix

#### Scenario: Empty or unreadable source
- **WHEN** the source file is missing or contains no respondent rows
- **THEN** loading fails with a clear error rather than returning a silently empty matrix

### Requirement: Hold out criterion and demographic columns as metadata
The system SHALL retain the construct criterion column and demographic columns as separate respondent-level metadata rather than discarding them, and SHALL NOT place them in the candidate item matrix. For the pilot, the criterion is the global self-rating `ControlItem` ("rate your own patience 1–10") and the demographics are `Sex` and `Age`. The criterion SHALL be retrievable for use by downstream polarity and validation steps.

#### Scenario: Criterion is held out, not pooled
- **WHEN** the pilot CSV is loaded
- **THEN** `ControlItem` is retrievable as the construct criterion (one value per respondent)
- **AND** `ControlItem` does not appear as a column in the candidate item matrix

#### Scenario: Demographics are retained as metadata
- **WHEN** the pilot CSV is loaded
- **THEN** `Sex` and `Age` are retrievable as respondent metadata
- **AND** they do not appear in the candidate item matrix

### Requirement: Identify valid Likert items and their scale
The system SHALL classify each candidate column as a valid Likert item only if all of its non-missing values are integers within a single contiguous integer scale `[lo_i, hi_i]`. Columns containing free-text or multi-select values (such as the social-media columns in the pilot file) SHALL be rejected as non-Likert and excluded from the response matrix. For each accepted item the system SHALL record its integer scale `[lo_i, hi_i]`.

#### Scenario: Accept a Likert column
- **WHEN** a column contains only integer values within a contiguous range (e.g. 1–5)
- **THEN** the column is accepted as an item
- **AND** its scale `[lo_i, hi_i]` is recorded

#### Scenario: Reject a free-text / multi-select column
- **WHEN** a column named like an item contains non-integer values (e.g. "Instagram;Facebook", "Inget")
- **THEN** the column is rejected as a non-Likert item and excluded from the response matrix

#### Scenario: Scale metadata is available per item
- **WHEN** the response matrix is exposed
- **THEN** each item's recorded scale `[lo_i, hi_i]` is retrievable so downstream code can compute the theoretical total-score support without inspecting raw data

### Requirement: Handle missing responses explicitly
The system SHALL represent missing responses explicitly and SHALL NOT silently coerce them to a valid scale value (e.g. zero). The chosen handling policy (such as dropping respondents with missing values within a working subset) SHALL be applied at total-score computation time, not hidden inside loading.

#### Scenario: Missing value is not coerced
- **WHEN** an item cell is blank for a respondent
- **THEN** that cell is represented as missing in the response matrix
- **AND** it is not counted as the lowest scale value
