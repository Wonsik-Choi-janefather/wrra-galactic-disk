"""Conditional conservative completion of the frozen WRRA radial residual.

Units: kpc, km/s, solar masses. This is not a full AGAMA/DF fit.
Spatial flattening q is an explicit additional closure, not an upstream result.
"""
from pathlib import Path
import math
import numpy as np
from scipy.special import ive, kve, j0
from scipy.interpolate import CubicSpline
from scipy.integrate import quad

G = 4.30091e-6
ACC_CONV = 1e6 / 3.0856775814913673e19
A_T = 1.191812669e-10
COMPONENTS = {
    'thin': (2*math.pi*886.7e6*2.53**2, 2.53),
    'thick': (2*math.pi*156.7e6*3.38**2, 3.38),
    'HI': (1.1e10, 7.0), 'H2': (1.2e9, 1.5),
}
M_BULGE, A_BULGE = 9.13e9, 0.7

def baryonic_v2(r):
    r = np.asarray(r, dtype=float)
    result = G*M_BULGE*r/(r+A_BULGE)**2
    for mass, rd in COMPONENTS.values():
        y = r/(2*rd)
        kernel = ive(0,y)*kve(0,y)-ive(1,y)*kve(1,y)
        result = result + 2*G*mass/rd*y*y*kernel
    return result

def residual_g(r):
    gm = baryonic_v2(r)/np.asarray(r)
    return gm/np.expm1(np.sqrt(gm*ACC_CONV/A_T))

def rotation_speed(r):
    return np.sqrt(baryonic_v2(r)+np.asarray(r)*residual_g(r))

class ResidualPotential:
    """Phi_T(R,z)=F(sqrt(R^2+z^2/q^2)); F'=g_T.

    The finite domain is deliberately enforced: no unverified extrapolation,
    origin regularisation, outer truncation or global AGAMA callback is implied.
    q is potential flattening, NOT the upstream anisotropic stress q_T.
    """
    def __init__(self, q=1.0, nodes=8193, rmin=0.1, rmax=100.0):
        if not np.isfinite(q) or q <= 0:
            raise ValueError('q must be positive and finite')
        self.q, self.rmin, self.rmax = float(q), rmin, rmax
        r = np.geomspace(rmin, rmax, nodes)
        self.gs = CubicSpline(r, residual_g(r), extrapolate=False)
        self.F = self.gs.antiderivative()
        self.offset = self.F(8.2)

    def _geom(self, xyz):
        xyz = np.asarray(xyz,dtype=float)
        if xyz.shape[-1] != 3 or not np.all(np.isfinite(xyz)):
            raise ValueError('finite Cartesian coordinates (...,3) required')
        A = np.array([1.,1.,1/self.q**2])
        s = np.sqrt(np.sum(A*xyz*xyz, axis=-1))
        if np.any((s < self.rmin) | (s > self.rmax)):
            raise ValueError('outside verified ellipsoidal-radius domain')
        return xyz, A, s

    def potential(self, xyz):
        _, _, s = self._geom(xyz)
        return self.F(s)-self.offset

    def force(self, xyz):
        xyz,A,s = self._geom(xyz)
        return -self.gs(s)[...,None]*A*xyz/s[...,None]

    def density(self, xyz):
        xyz,A,s = self._geom(xyz)
        w = np.sum(A*A*xyz*xyz, axis=-1)/s**2
        lap = self.gs(s,1)*w+self.gs(s)/s*(A.sum()-w)
        return lap/(4*math.pi*G)

def baryonic_kz(R,z):
    """Signed dPhi_b/dz. Exact off-plane razor-thin exponential discs.

    At z=0 the distributional sheet force is discontinuous; reject that input.
    Original thin-disc approximation retained, no new height parameters fitted.
    """
    if abs(z) < 0.05:
        raise ValueError('off-plane quadrature verified only for |z|>=0.05 kpc')
    radius = math.hypot(R,z)
    result = G*M_BULGE*z/(radius*(radius+A_BULGE)**2)
    for mass,rd in COMPONENTS.values():
        val,err = quad(lambda k:k*j0(k*R)*math.exp(-k*abs(z))/(1+(k*rd)**2)**1.5,
                       0,np.inf,epsabs=1e-11,epsrel=1e-9,limit=1000)
        result += G*mass*val*np.sign(z)
    return result

def baryonic_sheet(R):
    return sum(m/(2*math.pi*rd**2)*math.exp(-R/rd) for m,rd in COMPONENTS.values())

def equivalent_surface(Kz):
    """Kz/(2 pi G), a force diagnostic, NOT the actual integrated column."""
    return Kz/(2*math.pi*G)/1e6
