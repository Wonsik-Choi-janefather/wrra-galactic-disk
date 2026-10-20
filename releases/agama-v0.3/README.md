# WRRA AGAMA bridge v0.3 — numerical convergence and Gaia comparison

Wonsik Choi, independent researcher. 20 October 2026.

## Evaluation

| Stage | Evidence |
|---|---|
| Validation inputs | Parent baryonic masses/radii and calibrated residual-response law; explicit finite-height, spherical-residual and stellar-DF assumptions; defined Gaia DR3 sample of 90,113 stars. |
| WRRA transformation | Baryonic state → prescribed residual acceleration → effective density/potential → coupled stellar f(J), Poisson and residual-response iteration. The law and DF parameters are fixed; the field evolves. |
| Outputs | Both tested resolutions meet the local convergence criterion; solar circular speed 215.62 km/s; total midplane density changes by 0.0344% between resolutions; four test-orbit conservation checks pass. |
| Falsification conditions | Numerical inconsistency, non-convergence, or observational disagreement after the tracer populations and selection function are specified. The current geometry-only tracer template does not reproduce the selected height-count profile. |

## Conclusion

An executed, reproducible conditional AGAMA implementation and explicit Gaia comparison are available. Full population- and selection-corrected joint star-count/velocity validation is unfinished. Observed vertical asymmetries also require a non-equilibrium treatment. Calibration to verified measurements is legitimate model construction; these limitations concern this implemented comparison, not a requirement for independent novelty of numerical outputs.

The precision patch exposes existing native AGAMA integration controls; it changes no physical formula. Five extra iterations per resolution start from the archived v0.2 warm start. Read REPRODUCE.txt and the English PDF/Korean report for physical assumptions, measured quantities and remaining work.

The complete public archive on Zenodo contains the raw Gaia CSV. GitHub retains query, retrieval metadata, analysis and numerical results; run fetch_gaia.py to retrieve a fresh catalogue if using GitHub alone. Preserve the archived checksum when checking the original release.

## Files

- [English report](WRRA_AGAMA_v0_3_Binney_Report_EN.pdf)
- [한국어 설명](REPORT_KO.txt)
- [Reproduction](REPRODUCE.txt)
- [Numerical validation](validation/summary.json)
- [Gaia comparison](observations/summary.json)

AGAMA and observational data retain their original authorship and source attribution; see AGAMA_LICENSE and data/PROVENANCE.txt.
