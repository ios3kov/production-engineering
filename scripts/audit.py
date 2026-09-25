#!/usr/bin/env python3
"""Bounded local audit. Stdlib only. No project code or network by default."""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import quote
from supply_chain import scan_workflows

VERSION = '1.2.0'
HERE = Path(__file__).resolve().parent
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_FILES = 10000
SKIP = {'.git','node_modules','vendor','dist','build','out','.next','.nuxt','.output','.venv','venv','__pycache__','coverage','.cache','.terraform','Pods','target','.audit'}
EXTS = {'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.svelte','.html','.htm','.css','.scss','.json','.yaml','.yml','.toml','.ini','.conf','.cfg','.sh','.sql','.md','.mdx','.txt','.xml','.rules','.rb','.php','.go','.java','.kt','.cs','.swift','.env','.pem','.key','.lock','.astro','.webmanifest'}
PATTERNS = [
 ('github',r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{30,})\b'),
 ('provider',r'\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|[sr]k_(?:live|test)_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b'),
 ('aws',r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 ('telegram',r'\b\d{8,12}:[A-Za-z0-9_-]{35}\b'),
 ('private_key',r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 ('database',r'(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@]+:[^\s@]+@'),
 ('sendgrid',r'\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b'),
]
COMPILED = [(name,re.compile(rx)) for name,rx in PATTERNS]
GENERIC = re.compile(r'''(?i)\b(?:api[_-]?key|secret|password|passwd|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*["']([^"'\s]{12,})["']''')
PUBLIC = re.compile(r'\b(?:NEXT_PUBLIC_|VITE_|REACT_APP_|EXPO_PUBLIC_|NUXT_PUBLIC_)[A-Z0-9_]*(?:SECRET|PASSWORD|PRIVATE_KEY|SERVICE_ROLE|DATABASE_URL)[A-Z0-9_]*\b')


def safe_text(value):
    value = str(value)
    for _,rx in COMPILED:
        value = rx.sub('[REDACTED]',value)
    value = GENERIC.sub('[REDACTED_ASSIGNMENT]',value)
    return ''.join(c if c >= ' ' or c in '\n\t' else '?' for c in value)


def finding(rule,path,line,severity,title,fix,source='core',confidence='heuristic',standards=None):
    path=safe_text(path)
    identity=f'{rule}\0{path}\0{line}'
    return dict(rule=rule,path=path,line=line,severity=severity,title=safe_text(title),
                remediation=fix,source=source,confidence=confidence,
                standards=list(standards or []),
                fingerprint=hashlib.sha256(identity.encode()).hexdigest()[:24],
                evidence={'kind':'source_location','note':'Inspect locally; source text and values deliberately omitted.'})


def inventory(root,dest):
    digest=hashlib.sha256()
    result={'scope_digest':digest.hexdigest(),'files':0,'bytes':0,'excluded_directories':0,'unsupported_files':0,'omissions':[]}
    def omitted(path,reason):
        result['omissions'].append({'path':safe_text(str(path.relative_to(root))),'reason':reason})
    def onerror(error):
        result['omissions'].append({'path':'[directory]','reason':'directory unreadable'})
    for base,dirs,files in os.walk(root,followlinks=False,onerror=onerror):
        dirs.sort(); files.sort()
        kept=[]
        for name in dirs:
            p=Path(base)/name
            if p.is_symlink(): omitted(p,'symlink not followed')
            elif name in SKIP or p.resolve()==HERE.parent:
                result['excluded_directories']+=1
            else: kept.append(name)
        dirs[:]=kept
        for name in files:
            p=Path(base)/name
            if p.is_symlink():
                omitted(p,'symlink not followed');continue
            if not (p.suffix.lower() in EXTS or name.startswith('.env') or name in {'Dockerfile','Caddyfile','.gitignore','.htaccess'}):
                result['unsupported_files']+=1;continue
            try:
                mode=p.stat().st_mode
                if not stat.S_ISREG(mode): omitted(p,'non-regular file');continue
                if p.stat().st_size>MAX_FILE: omitted(p,'file size limit');continue
                # O_NOFOLLOW also closes the leaf-symlink race on POSIX.
                fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
                with os.fdopen(fd,'rb') as f:
                    if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                        omitted(p,'non-regular file');continue
                    data=f.read(MAX_FILE+1)
                if len(data)>MAX_FILE: omitted(p,'file size limit');continue
                if result['bytes']+len(data)>MAX_TOTAL or result['files']>=MAX_FILES:
                    omitted(p,'total budget limit');return result
                if b'\0' in data: omitted(p,'binary content in text candidate');continue
                text=data.decode('utf-8')
                out=dest/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True)
                out.write_text(text,encoding='utf-8')
                digest.update(p.relative_to(root).as_posix().encode()+b'\0'+str(len(data)).encode()+b'\0'+data)
                result['scope_digest']=digest.hexdigest()
                result['files']+=1;result['bytes']+=len(data)
            except (OSError,UnicodeError): omitted(p,'unreadable or non-UTF8 file')
    return result


def run_json(command,cwd=None,timeout=60,env=None,with_returncode=False):
    # File-backed capture avoids unbounded RAM consumption for subprocess output.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        p=subprocess.run(command,cwd=cwd,stdout=out,stderr=err,timeout=timeout,env=env)
        if p.returncode not in (0,1): raise RuntimeError('tool exit failure')
        out.seek(0); raw=out.read(4*1024*1024+1)
        if len(raw)>4*1024*1024: raise RuntimeError('tool output limit')
        data=json.loads(raw)
        if not isinstance(data,dict): raise ValueError('tool output must be an object')
        return (data,p.returncode) if with_returncode else data


def core_scan(root, checks=None):
    findings=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        text=p.read_text(encoding='utf-8');rel=p.relative_to(root).as_posix()
        claimed=set()
        for name,rx in COMPILED:
            for m in rx.finditer(text):
                line=text.count('\n',0,m.start())+1
                if line in claimed:continue
                claimed.add(line)
                findings.append(finding('secret.'+name,rel,line,'high','Potential embedded credential: '+name,
                    'Verify locally; remove literals and rotate exposed credentials. Examples and tests are not automatically trusted.'))
        for m in GENERIC.finditer(text):
            line=text.count('\n',0,m.start())+1;value=m.group(1)
            if line in claimed or value.startswith(('${','process.env','os.environ','YOUR_','your_','example','placeholder')):continue
            claimed.add(line)
            findings.append(finding('secret.assignment',rel,line,'medium','Potential credential assignment','Verify the value locally; use secret storage if real.'))
        for m in PUBLIC.finditer(text):
            findings.append(finding('secret.public_env',rel,text.count('\n',0,m.start())+1,'high','Sensitive name uses a public environment prefix','Verify bundling; keep secret values server-side.'))
        if re.fullmatch(r'(?:docker-)?compose(?:[.-].*)?\.ya?ml',p.name):
            rx=re.compile(r'''(?im)\b(?:POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|MONGO_INITDB_ROOT_PASSWORD)\s*[:=]\s*["']?(?:postgres|root|password|admin|123|example)\b''')
            for m in rx.finditer(text):
                findings.append(finding('config.default_db_password',rel,text.count('\n',0,m.start())+1,'high','Default database password candidate','Use a generated deployment secret; verify effective Compose configuration.'))
        if p.suffix=='.py':
            try:tree=ast.parse(text)
            except SyntaxError:
                if checks is not None:
                    checks.append({'id':'core.python_ast:'+safe_text(rel),'status':'error','reason':'Python parse failed; syntax or language-version mismatch.'})
                continue
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in {'execute','executemany'} and node.args and isinstance(node.args[0],ast.JoinedStr):
                    findings.append(finding('injection.sql_fstring',rel,node.lineno,'high','Interpolated string passed to database execution','Trace input origin and use bound query parameters.',standards=['v5.0.0-1.2.4']))
    return findings


def git_check(root):
    if not (root/'.git').exists():return [],{'id':'git.index','status':'not_applicable','reason':'No repository marker at audit root; Git history is never scanned.'}
    try:
        p=subprocess.run(['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(root),'ls-files','-z'],capture_output=True,timeout=20)
        if p.returncode:raise RuntimeError()
        files=p.stdout.decode('utf-8').split('\0');found=[]
        for name in files:
            bn=Path(name).name
            if bn.startswith('.env') and not bn.endswith(('.example','.sample','.template','.dist')):
                found.append(finding('secret.tracked_env',name,0,'high','Environment file tracked by Git','Inspect locally; remove sensitive values from version control and rotate exposed credentials.',confidence='observed'))
        return found,{'id':'git.index','status':'completed'}
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        return [],{'id':'git.index','status':'error','reason':'Git index unavailable.'}


def git_identity(root):
    if not (root/'.git').exists():return {'commit':None,'dirty':None}
    try:
        base=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(root)]
        head=subprocess.run([*base,'rev-parse','HEAD'],capture_output=True,timeout=20,check=True).stdout.decode('ascii').strip()
        if not re.fullmatch(r'[0-9a-f]{40,64}',head):raise ValueError()
        status=subprocess.run([*base,'status','--porcelain=v1','--untracked-files=normal'],capture_output=True,timeout=20,check=True)
        return {'commit':head,'dirty':bool(status.stdout)}
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError):
        return {'commit':None,'dirty':None}


def web_checks(root):
    findings=[];checks=[]
    for name in ['check_a11y','check_seo','check_consent','check_headers','find_pages']:
        try:
            data=run_json([sys.executable,str(HERE/'vendor'/'web'/(name+'.py')),str(root),'--json'])
            rows=data.get('findings')
            if not isinstance(rows,list):raise ValueError()
            for row in rows:
                if not isinstance(row,dict) or row.get('status') not in {'ok','warn','fail','info'} or not isinstance(row.get('check'),str):raise ValueError()
                if row['status']=='ok':continue
                # Upstream messages may contain literal source lines. Do not carry them forward.
                rule='web.'+row['check']
                findings.append(finding(rule,str(row.get('file','')),int(row.get('line',0)),
                    {'fail':'medium','warn':'low','info':'info'}[row['status']],
                    'Review '+row['check'], 'Inspect the referenced source and validate applicability in the running application.',source='web-audit'))
            checks.append({'id':name,'status':'completed','note':'Heuristic signals only; upstream success does not prove runtime behavior.'})
        except (OSError,ValueError,TypeError,RuntimeError,subprocess.SubprocessError):
            checks.append({'id':name,'status':'error','reason':'Check failed, timed out or returned invalid data.'})
    return findings,checks


def vibe_checks(root):
    # Separate process isolates imports and puts a timeout around upstream regex checks.
    try:
        data=run_json([sys.executable,str(HERE/'vibe_adapter.py'),str(root)])
        rows=data.get('findings');checks=data.get('checks')
        if not isinstance(rows,list) or not isinstance(checks,list):raise ValueError()
        result=[]
        for row in rows:
            where=row['where']; path,sep,line=where.rpartition(':')
            if not sep or not line.isdigit():path,line=where,0
            standards={'sql_fstring':['v5.0.0-1.2.4'],'eval_use':['v5.0.0-1.3.2']}.get(row['id'],[])
            result.append(finding('vibe.'+row['id'],path,int(line),'medium' if row['severity']!='info' else 'info',
                row['title'],'Inspect context and reproduce before changing code.',source='vibe-audit',standards=standards))
        return result,checks
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError):
        return [],[{'id':'vibe.static','status':'error','reason':'Adapter failed or timed out.'}]


