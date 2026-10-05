"""Bounded, spherical-equivalent twist diagnostic; NOT a 3D disk closure.

Units: kpc, km/s, Msun. Phi is relative to Phi(25 kpc)=0.
Only 5 <= spherical radius <= 25 kpc is supported. No extrapolation.
"""
import sys
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from build_wrra_milkyway_paper import model_values, G, ACC_CONV, A_T


class FrozenTwistDiagnostic:
    def __init__(self, nodes=4001):
        r = np.linspace(5., 25., nodes)
        # g_T is frozen by the original baryonic model, a_T and response nu.
        self.g = CubicSpline(r, model_values(r)[3] / ACC_CONV, extrapolate=False)
        self.integral = self.g.antiderivative()

    @staticmethod
    def radius(xyz):
        xyz = np.asarray(xyz, dtype=float)
        if xyz.ndim != 2 or xyz.shape[1] != 3:
            raise ValueError('Expected finite N x 3 Cartesian positions')
        r = np.linalg.norm(xyz, axis=1)
        if not np.all(np.isfinite(xyz)) or np.any((r < 5.) | (r > 25.)):
            raise ValueError('Diagnostic supports only 5 <= r <= 25 kpc')
        return xyz, r

    def potential(self, xyz):
        _, r = self.radius(xyz)
        return self.integral(r) - self.integral(25.)

    def force(self, xyz):
        xyz, r = self.radius(xyz)
        return -self.g(r)[:, None] * xyz / r[:, None]

    def density(self, xyz):
        _, r = self.radius(xyz)
        return (self.g(r, 1) + 2*self.g(r)/r) / (4*np.pi*G)


def density_from_potential(phi, xyz, step=0.001):
    """Poisson inversion of a twice-differentiable potential callback.

    Returns effective TOTAL gravitating density, not stellar counts or a
    WRRA constitutive response to an arbitrary trial potential.
    Stencil must remain within the potential's supported domain.
    """
    xyz = np.asarray(xyz, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.all(np.isfinite(xyz)):
        raise ValueError('Expected finite N x 3 positions')
    if not np.isfinite(step) or step <= 0:
        raise ValueError('step must be positive and finite')
    center = np.asarray(phi(xyz))
    lap = np.zeros(len(xyz))
    for axis in range(3):
        offset = np.zeros(3)
        offset[axis] = step
        lap += (phi(xyz+offset) - 2*center + phi(xyz-offset))/step**2
    return lap / (4*np.pi*G)
