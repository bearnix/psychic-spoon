# Small-N total-score entropy estimator bias

Generative model: latent-trait, DISCRIMINATION=1.0, ITEM_NOISE=0.8; N=51, 400 replicates; truth from N=400,000.
All entropies in nats. Bias = E[estimate] - truth.

| k | support (bins) | truth H | plug-in bias | Miller-Madow bias | MM sd |
|---|----------------|---------|--------------|-------------------|-------|
| 2 | 9 | 2.118 | -0.082 | -0.005 | 0.069 |
| 4 | 17 | 2.741 | -0.173 | -0.033 | 0.091 |
| 6 | 25 | 3.121 | -0.258 | -0.065 | 0.100 |
| 8 | 33 | 3.395 | -0.359 | -0.131 | 0.105 |
| 10 | 41 | 3.609 | -0.438 | -0.179 | 0.108 |
| 12 | 49 | 3.786 | -0.516 | -0.231 | 0.108 |
| 16 | 65 | 4.066 | -0.661 | -0.340 | 0.106 |
| 20 | 81 | 4.286 | -0.797 | -0.452 | 0.102 |

**Reading it.** Both estimators are biased *downward* (negative), and the
bias grows with k as bins/sample rises past ~1. Miller-Madow removes most
of it, but at large k the residual and the run-to-run sd (MM sd) are no
longer negligible -- a caution before the search leans on absolute H at
large subset sizes. Working in efficiency eta and/or coarser bins keeps the
effective bin count down and the estimate trustworthy.