def npm_checks(root):
    findings=[];checks=[]
    for pkg in sorted(root.rglob('package.json')):
        label=pkg.relative_to(root).as_posix();lock=pkg.parent/'package-lock.json'
        if not lock.exists():
            checks.append({'id':'deps.npm:'+label,'status':'skipped','reason':'No npm lockfile; use the project package manager and record separate evidence.'});continue
        try:
            with tempfile.TemporaryDirectory(prefix='pe-npm-') as tmp:
                dest=Path(tmp)
                # Do not trust npm config, registry URLs or lifecycle scripts in a project.
                data=json.loads(lock.read_text())
                if not isinstance(data,dict) or not isinstance(data.get('lockfileVersion'),int):raise ValueError()
                shutil.copyfile(lock,dest/'package-lock.json')
                (dest/'package.json').write_text('{"name":"audit-snapshot","version":"0.0.0","private":true}')
                env={k:v for k,v in os.environ.items() if k in {'PATH','SYSTEMROOT','WINDIR','TMPDIR'}}
                (dest/'user.npmrc').write_text('')
                (dest/'global.npmrc').write_text('')
                env.update(HOME=tmp,npm_config_cache=str(dest/'cache'),npm_config_userconfig=str(dest/'user.npmrc'),npm_config_globalconfig=str(dest/'global.npmrc'),npm_config_ignore_scripts='true')
                report=run_json(['npm','audit','--json','--ignore-scripts','--registry=https://registry.npmjs.org'],cwd=tmp,timeout=90,env=env)
                meta=report.get('metadata',{}).get('vulnerabilities')
                if 'error' in report or not isinstance(meta,dict) or not all(type(meta.get(k)) is int and meta[k]>=0 for k in ['critical','high','moderate','low','info']):raise ValueError()
                for severity in ['critical','high','moderate','low','info']:
                    if meta[severity]:
                        findings.append(finding('deps.npm.'+severity,label,0,'medium' if severity=='moderate' else severity,
                            f'{meta[severity]} dependency vulnerabilities at {severity} severity','Review npm advisories and dependency paths, update deliberately, then retest.',source='npm',confidence='tool_reported'))
                checks.append({'id':'deps.npm:'+label,'status':'completed'})
        except (OSError,ValueError,TypeError,AttributeError,RuntimeError,subprocess.SubprocessError):
            checks.append({'id':'deps.npm:'+label,'status':'error','reason':'Dependency audit unavailable, failed, or returned invalid data.'})
    if not checks:checks=[{'id':'deps.npm','status':'not_applicable','reason':'No package.json in scope.'}]
    return findings,checks


