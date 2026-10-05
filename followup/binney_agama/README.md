# Follow-up 0.1: Binney-inspired potential–density interface

Author: Wonsik Choi. Date: 2026-10-05. Parent release: v1.0,
https://doi.org/10.5281/zenodo.23003875.
The original manuscript, parameters and figures are preserved.

## Acknowledgement and scholarly connection

The author thanks James Binney for suggesting an AGAMA-based route to test
potential–density consistency, action-based disk distribution functions,
stellar velocities and solar-neighbourhood stellar distributions in personal
correspondence received on 5 October 2026. The date and methodological summary
are recorded from the author's supplied account; the original email has not
been independently inspected in this follow-up. This acknowledgement credits
methodological advice, not coauthorship, participation, endorsement or completed
observational validation. Binney indicated that he had no time to participate.
No private email text or address is published here.

Binney (2010) [1] provides the scientific connection: action-based distribution
functions with a vertical-action sector that controls vertical structure. It
motivates the future `f(J_R,J_z,J_phi)` layer. Vasiliev (2019) [2] provides the
AGAMA computational architecture. Neither is claimed to be a WRRA result.

## Inspection of the existing release

Inspected parent commit: `2528be62a70c1579308389621e75988f1f777c82`.
The English PDF distributed in the repository and its numerical build script
were read directly. The DOI landing page was not retrievable in this session;
identity with the current Zenodo file bytes has not been checked.

| Item | Implemented in v1.0 | Needed for follow-up |
|---|---|---|
| Baryonic radial gravity | Four razor-thin exponential disks and Hernquist bulge | Finite-thickness 3D baryonic potential with declared scale heights |
| Additional radial gravity | Frozen `a_T` and `nu`, evaluated in `model_values` | Off-plane extension of the same state |
| Warp surface | Calibrated m=1 surface | Orbital/time evolution; non-axisymmetric stage |
| Equivalent twist mass | Spherical inverse ledger `M_T=r^2 g_T/G` | 3D effective density closure |
| `q_T`, vertical restoring frequency | Discussed; no numerical constitutive closure | Explicit closure before an observational test |
| Action DF and AGAMA | Absent | DF, action computation, moments, self-consistency |
| Gaia RVS and local stellar counts | Absent | Selection functions, uncertainties, sample definitions, likelihood |

## What Phi → rho means

Two different maps must not be confused:

1. Poisson inversion: `rho_eff = Laplacian(Phi)/(4*pi*G)`. In cylindrical
   axisymmetry this is `(Phi_RR + Phi_R/R + Phi_zz)/(4*pi*G)` for `R>0`.
   This diagnoses a specified twice-differentiable gravitational potential.
   `density_from_potential` implements Cartesian finite differences, avoiding
   the cylindrical axis singularity. For the twist-only potential it returns
   twist effective source density; for a total potential it returns total
   gravitating density. Neither is a stellar number density.
2. WRRA response in a self-consistency iteration:
   `rho_T_eff = C[Phi_total, rho_b, T_fixed]`, with baryonic density from
   `integral f(J[Phi_total]) d^3v` plus gas/bulge sources, and total potential
   sourced by `rho_b + rho_T_eff`. This constitutive operator is not defined by
   v1.0. Poisson inversion alone would make this iteration tautological and
   is not a substitute for `C`.

The rotation curve specifies `Phi_R(R,0)` but does not determine `Phi_zz`.
For example, adding `z^2 h(R)` leaves the midplane radial force unchanged
while changing vertical force and density. Binney's proposed test therefore
requires a declared 3D WRRA closure; it cannot be inferred uniquely from the
published curve. This is a definition gap, not a requirement for a novel number.

## Minimal executable closure (diagnostic only)

We explicitly impose spherical symmetry for the *additional field only*:
`r=sqrt(R^2+z^2)`, `Phi_T(r)=integral_25^r g_T(s) ds`,
`F_T=-g_T(r) x/r`,
`rho_T_eff=(g_T'(r)+2 g_T(r)/r)/(4*pi*G)`.
Here `g_T` is the unchanged original response, converted to `(km/s)^2/kpc`.
This follows the spherical-equivalent mass ledger already in v1.0 but adds
a new explicitly declared diagnostic symmetry assumption. It does not derive
`q_T`, does not implement the warped disk plane and is not the final WRRA disk.
No independently fitted vertical amplitude is introduced. Under this assumption
alone `nu_T,z^2(R,0)=g_T(R)/R`; it is not the total disk vertical frequency.

Domain: **5–25 kpc spherical radius**, no extrapolation. The arbitrary gauge
`Phi_T(25)=0` is suitable for local derivative checks, not escape energies or
DF integrations. An inner/outer extension and boundary convention must be
specified before orbit/action/DF integrations. No global multipole potential
or self-consistent galaxy is silently generated from this bounded callback.

```bash
python followup/binney_agama/run_minimal.py
# With a separately installed AGAMA:
python followup/binney_agama/run_minimal.py --agama
```

AGAMA wrapping uses `Potential(potential=callback, symmetry='s')` and
`Density(density=callback, symmetry='s')`, following its upstream
`py/test_user_profiles.py`. Potential values have units `(km/s)^2`;
positions are Cartesian `N x 3` arrays in kpc. The script explicitly converts
the AGAMA external mass unit to preserve the original numerical `G`.

## Calibration ledger

