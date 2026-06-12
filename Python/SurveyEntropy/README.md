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
