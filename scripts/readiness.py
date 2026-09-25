"""Offline production-readiness evidence coordinator. Never executes project commands."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

DOMAINS = ('requirements','architecture','security','supply_chain','infrastructure',
           'data','reliability','performance','experience','operations')

def require(value):
    if not value: raise ValueError('Invalid readiness contract')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load(path):
    path=Path(path)
    require(not path.is_symlink() and path.is_file() and path.stat().st_size<=4*1024*1024)
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result);result[key]=value
        return result
    return json.loads(path.read_text(),object_pairs_hook=pairs)

def identifier(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}',value))
    return value

def timestamp(value):
    parsed=dt.datetime.fromisoformat(value)
    require(parsed.tzinfo is not None)
    return parsed

def plan(passport):
    require(passport.get('schema_version')==1)
    identifier(passport['project']);identifier(passport['environment'])
    require(isinstance(passport['components'],list) and passport['components'])
    components=[identifier(c) for c in passport['components']]
    require(len(set(components))==len(components))
    require(set(passport['domains'])==set(DOMAINS))
    checks=[];ids=set()
    for domain in DOMAINS:
        config=passport['domains'][domain]
        require(type(config['applicable']) is bool)
        if not config['applicable']:
            require(isinstance(config.get('reason'),str) and config['reason'].strip())
            continue
        require(isinstance(config['checks'],list) and config['checks'])
        for check in config['checks']:
            key=identifier(check['id']);require(key not in ids);ids.add(key)
            require(check['component'] in components)
            require(check['method'] in {'automated','manual'})
            require(isinstance(check['criterion'],str) and check['criterion'].strip())
            require(type(check['max_age_hours']) is int and 0<check['max_age_hours']<=720)
            checks.append(dict(check,domain=domain))
    require(checks)
    return {'project':passport['project'],'environment':passport['environment'],
            'plan_digest':digest(passport),'checks':checks,
            'not_applicable':[d for d in DOMAINS if not passport['domains'][d]['applicable']]}

def evaluate(passport,evidence,issues,now=None):
    planned=plan(passport);now=now or dt.datetime.now(dt.timezone.utc)
    release=passport['release']
    require(isinstance(release,dict) and re.fullmatch(r'[0-9a-f]{40,64}',release['commit']))
    require(re.fullmatch(r'[0-9a-f]{64}',release['artifact_sha256']))
    require(re.fullmatch(r'[0-9a-f]{64}',release['scope_digest']))
    require(evidence.get('plan_digest')==planned['plan_digest'])
    require(evidence.get('release')==release and evidence.get('environment')==passport['environment'])
    rows={};allowed={c['id'] for c in planned['checks']}
    require(isinstance(evidence['results'],list))
    for row in evidence['results']:
        key=identifier(row['id']);require(key in allowed and key not in rows)
        require(row['status'] in {'PASS','FAIL','BLOCKED','NOT_RUN'})
        rows[key]=row
    coverage=[];passed=set()
    for check in planned['checks']:
        row=rows.get(check['id']);status='NOT_RUN'
        if row:
            status=row['status']
            if status in {'PASS','FAIL'}:
                require(row['method']==check['method'])
                require(isinstance(row['producer'],str) and row['producer'].strip())
                require(isinstance(row['version'],str) and row['version'].strip())
                require(re.fullmatch(r'[0-9a-f]{64}',row['evidence_sha256']))
                age=(now-timestamp(row['created_at'])).total_seconds()
                if not -300<=age<=check['max_age_hours']*3600:status='BLOCKED'
                if row['method']=='automated':
                    require(type(row['exit_code']) is int)
                    if status=='PASS' and row['exit_code']!=0:status='BLOCKED'
                else:
                    require(isinstance(row['reviewer'],str) and row['reviewer'].strip())
            if status=='PASS':passed.add(check['id'])
        coverage.append({'id':check['id'],'domain':check['domain'],'component':check['component'],'status':status})
    require(isinstance(issues,list));seen=set();blockers=[]
    for issue in issues:
        key=identifier(issue['id']);require(key not in seen);seen.add(key)
        require(issue['check_id'] in allowed)
        require(issue['severity'] in {'info','low','medium','high','critical'})
        state=issue['state'];require(state in {'candidate','confirmed','fixed','false_positive','accepted_risk'})
        resolved=False
        if state in {'fixed','false_positive','accepted_risk'}:
            require(all(isinstance(issue.get(k),str) and issue[k].strip() for k in ['owner','reason']))
            if state=='fixed':
                require(issue['retest_check'] in allowed)
                resolved=issue['retest_check'] in passed
            else:
                require(re.fullmatch(r'[0-9a-f]{64}',issue['decision_sha256']))
                resolved=timestamp(issue['expires_at'])>now
        if not resolved and issue['severity'] in {'high','critical'}:blockers.append(key)
    incomplete=any(c['status'] in {'BLOCKED','NOT_RUN'} for c in coverage)
    failed=bool(blockers) or any(c['status']=='FAIL' for c in coverage)
    code=2 if incomplete else 1 if failed else 0
    return {'schema_version':1,'plan_digest':planned['plan_digest'],'release':release,
            'environment':passport['environment'],'coverage':coverage,'not_applicable':planned['not_applicable'],
            'blocking_issues':blockers,'exit_code':code,
            'verdict':{0:'SELECTED_REQUIREMENTS_SATISFIED',1:'NOT_READY',2:'INCOMPLETE'}[code],
            'limitations':'Evidence is supplied by trusted collectors/reviewers; hashes bind identity, not authenticity. No deployment authorization.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('passport');parser.add_argument('--evidence');parser.add_argument('--issues')
    args=parser.parse_args()
    try:
        passport=load(args.passport)
        if args.evidence:
            require(args.issues is not None)
            result=evaluate(passport,load(args.evidence),load(args.issues))
        else:result=plan(passport)
        print(json.dumps(result,indent=2));return result.get('exit_code',0)
    except (OSError,ValueError,KeyError,TypeError,AttributeError,RecursionError):
        print('Readiness input invalid or incomplete.',file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
