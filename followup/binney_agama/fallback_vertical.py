"""SciPy local 1D vertical-action fallback in the frozen spherical twist field.
No baryonic vertical field, self-gravity, Gaia data or full 3D actions.
Time unit kpc/(km/s); J unit kpc km/s. Domain |z|<=2 kpc, R=8.2 kpc.
"""
import json
from pathlib import Path
import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq
from interface import FrozenTwistDiagnostic

m=FrozenTwistDiagnostic()
R=8.2
ZMAX=2.0

def phi(z):
    z=np.asarray(z)
    return m.integral(np.sqrt(R*R+z*z))-m.integral(R)

def force(z):
    r=np.sqrt(R*R+z*z)
    return -m.g(r)*z/r

def action_period(amplitude):
    energy=float(phi(amplitude))
    # z=a sin(theta) regularizes the turning point.
    def action_integrand(t):
        z=amplitude*np.sin(t)
        return np.sqrt(max(0.,2*(energy-float(phi(z)))))*amplitude*np.cos(t)
    def period_integrand(t):
        z=amplitude*np.sin(t)
        return amplitude*np.cos(t)/np.sqrt(2*(energy-float(phi(z))))
    J=2/np.pi*quad(action_integrand,0,np.pi/2,epsabs=1e-8)[0]
    period=4*quad(period_integrand,0,np.pi/2,epsabs=1e-8)[0]
    return energy,J,period

def action_energy(energy):
    a=brentq(lambda z:float(phi(z))-energy,1e-10,ZMAX)
    return action_period(a)[1]

def main():
    rows=[]
    for a in (0.1,0.3,0.7,1.0,1.5):
        E,J,T=action_period(a)
        dE=E*1e-4
        derivative=(action_energy(E+dE)-action_energy(E-dE))/(2*dE)
        identity=abs(derivative/(T/(2*np.pi))-1)
        def rhs(t,y):return [y[1],float(force(y[0]))]
        sol=solve_ivp(rhs,[0,4*T],[0,np.sqrt(2*E)],rtol=1e-10,atol=1e-11,max_step=T/100)
        energies=.5*sol.y[1]**2+phi(sol.y[0])
        drift=float(np.max(np.abs(energies/E-1)))
        assert sol.success and drift<1e-7 and identity<1e-5
        rows.append({'zmax_kpc':a,'E_km2_s2':E,'Jz_kpc_km_s':J,'period_kpc_per_km_s':T,
                     'dJdE_period_relative_error':identity,'four_period_energy_relative_drift':drift})
    # Finite-domain equilibrium DF F(E)=exp(-E/sigma^2) for E<Ecut, zero otherwise.
    # This is also F(J)=exp(-E(J)/sigma^2), with J(E) computed above.
    # Demonstrates tracer freedom at identical potential; sigmas are demonstration inputs.
    Ecut=float(phi(ZMAX))
    tracers=[]
    for sigma in (10.,20.):
        def moments(z):
            p=float(phi(z)); vmax=np.sqrt(2*(Ecut-p))
            n=2*quad(lambda v:np.exp(-(.5*v*v+p)/sigma**2),0,vmax,epsabs=1e-9)[0]
            s2=2*quad(lambda v:v*v*np.exp(-(.5*v*v+p)/sigma**2),0,vmax,epsabs=1e-9)[0]/n
            return n,s2,vmax
        n0=moments(0)[0]
        profile=[]
        for z in (0.,0.3,0.7,1.):
            n,s2,vmax=moments(z)
            normalization=quad(lambda v:np.exp(-(.5*v*v+float(phi(z)))/sigma**2)/n,-vmax,vmax)[0]
            assert abs(normalization-1)<1e-9
            profile.append({'z_kpc':z,'relative_tracer_density':n/n0,'sigma_vz_km_s':np.sqrt(s2),
                            'velocity_pdf_integral':normalization})
        z=.5;h=1e-4
        pressure=lambda z:moments(z)[0]*moments(z)[1]
        gradient=(pressure(z+h)-pressure(z-h))/(2*h)
        expected=moments(z)[0]*float(force(z))
        jeans_error=abs(gradient/expected-1)
        assert jeans_error<1e-5
        tracers.append({'input_sigma_km_s':sigma,'vertical_Jeans_relative_error_at_z_0_5':jeans_error,'profile':profile})
    out={'status':'executed_local_1D_twist_only_diagnostic_no_observational_validation',
         'solver':'SciPy quadrature, root finding and solve_ivp', 'R_kpc':R,
         'energy_cutoff_at_z_kpc':ZMAX,'Ecut_km2_s2':Ecut,
         'boundary':'DF has compact energy support; cutoff is diagnostic assumption, not observed disk edge',
         'unchanged_field_between_DFs':True,'orbit_action_checks':rows,'tracer_DFs':tracers,
         'not_claimed':['full AGAMA equivalence','full 3D actions','baryonic vertical force','self-consistent disk','Gaia fit']}
    path=Path(__file__).with_name('fallback_results.json')
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
