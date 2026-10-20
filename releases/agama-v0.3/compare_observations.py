"""Actual public Gaia comparisons, with explicit selection/population limits."""
from pathlib import Path
import json,csv,math,hashlib
import numpy as np
from scipy.optimize import minimize
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import *

HERE=Path(__file__).resolve().parent
OUT=HERE/'observations';OUT.mkdir(exist_ok=True)
def csvfile(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

p=load_final_potential(HERE/'results_refined')
b,_,_,_=make_baryons()
p0=agama.Potential(b,SphericalResponse(b).potential(grid=450))
df,_=stellar_df(p0)
af=agama.ActionFinder(p,interp=True)
gm=agama.GalaxyModel(p,df,af)

# Reflection-symmetric equilibrium predicts zero count asymmetry and zero
# vertical streaming for every population, regardless of its mass normalization.
zp=np.array([.2,.6,1.1])
pts=np.array([[8.2,0,z] for z in np.r_[zp,-zp]])
rho,vel=gm.moments(pts,dens=True,vel=True,vel2=False,
                 relError=1e-4,maxNumEval=1000000)
parity_error=float(np.max(abs((rho[:3]-rho[3:])/(rho[:3]+rho[3:]))))
streaming_max=float(np.max(abs(vel[:,2])))
if parity_error>1e-8 or streaming_max>1e-6:
    raise ValueError('Equilibrium symmetry check failed')

# Author-released DR2 tables: no fabricated digitisation or synthetic data.
a=np.loadtxt(HERE/'data/Asym_bin.txt')
v=np.loadtxt(HERE/'data/bin_vel.txt')
w=1/v[2]**2
offset=float(np.sum(w*v[1])/w.sum())
offseterr=float(1/math.sqrt(w.sum()))
chiA=float(np.sum((a[1]/a[2])**2))
chiV=float(np.sum(((v[1]-offset)/v[2])**2))
csvfile('published_DR2_count_asymmetry.csv',[
    dict(z_kpc=z,A_observed=aa,error=er,A_equilibrium=0.,pull_diagonal=aa/er)
    for z,aa,er in a.T])
csvfile('published_DR2_median_vertical_velocity.csv',[
    dict(z_heliocentric_kpc=z,median_vz_kms=vv,error_kms=er,
         equilibrium_offset_kms=offset,pull_diagonal=(vv-offset)/er)
    for z,vv,er in v.T])

# Direct ESA archive sample. IDs remain intact in the raw CSV; they are not
# converted to floats or used in the numerical arrays below.
d=np.genfromtxt(HERE/'data/gaia_dr3_sample.csv',names=True,delimiter=',',
               usecols=range(1,11),missing_values='',filling_values=np.nan)
z=d['z_kpc'];edges=np.arange(.15,1.00001,.05)
centres=(edges[1:]+edges[:-1])/2
plus=np.histogram(z,bins=edges)[0]
minus=np.histogram(-z,bins=edges)[0]
folded=plus+minus
asym=(plus-minus)/folded
asymerr=np.sqrt(4*plus*minus/folded**3)

# Integrate each fixed stellar DF over the same geometric cylinder and z bins.
# This is a geometry-only forward model. Population-dependent luminosity,
# colour, extinction, RUWE and survey completeness are not silently omitted
# from a claimed complete selection function; instead, that gate stays open.
gz,wz=leggauss(3);gu,wu=leggauss(2)
coords=[];weights=[];ibin=[]
for i,(low,high) in enumerate(zip(edges[:-1],edges[1:])):
    for uz,wwz in zip(gz,wz):
        zz=(low+high)/2+uz*(high-low)/2
        for u,wwu in zip(gu,wu):
            dist=.25*math.sqrt((u+1)/2)
            for phi in (np.arange(4)+.5)*math.pi/2:
                R=math.sqrt(8.2**2+dist**2-2*8.2*dist*math.cos(phi))
                coords.append([R,0,zz]);ibin.append(i)
                # factor 2 folds both Galactic hemispheres
                weights.append(2*math.pi*.25**2*(high-low)/2*wwz*wwu/2/4)
den=gm.moments(np.asarray(coords),dens=True,vel=False,vel2=False,separate=True,
               relError=1e-4,maxNumEval=1000000)
X=np.zeros((len(centres),2))
for i,ww,dd in zip(ibin,weights,den):X[i]+=ww*dd
c0=folded.sum()/X.sum()
def objective(logc):
    mu=X@np.exp(logc)
    return float(np.sum(mu-folded*np.log(mu)))
fit=minimize(objective,np.log([c0,c0]),method='L-BFGS-B',bounds=[(-25,5),(-25,5)])
if not fit.success:raise ValueError('Global tracer-normalization optimization failed')
c=np.exp(fit.x);mu=X@c
deviance=float(2*np.sum(folded*np.log(folded/mu)-folded+mu))
csvfile('direct_DR3_folded_counts.csv',[
    dict(z_low_kpc=lo,z_high_kpc=hi,z_mid_kpc=zz,N_north=int(nn),N_south=int(ns),
         N_folded=int(nt),count_asymmetry=aa,asymmetry_poisson_error=ee,
         model_count_global_tracer_weights=float(mm),relative_count_residual=float(nt/mm-1))
    for lo,hi,zz,nn,ns,nt,aa,ee,mm in zip(edges[:-1],edges[1:],centres,plus,minus,folded,asym,asymerr,mu)])

# Heliocentric ICRS velocity -> Galactic W, then one fixed solar W offset.
# The ICRS-to-Galactic rotation matrix is the standard right-handed IAU frame.
ra=np.deg2rad(d['ra']);dec=np.deg2rad(d['dec'])
ez=np.array([-.8676661490190047,-.1980763734312015,.4559837761750669])
n=np.column_stack([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)])
era=np.column_stack([-np.sin(ra),np.cos(ra),ra*0])
edec=np.column_stack([-np.sin(dec)*np.cos(ra),-np.sin(dec)*np.sin(ra),np.cos(dec)])
W=d['radial_velocity']*(n@ez)+4.74047/d['parallax']*(d['pmra']*(era@ez)+d['pmdec']*(edec@ez))+7.25
valid=np.isfinite(W)&np.isfinite(d['radial_velocity_error'])&(d['radial_velocity_error']<3.)
vedges=np.arange(-1,1.00001,.1);vr=[]
for lo,hi in zip(vedges[:-1],vedges[1:]):
    values=W[valid&(z>=lo)&(z<hi)]
    if len(values)<30:continue
    med=float(np.median(values));mad=float(1.4826*np.median(abs(values-med)))
    vr.append(dict(z_mid_kpc=(lo+hi)/2,N_RV=int(len(values)),median_W_kms=med,
                   robust_sigmaW_kms=mad,median_SE_approx_kms=1.253314*mad/math.sqrt(len(values))))
