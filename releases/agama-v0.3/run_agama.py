from pathlib import Path
import argparse,csv,json,math,platform,time,sys
import numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import *

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--refined',action='store_true')
parser.add_argument('--iterations',type=int,default=20)
args=parser.parse_args()
tag='refined' if args.refined else 'base'
OUT=HERE/('results_'+tag);OUT.mkdir(exist_ok=True)
checks=[]
def check(name,value,limit,lower=False):
    checks.append(dict(name=name,value=float(value),limit=float(limit),pass_=bool(value>=limit if lower else value<=limit)))
def savecsv(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def moment_rows(pot,df,af=None):
    z=np.array([0,.1,.3,.6,1.1,1.5,2.])
    x=np.column_stack([np.full_like(z,8.2),z*0,z])
    gm=agama.GalaxyModel(pot,df) if af is None else agama.GalaxyModel(pot,df,af)
    den,vel,v2=gm.moments(x,dens=True,vel=True,vel2=True,separate=True,relError=1e-4,maxNumEval=1000000)
    rows=[]
    for i,zz in enumerate(z):
        for j,comp in enumerate(['thin','thick']):
            rows.append(dict(z_kpc=zz,component=comp,rho_Msun_pc3=den[i,j]/1e9,
                    vphi_kms=vel[i,j,1],sigmaR_kms=np.sqrt(v2[i,j,0]-vel[i,j,0]**2),
                    sigmaPhi_kms=np.sqrt(v2[i,j,1]-vel[i,j,1]**2),
                    sigmaZ_kms=np.sqrt(v2[i,j,2]-vel[i,j,2]**2)))
    return rows

b,discs,densities,bulge=make_baryons()
response=SphericalResponse(b)
residual=response.potential(grid=450 if args.refined else 300)
initial=agama.Potential(b,residual)
df,dfparams=stellar_df(initial)
(OUT/'df_parameters.json').write_text(json.dumps(dfparams,indent=2))
r=np.linspace(5,25,81);x=np.column_stack([r,r*0,r*0])
gb=-b.force(x)[:,0]
target=gb/np.expm1(np.sqrt(gb*frozen.ACC_CONV/frozen.A_T))
check('initial reconstructed residual force versus prescribed rule',np.max(abs(-residual.force(x)[:,0]/target-1)),5e-5)
regtests=[]
for core,width in [(.005,200),(.02,200),(.01,100),(.01,400)]:
    pr=SphericalResponse(b,core=core,taper_width=width).potential(grid=450 if args.refined else 300)
    change=np.max(abs(pr.force(x)[:,0]/residual.force(x)[:,0]-1))
    regtests.append(dict(core_kpc=core,taper_width_kpc=width,max_radial_force_change=change))
    check(f'regulator local force core={core} outer={width}',change,1e-4)
savecsv('regulator_sensitivity.csv',regtests)
initialmom=moment_rows(initial,df)
savecsv('initial_velocity_density.csv',initialmom)

# Native AGAMA DF/Poisson iteration, with an explicit spherical WRRA response
# update after each DF-density update. DF parameters are never reconstructed.
factor=1.5 if args.refined else 1.
scm=agama.SelfConsistentModel(RminCyl=.1,RmaxCyl=60,sizeRadialCyl=int(48*factor),
        zminCyl=.08,zmaxCyl=8,sizeVerticalCyl=int(40*factor),
        rminSph=.0005,rmaxSph=2500,sizeRadialSph=int(180*factor),
        lmaxAngularSph=0,useActionInterpolation=True)
warm=HERE/'warm_start'
if not warm.exists():
    warm=HERE.parent/'binney_bridge_v0_2'/'results_refined'
warmdensity=agama.Density(str(warm/'final_stellar_density.ini'))
residual=agama.Potential(str(warm/'residual_multipole.ini'))
scm.components.append(agama.Component(df=df,density=warmdensity,disklike=True,relError=1e-4,maxNumEval=1000000,
        RminCyl=.15,RmaxCyl=40,sizeRadialCyl=int(24*factor),
        zminCyl=.06,zmaxCyl=6,sizeVerticalCyl=int(20*factor)))
static=agama.Potential(discs[2],discs[3],bulge)
scm.components.append(agama.Component(potential=static))
scm.components.append(agama.Component(potential=residual))

class BaryonicField:
    def __init__(self,total,residual): self.total,self.residual=total,residual
    def force(self,x):return self.total.force(x)-self.residual.force(x)

probes=np.array([[R,0,z] for R in [5,8.2,12,20,25] for z in [0,.3,1.1,2.]])
history=[];previous_force=None;previous_density=None;consecutive=0
for iteration in range(1,args.iterations+1):
    start=time.time()
    scm.iterate()
    pot=scm.potential
    # The residual currently in the potential was built from the previous
    # baryonic state. Re-evaluate the same constitutive rule for the new state.
    bf=BaryonicField(pot,residual)
    newresponse=SphericalResponse(bf)
    newresidual=newresponse.potential(grid=450 if args.refined else 300)
    force=pot.force(probes)
    density=scm.components[0].density.density(probes)
    fchange=np.max(np.linalg.norm(force-previous_force,axis=1)/np.maximum(np.linalg.norm(force,axis=1),1)) if previous_force is not None else float('inf')
    dchange=np.max(abs(density/previous_density-1)) if previous_density is not None else float('inf')
    rchange=np.max(abs(newresidual.force(x)[:,0]/residual.force(x)[:,0]-1))
    vc=float(np.sqrt(-pot.force([8.2,0,0])[0]*8.2))
    kz=float(-pot.force([8.2,0,1.1])[2]/(2*math.pi*G)/1e6)
    row=dict(iteration=iteration,seconds=time.time()-start,force_change=fchange,
             stellar_density_change=dchange,residual_update_change=rchange,
             vc_solar_kms=vc,Kz11_equiv_Msun_pc2=kz,
             stellar_density_solar_Msun_pc3=float(scm.components[0].density.density([8.2,0,0])/1e9))
    history.append(row);savecsv('iteration_history.csv',history)
    savecsv('density_probes_iter_%02d.csv'%iteration,[dict(R_kpc=float(pt[0]),z_kpc=float(pt[2]),rho_Msun_pc3=float(dd/1e9)) for pt,dd in zip(probes,density)])
    print(json.dumps(row),flush=True)
    previous_force,previous_density=force,density
    # Demand two successive iterations; report an unclosed result if this fails.
    if max(fchange,dchange,rchange)<.002:consecutive+=1
    else:consecutive=0
    if consecutive>=2:break
    if iteration<args.iterations:
        residual=newresidual
        scm.components[2]=agama.Component(potential=residual)

converged=consecutive>=2
final=scm.potential
final.export(str(OUT/'final_potential.ini'))
scm.components[0].density.export(str(OUT/'final_stellar_density.ini'))
savecsv('final_velocity_density.csv',moment_rows(final,df,scm.af))
check('two successive coupled fixed-point iterations below 0.2 percent',max(history[-1]['force_change'],history[-1]['stellar_density_change'],history[-1]['residual_update_change']),.002)

# Residual finite-difference density and direct DF moments vs the SCM density
# interpolation are separate numerical checks of the actual exported model.
check('residual positive sampled density',np.min(residual.density(probes)),0,lower=True)
dm=agama.GalaxyModel(final,df) # direct action evaluation
dmden=dm.moments(probes,dens=True,vel=False,vel2=False,relError=1e-4,maxNumEval=1000000)
interpden=scm.components[0].density.density(probes)
check('DF moments versus final SCM density interpolation max relative',np.max(abs(dmden/interpden-1)),.05)

# Orbits in the actual final potential; Lz and energy are true invariants.
# Actions other than Lz use the axisymmetric Staeckel approximation.
orbitmetrics=[];orbittraces=[]
af=agama.ActionFinder(final)
for i,(R,z,vR,vz) in enumerate([(5,.05,10,10),(8.2,.1,20,20),(12,.2,-20,30),(20,.4,15,20)]):
    vphi=float(np.sqrt(-final.force([R,0,0])[0]*R))
    ic=[R,0,z,vR,vphi,vz]
    period=2*math.pi*R/vphi
    t,orb=agama.orbit(potential=final,ic=ic,time=10*period,trajsize=1001,accuracy=1e-10,dtype=float)
    energy=final.potential(orb[:,:3])+np.sum(orb[:,3:]**2,axis=1)/2
    Lz=orb[:,0]*orb[:,4]-orb[:,1]*orb[:,3]
    es=float(np.max(abs(energy-energy[0]))/max(np.sum(np.array(ic[3:])**2)/2,1))
    ls=float(np.max(abs(Lz/Lz[0]-1)))
    a=af(orb[::10])
    drift=np.ptp(a,axis=0)/np.maximum(np.mean(a,axis=0),1e-12)
    orbitmetrics.append(dict(orbit=i,R_initial_kpc=R,time_internal=float(t[-1]),
               periods=10,energy_error_scaled=es,Lz_relative_error=ls,
               Jr_relative_range=float(drift[0]),Jz_relative_range=float(drift[1]),
               Jphi_relative_range=float(drift[2]),zmax_kpc=float(np.max(abs(orb[:,2])))))
    check(f'orbit {i} energy conservation',es,1e-6)
    check(f'orbit {i} angular momentum conservation',ls,1e-7)
    for tt,xx in zip(t[::5],orb[::5]):
        orbittraces.append(dict(orbit=i,time=float(tt),x=xx[0],y=xx[1],z=xx[2],vx=xx[3],vy=xx[4],vz=xx[5]))
savecsv('orbit_metrics.csv',orbitmetrics);savecsv('orbit_traces.csv',orbittraces)

rad,vf,zz,kf=diagnostics(final)
_,vi,_,ki=diagnostics(initial)
savecsv('rotation_final.csv',[dict(R_kpc=R,vc_initial_kms=v0,vc_final_kms=v) for R,v0,v in zip(rad,vi,vf)])
savecsv('vertical_force_final.csv',[dict(z_kpc=z,Kz_initial_equiv_Msun_pc2=k0/(2*math.pi*G)/1e6,Kz_final_equiv_Msun_pc2=k/(2*math.pi*G)/1e6) for z,k0,k in zip(zz,ki,kf)])
savecsv('checks.csv',checks)
summary=dict(version='0.3',run=tag,agama_version=agama.__version__,G=G,
    converged=converged,iterations=len(history),last_iteration=history[-1],
    checks_passed=sum(c['pass_'] for c in checks),checks_total=len(checks),
    initial_vc_solar=float(np.sqrt(-initial.force([8.2,0,0])[0]*8.2)),
    initial_Kz11_equiv=float(-initial.force([8.2,0,1.1])[2]/(2*math.pi*G)/1e6),
    initial_residual_rho_solar=float(response.density(np.array([[8.2,0,0]]))[0]/1e9),
    initial_stellar_midplane_rho=float(agama.Density(*densities[:2]).density([8.2,0,0])/1e9),
    final_residual_rho_solar=float(residual.density([8.2,0,0])/1e9),
    fixed_df_parameters=dfparams,orbit_metrics=orbitmetrics,
    stage='precision-controlled coupled DF-Poisson and spherical WRRA response; warm-started from v0.2',
    DF_density_relError=1e-4,DF_density_maxNumEval=1000000,vertical_potential_grid_min_kpc=.08,
    observational_likelihood_run=False,python=platform.python_version())
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
fig,ax=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
ax[0].plot(rad,vi,label='Finite-height initial');ax[0].plot(rad,vf,label='Coupled DF iteration');ax[0].set(xlabel='R [kpc]',ylabel='Circular speed [km/s]');ax[0].legend(fontsize=8)
ax[1].plot(zz,ki/(2*math.pi*G)/1e6,label='Initial');ax[1].plot(zz,kf/(2*math.pi*G)/1e6,label='Final');ax[1].set(xlabel='z [kpc] at R=8.2',ylabel='Kz/(2 pi G) [Msun/pc^2]');ax[1].legend(fontsize=8)
for key,label in [('force_change','Total force'),('stellar_density_change','Stellar density'),('residual_update_change','WRRA field update')]:
    ax[2].semilogy([h['iteration'] for h in history[1:]],[h[key] for h in history[1:]],label=label)
ax[2].axhline(.002,color='black',lw=.6,ls='--');ax[2].set(xlabel='Iteration',ylabel='Maximum relative change');ax[2].legend(fontsize=7)
fig.suptitle('Actual AGAMA run: fixed DFs with updated spherical WRRA response')
fig.savefig(OUT/'agama_diagnostics.png',dpi=180);plt.close(fig)
print(json.dumps(summary,indent=2),flush=True)
if not all(c['pass_'] for c in checks):raise SystemExit('One or more verification gates failed; see checks.csv')
