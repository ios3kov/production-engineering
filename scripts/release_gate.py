"""Explicit policy gate; missing evidence never passes. Not a release certification."""
SEVERITIES={'info':0,'low':1,'medium':2,'high':3,'critical':4}


def evaluate_gate(report,policy):
    if not isinstance(policy,dict):raise ValueError('Policy must be an object')
    required=policy.get('required');threshold=policy.get('fail_on','high')
    if not isinstance(required,list) or not required or not all(isinstance(x,str) and x for x in required) or len(set(required))!=len(required):
        raise ValueError('Required checks must be a nonempty unique list')
    if threshold not in SEVERITIES:raise ValueError('Invalid severity threshold')
    checks={}
    for check in report['checks']:
        if check['id'] in checks:raise ValueError('Duplicate check ID')
        checks[check['id']]=check
    missing=[name for name in required if name not in checks or checks[name]['status']!='completed']
    # An error in any selected check also blocks, even if accidentally absent from policy.
    missing+= [name for name,c in checks.items() if c['status'] in {'error','skipped'} and name not in missing]
    if 'authz' in required or 'authz' in checks:
        expected=policy.get('authz_required_cases')
        if not isinstance(expected,list) or not expected or not all(isinstance(x,str) and x for x in expected) or len(set(expected))!=len(expected):
            raise ValueError('Authorization policy requires unique authz_required_cases')
        actual=checks.get('authz',{}).get('case_ids',[])
        if not set(expected).issubset(actual) and 'authz' not in missing:missing.append('authz')
    blockers=[f for f in report['findings'] if SEVERITIES[f['severity']]>=SEVERITIES[threshold]]
    code=2 if missing else 1 if blockers else 0
    return {'exit_code':code,'verdict':{0:'selected_gates_passed',1:'blocked_by_findings',2:'incomplete'}[code],
            'required':required,'missing_or_incomplete':missing,'blocking_findings':len(blockers),
            'note':('Selected policy satisfied.' if code==0 else 'Selected policy not satisfied.')+' This is not authorization to deploy or proof of overall readiness.'}