csvfile('direct_DR3_RVS_vertical_velocity.csv',vr)
ww=np.array([1/r['median_SE_approx_kms']**2 for r in vr])
vv=np.array([r['median_W_kms'] for r in vr]);v0=float(np.sum(ww*vv)/ww.sum())

summary=dict(
    model='v0.3 precision-controlled reflected axisymmetric equilibrium',
    reflection_error=parity_error,max_abs_equilibrium_mean_vz_kms=streaming_max,
    published_DR2=dict(author='Bennett & Bovy',paper='https://arxiv.org/abs/1809.03507',
        repository_commit='203c2e111c24b99351871e562d4efe193fed586b',
        count_asymmetry_bins=a.shape[1],max_abs_count_asymmetry=float(np.max(abs(a[1]))),
        count_asymmetry_zero_model_diagonal_chi2=chiA,
        velocity_bins=v.shape[1],fitted_global_velocity_offset_kms=offset,
        velocity_offset_diagonal_error_kms=offseterr,velocity_constant_model_diagonal_chi2=chiV,
        covariance_supplied=False,formal_joint_likelihood=False,
        result='Observed vertical perturbations are not reproduced by the symmetric equilibrium background; same limitation applies to any reflected equilibrium control.'),
    direct_DR3=dict(rows=len(d),rows_with_RV=int(np.isfinite(d['radial_velocity']).sum()),
        RV_error_cut_kms=3.,RV_rows_after_cut=int(valid.sum()),height_range_for_counts_kpc=[.15,1.],
        hemisphere_pair_bins=len(centres),counts_in_compared_bins=int(folded.sum()),
        global_tracer_weights_per_Msun=c.tolist(),normalization_parameters=2,
        geometry_only_folded_count_poisson_deviance=deviance,
        max_abs_raw_count_asymmetry=float(np.max(abs(asym))),
        RVS_global_offset_kms=v0,RVS_constant_model_diagonal_chi2=float(np.sum(ww*(vv-v0)**2)),
        full_selection_corrected=False,population_mapping_verified=False,
        result='Sample-level forward comparison only; full star-count validation gate remains open.'),
    no_per_bin_tuning=True,no_gravity_parameter_refit=True,
    full_star_count_and_velocity_validation_passed=False)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
fig,ax=plt.subplots(2,2,figsize=(10,7),layout='constrained')
ax[0,0].errorbar(centres,folded,yerr=np.sqrt(folded),fmt='o',ms=3,label='Gaia DR3 selected counts')
ax[0,0].plot(centres,mu,label='Fixed DF + two global tracer weights')
ax[0,0].set(yscale='log',xlabel='|z| [kpc]',ylabel='Folded star counts / bin');ax[0,0].legend(fontsize=7)
ax[0,1].errorbar(centres,asym,yerr=asymerr,fmt='o',ms=3,label='Direct DR3 selected sample')
ax[0,1].axhline(0,color='black',ls='--',label='Reflected equilibrium')
ax[0,1].set(xlabel='|z| [kpc]',ylabel='North-South count asymmetry');ax[0,1].legend(fontsize=7)
ax[1,0].errorbar(a[0],a[1],yerr=a[2],fmt='o',ms=3)
ax[1,0].axhline(0,color='black',ls='--');ax[1,0].set(xlabel='|z| [kpc]',ylabel='Published Gaia DR2 count asymmetry')
ax[1,1].errorbar(v[0],v[1],yerr=v[2],fmt='o',ms=3)
ax[1,1].axhline(offset,color='black',ls='--');ax[1,1].set(xlabel='Published height coordinate [kpc]',ylabel='Published median W [km/s]')
fig.suptitle('Actual Gaia comparisons: equilibrium background and remaining perturbations',fontsize=12)
fig.savefig(OUT/'gaia_comparison.png',dpi=180);plt.close(fig)
print(json.dumps(summary,indent=2),flush=True)
