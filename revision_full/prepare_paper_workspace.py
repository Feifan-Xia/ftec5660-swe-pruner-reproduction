"""Restore recorded source-root layout with pinned, source-only repositories."""
import hashlib,io,json,subprocess,tarfile,time,os
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'data/paper-workspace/swe-repos';folder.mkdir(parents=True,exist_ok=True)
manifest=[]
client=httpx.Client(proxy=os.getenv('PAPER_DOWNLOAD_PROXY','http://127.0.0.1:7898') or None,trust_env=False,follow_redirects=True,timeout=httpx.Timeout(90,connect=15))
for owner,name,short in [('conan-io','conan','52f43d9'),('reflex-dev','reflex','fe0f946'),('streamlink','streamlink','ab1f365')]:
    target=folder/name
    if target.exists():
        print('Existing snapshot',name,flush=True);continue
    if name=='streamlink':
        sha=subprocess.check_output(['git','rev-parse',short],cwd=ROOT/'data/streamlink',text=True).strip()
        data=subprocess.check_output(['git','archive',sha],cwd=ROOT/'data/streamlink')
        archive=tarfile.open(fileobj=io.BytesIO(data));target.mkdir()
        archive.extractall(target,filter='data')
    else:
        response=client.get(f'https://codeload.github.com/{owner}/{name}/tar.gz/{short}');response.raise_for_status();data=response.content
        assert len(data)<100*1024*1024
        archive=tarfile.open(fileobj=io.BytesIO(data));target.mkdir()
        sha=archive.pax_headers.get('comment',short)
        prefix=archive.getmembers()[0].name.split('/')[0]
        for member in archive.getmembers():
            parts=Path(member.name).parts
            assert parts[0]==prefix
            if len(parts)==1:continue
            member.name='/'.join(parts[1:])
            destination=(target/member.name).resolve()
            assert destination.is_relative_to(target.resolve())
            archive.extract(member,target,filter='data')
    row={'repo':name,'commit':sha,'archive_bytes':len(data),'archive_sha256':hashlib.sha256(data).hexdigest(),'files':sum(p.is_file() for p in target.rglob('*'))}
    manifest.append(row);print(json.dumps(row),flush=True)
    (ROOT/'runs/author_evidence/workspace_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
