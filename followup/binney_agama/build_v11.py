from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV",normal="DV",bold="DV-Bold",italic="DV",boldItalic="DV-Bold")
from pypdf import PdfReader,PdfWriter
root=Path(__file__).resolve().parents[2]; here=Path(__file__).resolve().parent
out=root/'papers'; r=json.loads((here/'fallback_results.json').read_text())
s=getSampleStyleSheet();s['BodyText'].fontName='DV';s['Heading2'].fontName='DV-Bold';s['BodyText'].fontSize=9;s['BodyText'].leading=13
story=[]
def p(t):story.append(Paragraph(t,s['BodyText']));story.append(Spacer(1,9))
def h(t):story.append(Paragraph(t,s['Heading2']));story.append(Spacer(1,8))
def table(rows,widths):
    data=[[Paragraph(escape(str(c)),s['BodyText']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.lightgrey),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t)
h('Version 1.1 - computational follow-up and preserved v1.0 manuscript')
p('<b>WRRA Spatial-Twist Selection of Galactic Disk Planes and the Dark-Mass Phenotype</b>')
p('Wonsik Choi | Independent Researcher, Seoul, Republic of Korea<br/>janefather@gmail.com | ORCID: 0009-0001-4263-9772<br/>5 October 2026')
p('This edition adds a methodological and computational addendum, then reproduces the original twelve-page English manuscript unchanged. Its embedded v1.0 dates and conclusion describe that earlier release. The new results below supersede only the follow-up implementation status; the original calibration is preserved.')
h('Evaluation before conclusion')
table([['Stage','Evidence in this edition'],['Validation input','Original radial baryonic model, a_T and response; explicitly declared spherical additional-field and local 1D diagnostic assumptions. No new observation samples.'],['WRRA transformation','Frozen g_T -> bounded potential, force and effective density -> local vertical Hamiltonian, action quadrature, tracer DF moments.'],['Outputs','Numerical Poisson, force, orbit energy, action-period and local Jeans checks pass. Parent circular speeds retained.'],['Falsification','Numerical inconsistency; later failure to match radial/vertical/count observations with one frozen response; independent force refitting.']], [3.5*cm,13*cm])
p('<b>Conclusion:</b> an executable local diagnostic now exists without AGAMA. This is neither a self-consistent 3D disk nor a Gaia validation.')
h('Acknowledgement')
p('The author thanks James Binney for suggesting an AGAMA-based route involving potential-density consistency, action-based disk distribution functions, stellar velocities and solar-neighbourhood distributions in correspondence received on 5 October 2026. This methodological summary is author-reported; the email has not been independently inspected. Binney indicated he had no time to participate. This credits advice, not coauthorship, participation, endorsement or completed validation. No private correspondence is reproduced.')
story.append(PageBreak())
h('1. Interface definition and calibration ledger')
p('Poisson inversion rho_eff = Laplacian(Phi)/(4 pi G) returns the effective gravitating source of a specified smooth potential. It does not return star counts. For a total Phi it returns total source density; for the twist-only Phi used here it returns effective twist density.')
p('A constitutive WRRA response C[Phi_total, rho_b, T_fixed] needed for self-consistent iteration is a different operator and remains undefined in v1.0. Repeated Poisson inversion alone is not a new self-consistency test. The midplane radial curve does not uniquely fix off-plane derivatives: adding z^2 h(R) leaves its radial force unchanged while changing vertical force and density.')
p('The diagnostic explicitly imposes spherical symmetry for the additional field: r = sqrt(R^2+z^2); Phi_T(r) = integral from 25 to r of g_T(s) ds; F_T = -g_T(r) x/r; rho_T,eff = [g_T\'(r)+2g_T(r)/r]/(4 pi G). This uses the existing spherical-equivalent mass ledger but adds a declared symmetry assumption, not a derivation of q_T.')
p('Supported spherical radii: 5-25 kpc, with no extrapolation. Phi_T(25)=0 is a derivative-test gauge, not an escape-energy convention. G=4.30091e-6 kpc (km/s)^2 per solar mass. Potential: (km/s)^2; density: solar masses/kpc^3.')
table([['Item','Policy'],['a_T = 1.191812669e-10 m/s^2; response nu','Frozen parent values'],['Parent baryonic masses and radial scales','Unchanged radial input model'],['Spherical additional field; fixed R=8.2 kpc; vertical cutoff 2 kpc','New diagnostic assumptions; not fitted to data'],['Tracer sigma=10,20 km/s','Demonstration inputs; same field for both'],['3D q_T closure, finite-thickness baryonic field, global boundary','Still required before full disk validation']], [6*cm,10.5*cm])
p('Self-gravitating DF changes affect baryonic density and total potential. A fixed WRRA law must be applied again to those sources and radial residuals logged. A tracer fit in a fixed potential is distinct from this iteration. Independent radial and vertical force amplitudes are not allowed in the joint test.')
story.append(PageBreak())
h('2. Executed SciPy fallback: local vertical action and equilibrium')
p('AGAMA compilation failed in the Python-library linkage probe. The installed libpython link points to a missing runtime location. A portable SciPy fallback runs quadrature, root finding and solve_ivp instead; the unexecuted AGAMA callback is not counted as a result.')
p('At fixed R=8.2 kpc define Psi(z)=Phi_T(sqrt(R^2+z^2))-Phi_T(R), E_z=v_z^2/2+Psi(z). The auxiliary one-dimensional system holds R fixed and omits radial-vertical coupling and baryonic vertical gravity. Its J_z is the action of this auxiliary Hamiltonian, not the full 3D Galactic action.')
p('J_z(E)=(2/pi) integral from 0 to z_turn of sqrt[2(E-Psi(z))] dz. The period is 4 integral dz/sqrt[2(E-Psi)]. Turning-point quadrature uses z=z_turn sin(theta). The independent identity dJ_z/dE = period/(2 pi) and four-period energy conservation are checked.')
table([['Turning height (kpc)','J_z (kpc km/s)','dJ/dE check','Energy drift']]+[[x['zmax_kpc'],f"{x['Jz_kpc_km_s']:.8f}",f"{x['dJdE_period_relative_error']:.2e}",f"{x['four_period_energy_relative_drift']:.2e}"] for x in r['orbit_action_checks']], [4*cm,4.5*cm,4*cm,4*cm])
p('Tracer demonstration: F(E)=exp(-E/sigma^2) for E below E_cut, zero otherwise; E_cut=Psi(2 kpc)=522.7022999 (km/s)^2. Since J(E) is monotone this also defines F(J)=exp[-E(J)/sigma^2]. The energy cutoff confines support to the diagnostic domain and is not an observed disk edge. These are normalized local relative profiles, not absolute number-count predictions.')
p('Velocity moments are integrated over the allowed finite velocity interval. Numerical velocity PDFs integrate to unity; the local Jeans identity d(n sigma_vz^2)/dz = n F_z is checked at z=0.5 kpc. The two DF parameters change tracer distributions while leaving the same gravity untouched. In the cutoff model input sigma is not identical to the resulting measured dispersion.')
story.append(PageBreak())
h('3. Results, limitations and next validation gates')
table([['Input sigma','n(1 kpc)/n(0)','sigma_vz(0)','Jeans relative error']]+[[t['input_sigma_km_s'],f"{t['profile'][-1]['relative_tracer_density']:.6f}",f"{t['profile'][0]['sigma_vz_km_s']:.6f} km/s",f"{t['vertical_Jeans_relative_error_at_z_0_5']:.2e}"] for t in r['tracer_DFs']], [3*cm,4.5*cm,4.5*cm,4.5*cm])
p('Original total circular speeds: 226.341399 km/s at 8.2 kpc and 201.588942 km/s at 25 kpc. Force-gradient relative error is 1.51e-9; Poisson inversion maximum relative error is 1.02e-6 at 0.01 kpc step. Independent analytic Plummer inversion error is 5.32e-6. Positive effective density was checked at 80 sample radii, not proved globally.')
p('The fallback replaces only the immediate local action/orbit/moment diagnostic. It does not replace the full AGAMA multicomponent self-consistent solver. It does not implement finite-thickness baryonic vertical force, the q_T constitutive closure, warp dynamics, survey selection, stellar population conversions or observational likelihoods. Agreement with a constructed equilibrium is an implementation result, not an observational success.')
p('Next: (1) specify finite-thickness baryonic sources and global boundaries; (2) declare and freeze the 3D WRRA response; (3) run full action-DF and source-potential iterations with convergence and Poisson residuals; (4) incorporate Gaia RVS selection, uncertainties, solar motion and asymmetric drift; (5) jointly test V_c, vertical velocity distributions, K_z and solar-neighbourhood star counts. Assess the time-dependent non-axisymmetric warp separately.')
h('References and reproducibility')
p('[1] Binney, J. (2010). Distribution functions for the Milky Way. MNRAS 401, 2318-2330. DOI: 10.1111/j.1365-2966.2009.15845.x. This motivates the action-based vertical DF layer; it is not a WRRA output.')
p('[2] Vasiliev, E. (2019). AGAMA: action-based galaxy modelling architecture. MNRAS 482, 1525-1544. DOI: 10.1093/mnras/sty2672. AGAMA provides the full architecture, not executed here.')
p('[3] Choi, W. (2026). Parent v1.0 preprint. DOI: 10.5281/zenodo.23003875. Repository: https://github.com/Wonsik-Choi-janefather/wrra-galactic-disk. Parent source commit: 2528be62a70c1579308389621e75988f1f777c82.')
p('Commands: python followup/binney_agama/run_minimal.py; python followup/binney_agama/fallback_vertical.py. NumPy 2.3.5 and SciPy 1.17.0. Source, results JSON, ledger and this edition builder are included in the reproducibility archive. Existing GitHub PR: https://github.com/Wonsik-Choi-janefather/wrra-galactic-disk/pull/1.')
def footer(c,d):
    c.setFont('DV',8);c.drawString(2*cm,1.2*cm,'WRRA Galactic Disk v1.1 | Computational addendum');c.drawRightString(19*cm,1.2*cm,f'Addendum {d.page}')
appendix=out/'WRRA_Galactic_Disk_v1_1_Addendum_EN.pdf'
SimpleDocTemplate(str(appendix),pagesize=(21*cm,29.7*cm),rightMargin=2*cm,leftMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm).build(story,onFirstPage=footer,onLaterPages=footer)
w=PdfWriter()
for file in (appendix,out/'WRRA_Galactic_Disk_EN.pdf'):
    w.append(str(file))
w.add_metadata({'/Title':'WRRA Galactic Disk v1.1: preserved v1.0 with computational follow-up','/Author':'Wonsik Choi'})
w.write(str(out/'WRRA_Galactic_Disk_v1_1_EN.pdf'))
print('addendum pages',len(PdfReader(appendix).pages))
