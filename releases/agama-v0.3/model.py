"""Finite-thickness, global spherical-response completion for actual AGAMA runs.

The spatial closure is conditional: the observed/input disc heights, spherical
residual response and distant outer taper are model specifications, not derived
microscopic stress dynamics. No fit to velocity data is performed here.
"""
from pathlib import Path
import sys
import math
import re
import numpy as np
from scipy.interpolate import CubicSpline
import agama

try:
    import frozen_radial as frozen
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'binney_bridge_v0_1'))
    import bridge as frozen

agama.setUnits(length=1,velocity=1,mass=1)
G=float(agama.G)
HEIGHTS={'thin':.3,'thick':.9,'HI':-.085,'H2':-.045}

def make_baryons(height_factor=1.):
    discs=[];densities=[]
    for name,(mass,rd) in frozen.COMPONENTS.items():
        d=agama.Density(type='Disk',mass=mass,scaleRadius=rd,
                        scaleHeight=HEIGHTS[name]*height_factor)
        densities.append(d)
        # Disk constructor uses the analytic disc ansatz plus an expansion.
        discs.append(agama.Potential(type='Disk',mass=mass,scaleRadius=rd,
                      scaleHeight=HEIGHTS[name]*height_factor))
    bulge=agama.Potential(type='Dehnen',mass=frozen.M_BULGE,
                          scaleRadius=frozen.A_BULGE,gamma=1.)
    return agama.Potential(*discs,bulge),discs,densities,bulge

class SphericalResponse:
    def __init__(self,baryons,core=.01,taper_start=100.,taper_width=200.,nodes=4097):
        self.core,self.taper_start,self.taper_width=core,taper_start,taper_width
        self.r=np.geomspace(.0005,1e4,nodes)
        xyz=np.column_stack([self.r,np.zeros_like(self.r),np.zeros_like(self.r)])
        gb=-baryons.force(xyz)[:,0]
        if not np.all(np.isfinite(gb)&(gb>0)):
            raise ValueError('baryonic radial force must be finite and attractive')
        self.gtarget=gb/np.expm1(np.sqrt(gb*frozen.ACC_CONV/frozen.A_T))
        mass=self.r**2*self.gtarget/G
        self.logmass=CubicSpline(np.log(self.r),np.log(mass),extrapolate=False)
        # Positivity is required before smoothing or any Poisson reconstruction.
        slopes=self.logmass(np.log(self.r),1)
        if np.any(slopes<0):
            raise ValueError('negative spherical density in prescribed response')

    def density(self,xyz):
        xyz=np.asarray(xyz)
        r=np.linalg.norm(xyz,axis=-1)
        s=np.sqrt(r*r+self.core*self.core)
        s=np.clip(s,self.r[0],self.r[-1])
        log=np.log(s)
        rho=np.exp(self.logmass(log))*self.logmass(log,1)/(4*math.pi*s**3)
        taper=np.exp(-(np.maximum(r-self.taper_start,0)/self.taper_width)**4)
        return rho*taper

    def potential(self,grid=180):
        return agama.Potential(type='Multipole',density=self.density,symmetry='s',
                                lmax=0,gridSizeR=grid,rmin=.0005,rmax=2500.)

def stellar_df(initial_potential):
    dfs=[];params=[]
    # Dispersion amplitudes are explicit initial DF choices, not new observations
    # or WRRA predictions; freeze these before subsequent iterations.
    for name,sigmar_local in [('thin',35.),('thick',55.)]:
        mass,rd=frozen.COMPONENTS[name]
        rs=2*rd
        par=dict(type='QuasiIsothermal',mass=mass,Rdisk=rd,Hdisk=abs(HEIGHTS[name]),
                 sigmar0=sigmar_local*math.exp(8.2/rs),Rsigmar=rs,sigmamin=5.,Jmin=10.)
        dfs.append(agama.DistributionFunction(potential=initial_potential,**par))
        params.append(dict(component=name,**par))
    return agama.DistributionFunction(*dfs),params

def diagnostics(potential):
    r=np.linspace(5,25,81)
    x=np.column_stack([r,np.zeros_like(r),np.zeros_like(r)])
    vc=np.sqrt(-r*potential.force(x)[:,0])
    z=np.linspace(.1,2.,20)
    xz=np.column_stack([np.full_like(z,8.2),np.zeros_like(z),z])
    kz=-potential.force(xz)[:,2]
    return r,vc,z,kz

def load_final_potential(folder):
    """Recreate analytic components explicitly, reload exported expansions.

    AGAMA's general export omits parameters of DiskAnsatz and Dehnen; the raw
    composite export therefore must NOT be advertised as a standalone model.
    """
    folder=Path(folder)
    if not ((folder/'residual_multipole.ini').exists() and (folder/'stellar_cylspline.ini').exists()):
        text=(folder/'final_potential.ini').read_text()
        blocks=re.split(r'(?=^\[Potential[^\]]*\])',text,flags=re.M)
        multipoles=[b for b in blocks if re.search(r'^type=Multipole$',b,re.M)]
        cylinders=[b for b in blocks if re.search(r'^type=CylSpline$',b,re.M)]
        if not multipoles or len(cylinders)!=1:
            raise ValueError('Unexpected composite export structure')
        # Static gas corrections precede the spherical WRRA Multipole.
        for name,block in [('residual_multipole.ini',multipoles[-1]),('stellar_cylspline.ini',cylinders[0])]:
            block=re.sub(r'^\[Potential[^\]]*\]','[Potential]',block,count=1,flags=re.M)
            (folder/name).write_text(block)
    _,discs,_,bulge=make_baryons()
    residual=agama.Potential(str(folder/'residual_multipole.ini'))
    stars=agama.Potential(str(folder/'stellar_cylspline.ini'))
    return agama.Potential(discs[2],discs[3],bulge,residual,stars)
