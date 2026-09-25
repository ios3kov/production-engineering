"""Scan unique reachable Git blobs; bounded and without diff/textconv execution."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from audit import COMPILED, GENERIC, finding


def git_bytes(root,args,timeout=20,limit=8*1024*1024):
    env=os.environ.copy()
    env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1')
    cmd=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','--no-pager','-C',str(root),*args]
    with tempfile.TemporaryFile() as output:
        result=subprocess.run(cmd,stdout=output,stderr=subprocess.DEVNULL,timeout=timeout,env=env)
        if result.returncode:raise ValueError('Git command failed')
        output.seek(0);data=output.read(limit+1)
        if len(data)>limit:raise ValueError('Git output budget exceeded')
        return data


def scan_history(root,max_bytes=64*1024*1024,max_objects=10000,timeout=60):
    start=time.monotonic();findings=[];scanned=0;used=0
    check={'id':'history','status':'error','blobs_scanned':0}
    def run(args,limit=8*1024*1024):
        remaining=timeout-(time.monotonic()-start)
        if remaining<=0:raise ValueError('History time budget exceeded')
        return git_bytes(root,args,min(20,remaining),limit)
    try:
        if run(['rev-parse','--is-shallow-repository']).strip()!=b'false':
            raise ValueError('History is shallow; fetch complete history before scanning')
        # No object names means hostile filenames cannot alter framing.
        ids=run(['rev-list','--objects','--all','--no-object-names']).decode('ascii').splitlines()
        ids=list(dict.fromkeys(ids))
        if not ids:raise ValueError('No reachable Git objects')
        if len(ids)>max_objects:raise ValueError('Git object budget exceeded')
        for oid in ids:
            if not re.fullmatch(r'[0-9a-f]{40,64}',oid):raise ValueError('Invalid Git object identifier')
            kind=run(['cat-file','-t',oid],128).strip()
            if kind!=b'blob':continue
            size=int(run(['cat-file','-s',oid],128))
            if size>2*1024*1024 or used+size>max_bytes:raise ValueError('Git blob byte budget exceeded')
            data=run(['cat-file','blob',oid],2*1024*1024)
            used+=len(data);scanned+=1
            # latin1 preserves all bytes while matching ASCII credential formats.
            text=data.decode('latin1');seen=set()
            for name,rx in [*COMPILED,('assignment',GENERIC)]:
                for match in rx.finditer(text):
                    line=text.count('\n',0,match.start())+1
                    if line in seen:continue
                    seen.add(line)
                    f=finding('history.secret.'+name,'',line,'high','Potential credential in reachable Git blob',
                        'Inspect the object locally; rotate exposed credentials. History cleanup is a separate authorized operation.',source='git-history')
                    f['evidence']={'kind':'git_blob','object':oid,'line':line}
                    f['fingerprint']=__import__('hashlib').sha256(f"{name}:{oid}:{line}".encode()).hexdigest()[:24]
                    findings.append(f)
        check.update(status='completed',blobs_scanned=scanned,bytes_scanned=used,
                     note='All local reachable refs; unreachable objects, LFS payloads and remote-only refs not covered.')
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError):
        check.update(reason='History unavailable, shallow, incomplete, or resource budget exceeded.',blobs_scanned=scanned,bytes_scanned=used)
    return findings,check