def exit_code(report):
    if any(c['status'] in {'error','skipped'} for c in report['checks']):return 2
    return 1 if report['findings'] else 0


def scan(root,web=True,npm=False):
    root=Path(root).resolve()
    if not root.is_dir():raise ValueError('Audit root must be an existing directory.')
    checks=[];findings=[]
    with tempfile.TemporaryDirectory(prefix='pe-audit-') as tmp:
        snapshot=Path(tmp)
        inv=inventory(root,snapshot)
        checks.append({'id':'inventory','status':'completed' if inv['files'] and not inv['omissions'] else 'error',
                       'reason':'Empty or incomplete text scope.' if not inv['files'] or inv['omissions'] else 'Bounded text scope inventoried.'})
        findings+=core_scan(snapshot,checks);checks.append({'id':'core.static','status':'completed'})
        f,c=git_check(root);findings+=f;checks.append(c)
        f,c=vibe_checks(snapshot);findings+=f;checks+=c
        f,c=scan_workflows(snapshot,finding);findings+=f;checks.append(c)
        if web:
            f,c=web_checks(snapshot);findings+=f;checks+=c
        if npm:
            f,c=npm_checks(snapshot);findings+=f;checks+=c
    unique={f['fingerprint']:f for f in findings}
    rank={'critical':0,'high':1,'medium':2,'low':3,'info':4}
    findings=sorted(unique.values(),key=lambda f:(rank[f['severity']],f['path'],f['line'],f['rule']))
    report={'schema_version':1,'tool_version':VERSION,'time_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source_identity':git_identity(root),
            'profile':'web' if web else 'code','release_readiness':'not_assessed','inventory':inv,'checks':checks,'findings':findings,
            'not_assessed':['Git history','runtime headers/cookies','browser flows and accessibility','authorization and E2EE','performance under load','backup restore and rollback','legal applicability']+([] if npm else ['dependency vulnerabilities']),
            'scope_note':'Generated/dependency directories and unsupported file types excluded. No finding is a safety guarantee.'}
    report['exit_code']=exit_code(report)
    report['verdict']={0:'no_findings_in_scanned_scope',1:'review_required',2:'incomplete'}[report['exit_code']]
    return report


