"""A transparent Gaia DR3 sample for a sample-level star-count diagnostic.

This selection is not silently declared an exact completeness correction.
The public author-released DR2 perturbation tables are separate benchmarks.
"""
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,datetime

HERE=Path(__file__).resolve().parent
OUT=HERE/'data';OUT.mkdir(exist_ok=True)
query="""SELECT source_id,ra,dec,parallax,pmra,pmdec,radial_velocity,radial_velocity_error,
SIN(RADIANS(b))/parallax+0.0208 AS z_kpc,phot_g_mean_mag,bp_rp
FROM gaiadr3.gaia_source
WHERE parallax BETWEEN 0.95 AND 12.5
AND parallax_over_error>10
AND ruwe<1.4
AND phot_g_mean_mag BETWEEN 7 AND 17
AND bp_rp BETWEEN 1.0 AND 1.4
AND phot_g_mean_mag+5*LOG10(parallax)-10 BETWEEN 5 AND 6
AND COS(RADIANS(b))/parallax<0.25
AND SIN(RADIANS(b))/parallax+0.0208 BETWEEN -1 AND 1
AND ABS(SIN(RADIANS(b))/parallax+0.0208)>0.1
"""
(OUT/'gaia_dr3_query.adql').write_text(query)
url='https://gea.esac.esa.int/tap-server/tap/sync?'+urllib.parse.urlencode(
    dict(REQUEST='doQuery',LANG='ADQL',FORMAT='csv',MAXREC=1000000,QUERY=query))
with urllib.request.urlopen(url,timeout=90) as response:
    raw=response.read()
if not raw.startswith(b'source_id,'):
    raise ValueError('Unexpected query response: '+raw[:700].decode(errors='replace'))
(OUT/'gaia_dr3_sample.csv').write_bytes(raw)
meta=dict(archive='ESA Gaia Archive',table='gaiadr3.gaia_source',
    retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    query=query,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw),
    rows=len(raw.splitlines())-1,MAXREC=1000000,
    selection_status='explicit sample; completeness, extinction and population mapping not fully modelled')
if meta['rows']>=meta['MAXREC']:raise ValueError('Possible query truncation')
(OUT/'gaia_dr3_sample_metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({k:v for k,v in meta.items() if k!='query'},indent=2))
