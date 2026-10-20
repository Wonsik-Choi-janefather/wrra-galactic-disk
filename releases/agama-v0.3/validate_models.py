"""Post-run comparisons and explicit equilibrium/observation diagnostics."""
from pathlib import Path
import csv,json,math
import numpy as np
from scipy.integrate import quad
from model import *

HERE=Path(__file__).resolve().parent
out=HERE/'validation';out.mkdir(exist_ok=True)
base=load_final_potential(HERE/'results_base')
ref=load_final_potential(HERE/'results_refined')
xb=np.array([[R,0,z] for R in [5,8.2,12,20,25] for z in [0,.3,1.1,2]])
fb,fr=base.force(xb),ref.force(xb)
fieldchange=float(np.max(np.linalg.norm(fr-fb,axis=1)/np.linalg.norm(fr,axis=1)))
rad=np.linspace(5,25,81);x=np.column_stack([rad,rad*0,rad*0])
vb=np.sqrt(-rad*base.force(x)[:,0]);vr=np.sqrt(-rad*ref.force(x)[:,0])
rotchange=float(np.max(abs(vr/vb-1)))

summary=dict(max_force_change_refined_vs_base=fieldchange,
             max_vc_change_refined_vs_base=rotchange,
             force_refinement_gate_1percent=fieldchange<.01,
             rotation_refinement_gate_half_percent=rotchange<.005,
             observation_fit_performed=False)
for name,p in [('base',base),('refined',ref)]:
    saved=np.genfromtxt(HERE/f'results_{name}/rotation_final.csv',delimiter=',',names=True)
    xxx=np.column_stack([saved['R_kpc'],saved['R_kpc']*0,saved['R_kpc']*0])
    reloaderror=float(np.max(abs(np.sqrt(-saved['R_kpc']*p.force(xxx)[:,0])/saved['vc_final_kms']-1)))
    column=2*quad(lambda z:float(p.density([8.2,0,z])),0,1.1,epsabs=1e-4,epsrel=1e-8)[0]/1e6
    summary[name]=dict(vc_solar_kms=float(np.sqrt(-p.force([8.2,0,0])[0]*8.2)),
            Kz11_equivalent_Msun_pc2=float(-p.force([8.2,0,1.1])[2]/(2*math.pi*G)/1e6),
            true_column_11_Msun_pc2=column,midplane_total_density_Msun_pc3=float(p.density([8.2,0,0])/1e9),export_reload_rotation_relative_error=reloaderror)
    if reloaderror>1e-7:raise ValueError('Export/reload force mismatch')

# Jeans diagnostic uses actual directly evaluated DF moments in the exported
# potential. It is diagnostic, not silently folded into an observational fit.
b,_,_,_=make_baryons();p0=agama.Potential(b,SphericalResponse(b).potential(grid=300))
df,_=stellar_df(p0)
initial_column=2*quad(lambda z:float(p0.density([8.2,0,z])),0,1.1,epsabs=1e-4,epsrel=1e-8)[0]/1e6
summary['initial_true_column_11_Msun_pc2']=initial_column
summary['linearized_rotation_target_diagnostic']={
    'target':'229-1.7*(R-8.2) km/s; original linearized Eilers reference, not data likelihood',
    'range_kpc':[8.25,25],
    'base_RMS_kms':float(np.sqrt(np.mean((vb[rad>=8.25]-(229-1.7*(rad[rad>=8.25]-8.2)))**2))),
    'refined_RMS_kms':float(np.sqrt(np.mean((vr[rad>=8.25]-(229-1.7*(rad[rad>=8.25]-8.2)))**2)))
}
gm=agama.GalaxyModel(ref,df)
rows=[]
for hz in [.08,.04]:
    hr=4*hz
    for z in [.3,.6,1.1]:
        R=8.2
        pts=np.array([[R,0,z],[R,0,z+hz],[R,0,z-hz],[R+hr,0,z],[R-hr,0,z]])
        rho,v2=gm.moments(pts,dens=True,vel=False,vel2=True,relError=1e-4,maxNumEval=1000000)
        dPz=(rho[1]*v2[1,2]-rho[2]*v2[2,2])/(2*hz)
        tilt=(rho[3]*v2[3,4]-rho[4]*v2[4,4])/(2*hr)+rho[0]*v2[0,4]/R
        grav=rho[0]*(-ref.force([R,0,z])[2])
        rows.append(dict(z_kpc=z,hz_kpc=hz,hR_kpc=hr,vertical_pressure=dPz,
                radial_tilt=tilt,gravity_term=grav,Jeans_residual_over_gravity=float((dPz+tilt+grav)/grav)))
with (out/'jeans_diagnostic.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary['jeans_max_relative_residual']=max(abs(r['Jeans_residual_over_gravity']) for r in rows)
summary['Jeans_note']='Staeckel approximate actions and finite-difference cubature diagnostic; no exact collisionless equilibrium claim.'
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
if not (summary['force_refinement_gate_1percent'] and summary['rotation_refinement_gate_half_percent']):
    raise SystemExit('Spatial grid refinement gate failed')
