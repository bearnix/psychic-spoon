"""Small-N characterization of total-score entropy estimators (task 6.1).

Question: at the pilot's sample size (N~51) and Likert 1-5, how badly is the
total-score entropy biased, and does the Miller-Madow correction fix enough of
it to trust the measure before the Monte Carlo search relies on it?

Method: a latent-trait generative model gives correlated items with a *known*
population total-score distribution (estimated from a very large sample). For a
range of subset sizes k we draw many N=51 samples and compare the plug-in and
Miller-Madow estimates against that ground truth. Bias = E[estimate] - truth
(negative means underestimate).

Run: ``uv run python studies/small_n_estimator_bias.py``. Writes a results table
to ``studies/small_n_estimator_bias.md`` (and a PNG if matplotlib is installed).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from surveyentropy.entropy import MILLER_MADOW, PLUG_IN

HERE = Path(__file__).resolve().parent

N_PILOT = 51
N_BIG = 400_000
REPLICATES = 400
SUBSET_SIZES = [2, 4, 6, 8, 10, 12, 16, 20]
DISCRIMINATION = 1.0
ITEM_NOISE = 0.8
SEED = 20260613


def simulate_totals(k: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """Total scores for ``n`` respondents on ``k`` correlated 1-5 items.

    Each respondent has a latent trait theta; every item is a noisy, rounded
    linear readout of theta, so items share variance (internal consistency) and
    the total score is peaked rather than flat -- the realistic hard case.
    """
    theta = rng.standard_normal(n)
    noise = rng.standard_normal((n, k)) * ITEM_NOISE
    x = np.rint(3.0 + DISCRIMINATION * theta[:, None] + noise)
    x = np.clip(x, 1, 5).astype(int)
    return x.sum(axis=1)


def counts(totals: np.ndarray, k: int) -> np.ndarray:
    """Histogram totals over the theoretical support [k, 5k]."""
    return np.bincount(totals - k, minlength=4 * k + 1).astype(float)


def run() -> list[dict]:
    rng = np.random.default_rng(SEED)
    rows = []
    for k in SUBSET_SIZES:
        truth = PLUG_IN(counts(simulate_totals(k, N_BIG, rng), k))
        plugin = np.empty(REPLICATES)
        miller = np.empty(REPLICATES)
        for r in range(REPLICATES):
            c = counts(simulate_totals(k, N_PILOT, rng), k)
            plugin[r] = PLUG_IN(c)
            miller[r] = MILLER_MADOW(c)
        rows.append(
            {
                "k": k,
                "support": 4 * k + 1,
                "truth": truth,
                "plugin_bias": plugin.mean() - truth,
                "miller_bias": miller.mean() - truth,
                "miller_sd": miller.std(),
            }
        )
    return rows


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "# Small-N total-score entropy estimator bias",
        "",
        f"Generative model: latent-trait, {DISCRIMINATION=}, {ITEM_NOISE=}; "
        f"N={N_PILOT}, {REPLICATES} replicates; truth from N={N_BIG:,}.",
        "All entropies in nats. Bias = E[estimate] - truth.",
        "",
        "| k | support (bins) | truth H | plug-in bias | Miller-Madow bias | MM sd |",
        "|---|----------------|---------|--------------|-------------------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['k']} | {r['support']} | {r['truth']:.3f} | "
            f"{r['plugin_bias']:+.3f} | {r['miller_bias']:+.3f} | {r['miller_sd']:.3f} |"
        )
    lines += [
        "",
        "**Reading it.** Both estimators are biased *downward* (negative), and the",
        "bias grows with k as bins/sample rises past ~1. Miller-Madow removes most",
        "of it, but at large k the residual and the run-to-run sd (MM sd) are no",
        "longer negligible -- a caution before the search leans on absolute H at",
        "large subset sizes. Working in efficiency eta and/or coarser bins keeps the",
        "effective bin count down and the estimate trustworthy.",
    ]
    return "\n".join(lines) + "\n"


def maybe_plot(rows: list[dict]) -> str | None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    ks = [r["k"] for r in rows]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axhline(0, color="k", lw=0.8)
    ax.plot(ks, [r["plugin_bias"] for r in rows], "o-", label="plug-in")
    ax.plot(ks, [r["miller_bias"] for r in rows], "s-", label="Miller-Madow")
    ax.set_xlabel("subset size k (items)")
    ax.set_ylabel("entropy bias (nats)")
    ax.set_title(f"Total-score entropy bias at N={N_PILOT}")
    ax.legend()
    fig.tight_layout()
    out = HERE / "small_n_estimator_bias.png"
    fig.savefig(out, dpi=120)
    return str(out)


def main() -> None:
    rows = run()
    md = to_markdown(rows)
    (HERE / "small_n_estimator_bias.md").write_text(md)
    print(md)
    png = maybe_plot(rows)
    print(f"figure: {png}" if png else "figure: skipped (matplotlib not installed)")


if __name__ == "__main__":
    main()
