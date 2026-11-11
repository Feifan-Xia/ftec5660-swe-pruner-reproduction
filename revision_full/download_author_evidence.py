"""Download the authors' public 23.9 MB archive through the selected Sakura route."""
import hashlib,json,time,zipfile
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'runs/author_evidence';folder.mkdir(exist_ok=True)
target=folder/'swepruner-sweqa-reproduce.zip'
url='https://drive.usercontent.google.com/download?id=18YPXGHuiqox8zUMt06l9j0nFt_zXMK75&export=download&confirm=t'
if not target.exists():
    with httpx.Client(proxy='http://127.0.0.1:7898',trust_env=False,follow_redirects=True,timeout=httpx.Timeout(90,connect=15)) as client:
        with client.stream('GET',url) as response:
            response.raise_for_status()
            print('Response:',response.status_code,response.headers.get('content-type'),response.headers.get('content-length'),flush=True)
            size=0
            with target.with_suffix('.part').open('wb') as output:
                for block in response.iter_bytes(1024*1024):
                    size+=len(block)
                    assert size<100*1024*1024,'Unexpected archive size'
                    output.write(block);print('Downloaded bytes',size,flush=True)
    assert zipfile.is_zipfile(target.with_suffix('.part')),'Expected a ZIP archive'
    target.with_suffix('.part').replace(target)
with zipfile.ZipFile(target) as archive:
    summary={'files':len(archive.infolist()),'uncompressed_bytes':sum(x.file_size for x in archive.infolist()),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source':url}
    (folder/'provenance.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)
    print(archive.namelist()[:20],flush=True)
