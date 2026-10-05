"""Run numerical interface checks; optional genuine AGAMA callback smoke test."""
import argparse
import json
from pathlib import Path
import numpy as np
from interface import FrozenTwistDiagnostic, density_from_potential, model_values, G, A_T


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agama', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('results.json'))
    args = parser.parse_args()
    m = FrozenTwistDiagnostic()
    r = np.linspace(5.1, 24.9, 80)
    points = np.column_stack((r, np.zeros_like(r), np.zeros_like(r)))
    rho = m.density(points)
    errors = {}
    for h in (0.01, 0.005, 0.002):
        errors[str(h)] = float(np.max(np.abs(density_from_potential(m.potential, points, h)/rho-1)))
    h = 0.001
    offset = np.array([h, 0., 0.])
    grad = (m.potential(points+offset)-m.potential(points-offset))/(2*h)
    ferr = float(np.max(np.abs(grad/(-m.force(points)[:,0])-1)))
    mass = r*r*m.g(r)/G
    mass_gradient = (2*r*m.g(r)+r*r*m.g(r, 1))/G
    merr = float(np.max(np.abs(mass_gradient/(4*np.pi*r*r*rho)-1)))
    # Check a generic known potential independently of the twist implementation.
    plummer = lambda p: -G*1e10/np.sqrt(np.sum(p*p,axis=1)+4.)
    plummer_rho = 3*1e10*4/(4*np.pi*(r*r+4.)**2.5)
    perr = float(np.max(np.abs(density_from_potential(plummer, points, 0.002)/plummer_rho-1)))
    escaped = False
    try:
        m.potential(np.array([[26.,0.,0.]]))
    except ValueError:
        escaped = True
    assert max(errors.values()) < 1e-4 and ferr < 1e-5 and merr < 1e-12 and perr < 1e-4
    assert np.all(rho > 0) and escaped
    out = {
        'status': 'numerical_interface_checks_only_no_observational_validation',
        'closure': 'spherical_equivalent_twist_only_not_disk_total_potential',
        'units': {'length':'kpc', 'velocity':'km/s', 'mass':'Msun', 'density':'Msun/kpc^3'},
        'a_T_m_s2': A_T,
        'potential_gauge': 'Phi_T(25 kpc)=0; not an escape-energy normalization',
        'poisson_max_relative_errors_by_step_kpc': errors,
        'force_gradient_max_relative_error': ferr,
        'mass_density_max_relative_error': merr,
        'independent_plummer_poisson_max_relative_error': perr,
        'positive_density_on_80_sample_points': True,
        'outside_domain_rejected': escaped,
        'original_total_vc_km_s': {str(x): float(model_values(np.array([x]))[4][0]) for x in (8.2,25.)},
        'agama': {'executed':False},
        'not_executed':['3D baryonic finite-thickness potential', 'q_T constitutive closure',
                        'self-consistent DF iteration', 'Gaia RVS comparison', 'stellar counts', 'warp dynamics']}
    if args.agama:
        import agama
        # Match the original numerical G exactly by selecting the external mass unit.
        agama.setUnits(length=1, velocity=1, mass=1)
        raw_g = agama.G
        mass_unit = G/raw_g
        agama.setUnits(length=1, velocity=1, mass=mass_unit)
        potential = agama.Potential(potential=m.potential, symmetry='s')
        density = agama.Density(density=lambda p: m.density(p)/mass_unit, symmetry='s')
        p = np.array([[8.2,0.,0.],[8.2,0.,0.3],[12.,0.,0.7]])
        ae = float(np.max(np.abs(potential.force(p)/np.where(m.force(p)==0,1,m.force(p)) -
                            (m.force(p)!=0))))
        de = float(np.max(np.abs(density.density(p)*mass_unit/m.density(p)-1)))
        # Include AGAMA's numerical second derivatives as a separate check.
        pe = float(np.max(np.abs(potential.density(p)*mass_unit/m.density(p)-1)))
        assert ae < 1e-4 and de < 1e-12 and pe < 1e-3
        out['agama'] = {'executed':True, 'scope':'Potential and Density callback evaluation only',
            'version':str(getattr(agama,'__version__','unknown')),
            'external_mass_unit_Msun':mass_unit, 'force_max_relative_error_nonzero_components':ae,
            'density_callback_max_relative_error':de, 'potential_poisson_density_max_relative_error':pe}
    args.output.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
