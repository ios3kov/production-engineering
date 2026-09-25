#!/usr/bin/env python3
"""Unified deep audit: opt-in history, HTTP, browser and specialist evidence."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
import audit
from external_reports import parse_tool_report
from history import scan_history
from live_http import validate_url
from release_gate import evaluate_gate


def load_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>4*1024*1024:
        raise ValueError('Report must be a regular bounded JSON file')
    return json.loads(path.read_text(encoding='utf-8'))


def source_scope(root):
    with tempfile.TemporaryDirectory(prefix='pe-scope-') as tmp:
        inv=audit.inventory(Path(root).resolve(),Path(tmp))
    if not inv['files'] or inv['omissions']:raise ValueError('Source inventory is incomplete')
    return inv['scope_digest']


def import_evidence(bundle,scope_digest,target_url=''):
    if not isinstance(bundle,dict) or bundle.get('schema_version')!=1 or bundle.get('scope_digest')!=scope_digest:
        raise ValueError('Evidence does not match current source scope')
    timestamp=dt.datetime.fromisoformat(bundle['created_at'])
    if timestamp.tzinfo is None:raise ValueError('Evidence timestamp must include timezone')
    age=(dt.datetime.now(dt.timezone.utc)-timestamp).total_seconds()
    if not -300<=age<=86400:raise ValueError('Evidence is stale or from the future')
    reports=bundle.get('reports')
    if not isinstance(reports,list) or not reports:raise ValueError('Empty evidence bundle')
    findings=[];checks=[];tools=set()
    for item in reports:
        tool=item['tool']
        if tool in tools:raise ValueError('Duplicate tool report')
        tools.add(tool)
        f,c=parse_tool_report(tool,item['data'],item['returncode'])
        if tool!='semgrep':
            if not target_url or bundle.get('target_url')!=target_url:raise ValueError('Evidence target mismatch')
            origin=urlsplit(target_url)
            # Validate every raw report URL, even when there are no findings.
            data=item['data']
            urls=([p['url'] for p in data['pages']] if tool=='browser' else
                  [data.get('finalDisplayedUrl',data.get('finalUrl'))] if tool=='lighthouse' else
                  [s['@name'] for s in data['site']])
            for url in urls:
                p=urlsplit(url)
                if (p.scheme,p.hostname,p.port)!=(origin.scheme,origin.hostname,origin.port):raise ValueError('Report contains an out-of-origin result')
        for check in c:check['evidence_time']=bundle['created_at']
        findings+=f;checks+=c
    return findings,checks


def deep_scan(root,history=False,url='',allow_loopback=False,evidence=None,policy=None,web=True,npm=False,semgrep_rules=None):
    root=Path(root).resolve();report=audit.scan(root,web=web,npm=npm)
    # Explicit summary ID can be required in CI policy.
    report['checks'].append({'id':'static','status':'error' if report['exit_code']==2 else 'completed'})
    scope=report['inventory']['scope_digest']
    def attach(findings,checks):
        seen={c['id'] for c in report['checks']}
        if any(c['id'] in seen for c in checks):raise ValueError('Duplicate evidence for selected check')
        report['findings'].extend(findings);report['checks'].extend(checks)
    if history:
        f,c=scan_history(root);attach(f,[c])
        report['not_assessed'].remove('Git history')
    if url:
        try:
            cmd=[sys.executable,str(audit.HERE/'live_http.py'),url]
            if allow_loopback:cmd+=['--allow-loopback']
            result=audit.run_json(cmd,timeout=45)
            attach(result['findings'],[result['check']])
        except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError):
            attach([],[{'id':'http','status':'error','reason':'HTTP unavailable, out of scope or timed out.'}])
    if semgrep_rules:
        try:
            rulefile=Path(semgrep_rules).resolve()
            if not rulefile.is_file():raise ValueError('Rules must be a local file')
            with tempfile.TemporaryDirectory(prefix='pe-semgrep-') as tmp:
                snapshot=Path(tmp);inv=audit.inventory(root,snapshot)
                if inv['scope_digest']!=scope:raise ValueError('Source changed during audit')
                data,returncode=audit.run_json(['semgrep','scan','--config',str(rulefile),'--json','--metrics=off','--disable-version-check','.'],cwd=tmp,timeout=120,with_returncode=True)
                f,c=parse_tool_report('semgrep',data,returncode);attach(f,c)
        except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError):
            attach([],[{'id':'semgrep','status':'error','reason':'Semgrep unavailable, failed, or incomplete.'}])
    if evidence:
        try:
            f,c=import_evidence(load_json(Path(evidence)),scope,url);attach(f,c)
        except (OSError,ValueError,KeyError,TypeError,RuntimeError):
            attach([],[{'id':'external_evidence','status':'error','reason':'External evidence invalid, stale, duplicate or mismatched.'}])
    try:
        if source_scope(root)!=scope:raise ValueError('Source changed')
    except (OSError,ValueError):
        report['checks'].append({'id':'scope_stability','status':'error','reason':'Source changed or became incomplete during audit.'})
    target=urlsplit(url)
    report['target_url']=url if url and not any((target.query,target.fragment,target.username,target.password)) else ''
    report['profile']='deep'
    if policy:
        report['gate']=evaluate_gate(report,load_json(Path(policy)))
        report['exit_code']=report['gate']['exit_code'];report['verdict']=report['gate']['verdict']
    else:
        report['exit_code']=audit.exit_code(report)
        report['verdict']={0:'no_findings_in_scanned_scope',1:'review_required',2:'incomplete'}[report['exit_code']]
    completed={c['id'] for c in report['checks'] if c['status']=='completed'}
    report['not_assessed']=[n for n in report['not_assessed'] if not (n=='runtime headers/cookies' and 'http' in completed)]
    if 'history' not in completed and 'Git history' not in report['not_assessed']:report['not_assessed'].append('Git history')
    report['scope_note']+=' Deep checks cover only selected pages/tools. Evidence import binds scope, not report authenticity.'
    return report


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root',nargs='?',default='.')
    ap.add_argument('--history',action='store_true')
    ap.add_argument('--url',default='')
    ap.add_argument('--allow-loopback',action='store_true')
    ap.add_argument('--semgrep-rules',type=Path)
    ap.add_argument('--evidence',type=Path)
    ap.add_argument('--policy',type=Path)
    ap.add_argument('--npm-audit',action='store_true')
    ap.add_argument('--profile',choices=['code','web'],default='web')
    ap.add_argument('--format',choices=['json','markdown','sarif'],default='markdown')
    ap.add_argument('--out',type=Path)
    args=ap.parse_args(argv)
    try:
        if args.out and args.out.exists():raise ValueError('Choose a fresh output path')
        report=deep_scan(args.root,args.history,args.url,args.allow_loopback,args.evidence,args.policy,args.profile=='web',args.npm_audit,args.semgrep_rules)
        output=audit.render(report,args.format)
        if args.out:
            with args.out.open('x',encoding='utf-8') as f:f.write(output)
        else:print(output,end='')
        return report['exit_code']
    except (OSError,ValueError,KeyError,TypeError):
        print('Deep audit could not complete: check configuration and required evidence.',file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