def render(report,fmt):
    if fmt=='json':return json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if fmt=='sarif':
        rules=sorted({f['rule'] for f in report['findings']})
        results=[]
        for f in report['findings']:
            row={'ruleId':f['rule'],'level':{'critical':'error','high':'error','medium':'warning','low':'warning','info':'note'}[f['severity']],
                 'message':{'text':f['title']+' — '+f['remediation']},'partialFingerprints':{'productionEngineering/v1':f['fingerprint']},
                 'properties':{'confidence':f['confidence'],'source':f['source'],'standards':f.get('standards',[])}}
            if f['path']:
                location={'artifactLocation':{'uri':quote(f['path'],safe='/')}}
                if f['line']>0:location['region']={'startLine':f['line']}
                row['locations']=[{'physicalLocation':location}]
            results.append(row)
        return json.dumps({'version':'2.1.0','$schema':'https://json.schemastore.org/sarif-2.1.0.json','runs':[{
            'tool':{'driver':{'name':'Production Engineering','version':VERSION,'rules':[{'id':r} for r in rules]}},
            'results':results,'invocations':[{'executionSuccessful':report['exit_code']!=2,
                'toolExecutionNotifications':[{'level':'error','message':{'text':c['id']+': '+c.get('reason','Incomplete')}} for c in report['checks'] if c['status'] in {'skipped','error'}]}],
            'properties':{'verdict':report['verdict'],'releaseReadiness':'not_assessed','notAssessed':report['not_assessed'],'gate':report.get('gate')}}]},ensure_ascii=False,indent=2)+'\n'
    def esc(s):return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('`','&#96;').replace('\n',' ')
    lines=['# Production Engineering audit','',f"Verdict: **{report['verdict']}**; exit {report['exit_code']}.",'Release readiness: **not assessed**.',
           f"Text files scanned: {report['inventory']['files']}. Findings: {len(report['findings'])}.",'',report['scope_note'],'','## Checks','']
    lines += [f"- {esc(c['id'])}: {c['status']}" for c in report['checks']]
    if 'gate' in report:
        lines += ['', '## Selected policy', '', 'Required: '+esc(', '.join(report['gate']['required'])), 'Missing/incomplete: '+esc(', '.join(report['gate']['missing_or_incomplete']) or 'none')]
    lines += ['','## Findings','']
    for f in report['findings']:
        lines += [f"### {f['severity']}: {esc(f['title'])}",f"- Rule: {esc(f['rule'])}; confidence: {f['confidence']}",f"- Standards: {esc(', '.join(f.get('standards',[])) or 'none')}",f"- Location: {esc(f['path'])}:{f['line']}",f"- Action: {esc(f['remediation'])}",f"- Fingerprint: {f['fingerprint']}",'']
    lines+=['## Not assessed','']+['- '+s for s in report['not_assessed']]
    if report['inventory']['omissions']:lines+=['','## Omitted inputs','']+['- '+esc(o['path'])+': '+o['reason'] for o in report['inventory']['omissions']]
    return '\n'.join(lines)+'\n'


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root',nargs='?',default='.')
    ap.add_argument('--profile',choices=['code','web'],default='web')
    ap.add_argument('--format',choices=['json','markdown','sarif'],default='markdown')
    ap.add_argument('--out',type=Path)
    ap.add_argument('--npm-audit',action='store_true',help='Opt in to npm audit; sends dependency metadata to npm registry.')
    args=ap.parse_args(argv)
    try:
        if args.out and args.out.exists():raise ValueError('Output exists; choose a fresh report path.')
        report=scan(args.root,web=args.profile=='web',npm=args.npm_audit)
        output=render(report,args.format)
        if args.out:
            # Exclusive creation prevents accidentally overwriting source files or symlink targets.
            with args.out.open('x',encoding='utf-8') as f:f.write(output)
        else:print(output,end='')
        return exit_code(report)
    except (OSError,ValueError) as e:
        print('Audit could not complete: '+safe_text(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
