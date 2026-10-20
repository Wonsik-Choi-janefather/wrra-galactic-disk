from pathlib import Path
import json,html,math,argparse
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',default=str(HERE/'reports'))
args=parser.parse_args()
OUT=Path(args.output_dir);OUT.mkdir(parents=True,exist_ok=True)
PDF=OUT/'WRRA_AGAMA_v0_3_Binney_Report_EN.pdf'
b=json.loads((HERE/'results_base/summary.json').read_text())
r=json.loads((HERE/'results_refined/summary.json').read_text())
v=json.loads((HERE/'validation/summary.json').read_text())
e=json.loads((HERE/'validation/additional_checks.json').read_text())
o=json.loads((HERE/'observations/summary.json').read_text())
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVu-Bold',italic='DejaVu',boldItalic='DejaVu-Bold')
NAVY=colors.HexColor('#17354b');TEAL=colors.HexColor('#167c80');PALE=colors.HexColor('#edf4f6')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Main',fontName='DejaVu',fontSize=9,leading=13,spaceAfter=7,textColor=NAVY))
styles.add(ParagraphStyle(name='SmallMain',parent=styles['Main'],fontSize=7.9,leading=11,spaceAfter=5))
styles.add(ParagraphStyle(name='TitleMain',parent=styles['Main'],fontName='DejaVu-Bold',fontSize=19,leading=23,spaceAfter=9))
styles.add(ParagraphStyle(name='SectionMain',parent=styles['Main'],fontName='DejaVu-Bold',fontSize=11,leading=15,spaceBefore=9,spaceAfter=6,textColor=TEAL))
styles.add(ParagraphStyle(name='CellMain',parent=styles['Main'],fontSize=8.1,leading=11,spaceAfter=0))
styles.add(ParagraphStyle(name='CellWhite',parent=styles['CellMain'],textColor=colors.white,fontName='DejaVu-Bold'))
def P(s,style='Main'):return Paragraph(s,styles[style])
def table(rows,widths,header=True):
    data=[[P(str(x),'CellWhite' if i==0 and header else 'CellMain') for x in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1 if header else 0)
    spec=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#c9d8df'))]
    if header:spec += [('BACKGROUND',(0,0),(-1,0),NAVY)]
    for i in range(1 if header else 0,len(rows)):
        if i%2:spec.append(('BACKGROUND',(0,i),(-1,i),PALE))
    t.setStyle(TableStyle(spec));return t
def footer(c,doc):
    c.setFont('DejaVu',7)
    c.setFillColor(colors.HexColor('#657681'))
    c.drawString(42,27,'Wonsik Choi | WRRA-AGAMA v0.3-dev | 20 October 2026')
    c.drawRightString(A4[0]-42,27,str(doc.page))
story=[]
story += [P('WRRA-AGAMA v0.3','TitleMain'),P('Numerical closure and a first Gaia sample comparison','SectionMain'),P('Wonsik Choi | Independent researcher, Seoul | 20 October 2026','SmallMain')]
story.append(P('<b>Scope:</b> actual stellar distribution-function and Poisson iteration, followed by public Gaia comparisons. Numerical convergence is demonstrated at two resolutions. Full joint star-count and velocity validation is <b>not yet established</b>.'))
story.append(table([
 ['Assessment stage','What was actually calculated'],
 ['Validation inputs','Original Galactic-disk masses and radial scales; literature finite heights; explicit, fixed trial stellar DFs. A direct Gaia DR3 sample is used for a subsequent comparison.'],
 ['WRRA transformation','At each baryonic state, apply the prescribed WRRA residual response; reconstruct its spherical effective density and potential; update the live stellar f(J) and repeat.'],
 ['Outputs','Converged forces and local densities at two resolutions; orbit and Jeans diagnostics; actual selected Gaia star counts and vertical velocities.'],
 ['Falsification conditions','Non-positive source, non-convergence, grid sensitivity, invariant violation, or disagreement with properly matched observational tracers and selection.'],
 ],[104,407]))
story += [P('Fixed physical specification; improved numerical controls','SectionMain'),P('The scale a_T = 1.191812669 x 10^-10 m/s^2 and the original constitutive response are retained. Gas and bulge are static; two stellar QuasiIsothermal DFs are live. Initial stellar heights are 0.3/0.9 kpc; gas sech-squared scale parameters are 0.085/0.045 kpc. The trial radial-dispersion amplitudes are 35/55 km/s at 8.2 kpc. These DF choices are explicit model inputs, not new measurements or microscopic derivations. The spatial residual closure is spherical.'),P('The Python interface was extended to expose AGAMA\'s existing internal integration controls; the physical formulae were unchanged. Density integration uses relative tolerance 10^-4 and up to 10^6 evaluations. The stellar potential grid begins at z = 0.08 kpc. Both runs start from the stored v0.2 density and perform five additional iterations, satisfying the 0.2% local criterion twice consecutively. The patch and warm-start inputs are included.','SmallMain')]
story.append(table([
 ['At R = 8.2 kpc','Base grid','Refined grid'],
 ['Additional warm-start iterations / checks','5 / 16 of 16','5 / 16 of 16'],
 ['Circular speed [km/s]',f"{v['base']['vc_solar_kms']:.5f}",f"{v['refined']['vc_solar_kms']:.5f}"],
 ['Kz(1.1 kpc)/(2 pi G) [Msun/pc^2]',f"{v['base']['Kz11_equivalent_Msun_pc2']:.5f}",f"{v['refined']['Kz11_equivalent_Msun_pc2']:.5f}"],
 ['True column within |z| = 1.1 kpc [Msun/pc^2]',f"{v['base']['true_column_11_Msun_pc2']:.5f}",f"{v['refined']['true_column_11_Msun_pc2']:.5f}"],
 ['Total midplane Poisson density [Msun/pc^3]',f"{v['base']['midplane_total_density_Msun_pc3']:.7f}",f"{v['refined']['midplane_total_density_Msun_pc3']:.7f}"],
 ],[285,113,113]))
story.append(P('Kz/(2 pi G) is a force-equivalent surface density; it is not the integrated mass column. Their difference retains the radial term of the cylindrical Poisson equation. Displayed digits support reproduction and do not represent observational accuracy.','SmallMain'))
story.append(PageBreak())
story += [P('Numerical checks and actual Gaia data','TitleMain')]
story.append(P(f"Across the two grids, the maximum force difference on 20 probes is <b>{v['max_force_change_refined_vs_base']*100:.4f}%</b>; circular speeds differ by at most <b>{v['max_vc_change_refined_vs_base']*100:.4f}%</b> over 5-25 kpc. Total midplane density differs by <b>{e['total_midplane_density_grid_change']*100:.4f}%</b>, resolving the earlier numerical sensitivity. Four test orbits each cover ten nominal periods and pass energy and axial-angular-momentum checks. A sampled direct-moment Jeans residual is at most {v['jeans_max_relative_residual']*100:.2f}%; approximate actions are not exact invariants."))
story.append(table([
 ['ESA Gaia DR3 sample','Retrieved / compared'],
 ['Explicit archive selection','Cylinder radius 0.25 kpc; G = 7-17; BP-RP = 1.0-1.4; uncorrected absolute G = 5-6; parallax S/N above 10; RUWE below 1.4.'],
 ['Retrieved stars / with radial velocities','90,113 / 72,603'],
 ['RV uncertainty below 3 km/s','48,794 stars'],
 ['Count comparison','79,716 stars in 17 paired height bins, |z| = 0.15-1.0 kpc. Two global tracer weights fitted; no gravity refit or per-bin adjustment.'],
 ],[170,341]))
story.append(Spacer(1,7))
story.append(Image(str(HERE/'observations/gaia_comparison.png'),width=493,height=345.1))
story.append(P('Upper panels: directly retrieved Gaia DR3 counts and raw sample asymmetry. The geometry-only fixed-DF count template does not fit the selected counts; its Poisson deviance is 1747.2 after two global weights. Lower panels: independent author-released Gaia DR2 perturbation tables from Bennett &amp; Bovy. These comparisons use different selections and are not combined into a joint likelihood.','SmallMain'))
story.append(PageBreak())
story += [P('Interpretation and review boundary','TitleMain')]
story.append(table([
 ['Claim','Supported status'],
 ['Actual potential-density/AGAMA implementation','Yes. The prescribed WRRA response, density inversion, stellar DF and Poisson iteration are executed.'],
 ['Density convergence at both tested resolutions','Yes, on the stated probes and numerical tests. No continuum or global theorem is claimed.'],
 ['An unchanged frozen field during iteration','No. The field evolves; the response law and DF parameters remain fixed.'],
 ['Zero added physical assumptions','No. Finite thickness, trial DFs, spherical closure and global boundary regularization are explicitly adopted.'],
 ['Star counts and vertical velocities fully validated','No. The selected count profile is not reproduced by the current template, full selection/population mapping is open, and vertical perturbations are absent from this equilibrium background.'],
 ],[179,332]))
story += [P('What the observational comparison establishes','SectionMain'),P('Mass density is not itself a star count. The current geometry-only conversion fits two global population weights but does not forward-model extinction, luminosity-colour distributions, RUWE cuts or the full Gaia/RVS completeness. Its count-profile discrepancy cannot yet be assigned uniquely to gravity. A population-matched tracer DF and a verified selection function are required.'),P('The reflected equilibrium background predicts zero North-South asymmetry and zero vertical streaming. The published DR2 table contains count asymmetries reaching 9.92%. Diagonal residual sums are 1692.2 for 31 count-asymmetry bins and 437.0 for 50 velocity bins after one global velocity offset. Covariance is not supplied, so no formal joint significance is claimed. The same limitation applies to a conventional reflected equilibrium control. This is a missing perturbation sector, not a unique test of WRRA against standard gravity.'),P('The initial finite-height circular speed is 222.16 km/s; the coupled result is about 215.62 km/s. The live stellar DF changes the initially specified spatial density. The old linearized rotation reference has RMS difference about 5.18 km/s over 8.25-25 kpc; it is not an individual-data likelihood.')]
story += [P('Concrete next steps','SectionMain'),P('1. Forward-model the selected stellar populations and Gaia/RVS selection, then calibrate the tracer DF against density and dispersion data.<br/>2. Test a fixed calibrated model on held-out observables.<br/>3. Add and test a physically specified non-equilibrium sector if the goal includes the measured vertical waves. Calibration to verified observations is legitimate; it must remain explicit.')]
story += [P('Sources and reproduction','SectionMain')]
refs=[
 'AGAMA source: GalacticDynamics-Oxford/Agama, commit f302756b8af2b763db58e278e30478517dc8eea3, plus the included precision-control interface patch.',
 'WRRA radial model: Wonsik-Choi-janefather/wrra-galactic-disk, commit 2528be62a70c1579308389621e75988f1f777c82. Upstream manuscript: doi.org/10.5281/zenodo.23003875.',
 'Gaia DR3: ESA Gaia Archive, gaiadr3.gaia_source; full ADQL query, raw public-source rows and checksums included. Gaia DR3 overview: doi.org/10.1051/0004-6361/202243940.',
 'Bennett &amp; Bovy: arxiv.org/abs/1809.03507; author repository morganb-phys/VWaves-GaiaDR2, commit 203c2e111c24b99351871e562d4efe193fed586b.',
 'Finite-height model family: McMillan (2017), doi.org/10.1093/mnras/stw2759, and official AGAMA data/McMillan17.ini. The full McMillan model is not copied.'
]
for ref in refs:story.append(P(ref,'SmallMain'))
doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=35,bottomMargin=42,title='WRRA-AGAMA v0.3: numerical closure and a first Gaia sample comparison',author='Wonsik Choi')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(PDF)