| Entry | Policy |
|---|---|
| `a_T=1.191812669e-10 m/s^2`, `nu` functional form | Fixed from v1.0 |
| Original radial baryonic masses/scale lengths | Fixed for this diagnostic |
| Spherical twist symmetry | New diagnostic assumption; no fit |
| `q_T` / 3D constitutive law | Undetermined; must be declared and frozen before joint test |
| Finite baryonic thickness and global boundaries | New physical inputs required; cannot be silently calibrated on vertical targets |
| DF `J_z` parameters, velocity scales and tracer normalizations | May be fitted under a declared ledger; not changes to WRRA gravity |
| Self-gravitating DF changes baryonic density | Recompute potential through the SAME frozen response operator; log changes and radial residuals |
| Independent radial/vertical force amplitudes | Prohibited in the joint validation |
| Survey selection, solar motion, population/luminosity model | Declared nuisance/input quantities; needed for velocities and star counts |

A tracer-DF fit in a fixed potential is distinct from a self-gravitating DF
iteration. In the latter, changing stellar density necessarily changes total
potential; fixed means the same WRRA law/state constraints, not numerically
holding an incompatible total potential while changing its sources.

## Evaluation and next gates

| Stage | Current evidence |
|---|---|
| Validation input | Parent code/PDF, original calibration, declared spherical diagnostic; no Gaia ingestion |
| WRRA transformation | Frozen radial response → spherical diagnostic Phi, force, effective density; generic Poisson adapter |
| Output | `results.json` records executed numerical checks and original rotation values |
| Falsification condition | Gradient/Poisson inconsistency or extra radial/vertical field refitting; joint observational failure when a full closure is frozen |

Next gates, without extending v1.0's claims:
1. Declare finite-thickness baryonic sources and a global potential domain.
2. Specify and freeze `C`/`q_T`; compare radial changes to the parent ledger.
3. Run AGAMA action-DF and self-consistency checks with convergence and
   Poisson residuals, without counting twist twice.
4. Define Gaia RVS selection/error model and fit allowed DF parameters. Mean
   stellar azimuthal velocity is not automatically `V_c`: model asymmetric
   drift and solar motion.
5. Jointly compare radial velocities, `p(v_z|R,z)`, `K_z` and local stellar
   number-density profiles with population/selection conversion. Then assess
   the warped, non-axisymmetric/time-dependent stage separately.

No observational pass is claimed by this interface release. Numerical errors
are implementation checks, not observational fit errors or proof of the
physical twist hypothesis.

### Executed result (2026-10-05)

Python 3.12, NumPy 2.3.5, SciPy 1.17.0. The standalone check passed:
maximum force-gradient relative error `1.51e-9`; Poisson relative errors
`1.02e-6`, `2.53e-7`, `2.33e-7` at steps 0.01, 0.005, 0.002 kpc;
independent analytic Plummer inversion error `5.32e-6`.
The density was positive at the 80 diagnostic sample radii; this is not a
global positivity proof. Out-of-domain evaluation was rejected.

AGAMA source was fetched and its callback API inspected, but local compilation
failed in its Python-library linkage probe (`Could not compile test program
which uses libpython3.12`). Thus `--agama` was **not executed**; its callback
path remains untested. The published result records `agama.executed=false`.

## References

[1] Binney, J. (2010). Distribution functions for the Milky Way.
*Monthly Notices of the Royal Astronomical Society*, **401**, 2318–2330.
https://doi.org/10.1111/j.1365-2966.2009.15845.x
https://arxiv.org/abs/0910.1512

[2] Vasiliev, E. (2019). AGAMA: action-based galaxy modelling architecture.
*Monthly Notices of the Royal Astronomical Society*, **482**, 1525–1544.
https://doi.org/10.1093/mnras/sty2672
https://arxiv.org/abs/1802.08239

[3] Choi, W. (2026). WRRA Spatial Twist Selection of Galactic Disk Planes
and the Dark Mass Phenotype, v1.0.
https://doi.org/10.5281/zenodo.23003875

AGAMA upstream: https://github.com/GalacticDynamics-Oxford/Agama.
API inspected at commit `f302756b8af2b763db58e278e30478517dc8eea3`.

Future archival editions should cite [1–3] and carry this acknowledgement as
methodological advice. This repository addendum does not modify an existing
Zenodo version or claim a new Zenodo publication.

## v1.1 SciPy fallback (executed)

Run `python followup/binney_agama/fallback_vertical.py`. At fixed R=8.2 kpc,
this solves the auxiliary local 1D Hamiltonian of the same spherical twist
field, computes its J_z, integrates orbits and evaluates finite-support tracer
DF moments. It holds R fixed and omits radial coupling and baryonic vertical
force; this J_z is not a full 3D Galactic action. Both demonstration DFs use
the same field. The energy cutoff at 2 kpc is a diagnostic boundary assumption.
The action-period identity, orbit energy conservation, PDF normalization and
local vertical Jeans identity pass. See `fallback_results.json` and the
four-page addendum in `papers/WRRA_Galactic_Disk_v1_1_EN.pdf` (followed by the
unchanged original twelve-page manuscript). Full AGAMA self-consistency and
observational comparison remain unexecuted.

During v1.1 preparation the Zenodo record was accessible through its signed-in
UI. Its published v1.0 MD5, `1ec9da6fbe2daaed27aee94cc0da3afd`, matches the
repository English PDF. The earlier access limitation above applies to the
initial search-tool attempt, not to this later successful inspection.
