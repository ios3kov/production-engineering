"""Strict adapters for specialist evidence. Discard raw snippets and console/cookie values."""
import math
import re
from urllib.parse import urlsplit
from audit import finding


def require(value,message='Invalid or incomplete tool report'):
    if not value:raise ValueError(message)


def safe_rule(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,180}',value))
    return value


def web_url(value):
    require(isinstance(value,str))
    p=urlsplit(value)
    require(p.scheme in {'http','https'} and p.hostname and not p.username and not p.password and not p.query and not p.fragment)
    return value


def _parse_tool_report(tool,data,returncode):
    require(isinstance(data,dict) and type(returncode) is int)
    findings=[];checks=[]
    def add(rule,severity,title,path='',line=0,url=None):
        require(type(line) is int and line>=0)
        require(isinstance(path,str) and not path.startswith(('/','\\')) and '..' not in path.replace('\\','/').split('/'))
        f=finding(tool+'.'+safe_rule(rule),path,line,severity,title,'Review the specialist report locally and verify a targeted fix.',source=tool,confidence='tool_reported')
        if url:f['evidence']={'kind':'runtime','url':web_url(url)}
        findings.append(f)
    if tool=='semgrep':
        require(returncode in {0,1})
        require(isinstance(data.get('results'),list) and data.get('errors')==[])
        paths=data.get('paths',{});require(isinstance(paths,dict) and isinstance(paths.get('scanned'),list) and paths['scanned'])
        require(not paths.get('skipped'))
        require(returncode==0 or data['results'])
        for row in data['results']:
            sev=row['extra']['severity'];require(sev in {'ERROR','WARNING','INFO'})
            add(row['check_id'],{'ERROR':'high','WARNING':'medium','INFO':'low'}[sev],
                'Semgrep static security finding',row['path'],row['start']['line'])
        checks=[{'id':'semgrep','status':'completed','files_scanned':len(paths['scanned'])}]
    elif tool=='browser':
        require(returncode==0 and isinstance(data.get('pages'),list) and data['pages'])
        incomplete=False
        for page in data['pages']:
            url=web_url(page['url']);status=page['status']
            require(type(status) is int and 100<=status<=599 and not page.get('error'))
            require(type(page.get('consoleErrorCount')) is int and page['consoleErrorCount']>=0)
            require(type(page.get('blockedRequests')) is int and page['blockedRequests']>=0)
            require(isinstance(page.get('cookies'),list) and isinstance(page.get('trackerHosts'),list))
            incomplete |= bool(page['blockedRequests'])
            if status>=400:add('http_status','high','Browser navigation returned an HTTP error',url=url)
            if page['consoleErrorCount']:add('console_errors','medium','Browser reported runtime or console errors (values omitted)',url=url)
            if page['trackerHosts']:add('tracking_candidate','medium','Tracking endpoint contacted before any consent interaction; applicability requires review',url=url)
            for cookie in page['cookies']:
                require(all(type(cookie.get(k)) is bool for k in ['secure','httpOnly','sessionLike']))
                if cookie['sessionLike'] and not cookie['httpOnly']:add('cookie_httponly','high','Session-like browser cookie lacks HttpOnly',url=url)
                if url.startswith('https:') and not cookie['secure']:add('cookie_secure','medium','Browser cookie lacks Secure',url=url)
            require(isinstance(page.get('axe'),list))
            for violation in page['axe']:
                impact=violation['impact'];require(impact in {'critical','serious','moderate','minor',None})
                add('axe.'+safe_rule(violation['id']),{'critical':'high','serious':'high','moderate':'medium','minor':'low',None:'medium'}[impact],'axe accessibility violation',url=url)
        checks=[{'id':name,'status':'error' if incomplete else 'completed',
                 'reason':'Requests blocked by scope; runtime coverage incomplete.' if incomplete else 'Explicit browser pages assessed.'} for name in ['browser','axe']]
    elif tool=='lighthouse':
        require(returncode==0 and not data.get('runtimeError'))
        url=web_url(data['finalDisplayedUrl'] if 'finalDisplayedUrl' in data else data['finalUrl'])
        require(isinstance(data.get('lighthouseVersion'),str) and data['lighthouseVersion'])
        cats=data['categories']
        for name,minimum in [('performance',.8),('accessibility',.9),('seo',.9),('best-practices',.9)]:
            score=cats[name]['score'];require(type(score) in {int,float} and math.isfinite(score) and 0<=score<=1)
            if score<minimum:add(name,'medium','Lighthouse score below default review budget',url=url)
        checks=[{'id':'lighthouse','status':'completed','note':'Single-run defaults; project-specific budgets and repeated runs still required.'}]
    elif tool=='zap':
        require(returncode in {0,1,2} and isinstance(data.get('site'),list) and data['site'])
        for site in data['site']:
            url=web_url(site['@name']);require(isinstance(site.get('alerts'),list))
            for alert in site['alerts']:
                risk=str(alert['riskcode']);require(risk in {'0','1','2','3'})
                add('alert.'+safe_rule(str(alert['pluginid'])),{'0':'info','1':'low','2':'medium','3':'high'}[risk],'ZAP passive alert',url=url)
        checks=[{'id':'zap','status':'completed','note':'Imported passive report; report authenticity belongs to the generating CI job.'}]
    elif tool=='trivy':
        require(type(data.get('SchemaVersion')) is int and isinstance(data.get('Results'),list) and data['Results'])
        count=0
        for result in data['Results']:
            vulnerabilities=result.get('Vulnerabilities') or []
            require(isinstance(vulnerabilities,list))
            for vulnerability in vulnerabilities:
                severity=str(vulnerability.get('Severity','')).upper()
                require(severity in {'UNKNOWN','LOW','MEDIUM','HIGH','CRITICAL'})
                rule=safe_rule(str(vulnerability['VulnerabilityID']))
                add(rule,{'UNKNOWN':'medium','LOW':'low','MEDIUM':'medium','HIGH':'high','CRITICAL':'critical'}[severity],
                    'Trivy dependency or image vulnerability')
                count+=1
        checks=[{'id':'trivy','status':'completed','results_scanned':len(data['Results']),'vulnerabilities':count}]
    elif tool=='osv':
        require(isinstance(data.get('results'),list))
        packages=0;count=0
        for result in data['results']:
            rows=result.get('packages');require(isinstance(rows,list))
            packages+=len(rows)
            for package in rows:
                vulnerabilities=package.get('vulnerabilities') or []
                require(isinstance(vulnerabilities,list))
                for vulnerability in vulnerabilities:
                    severity=str(vulnerability.get('database_specific',{}).get('severity','MODERATE')).upper()
                    mapped={'LOW':'low','MODERATE':'medium','MEDIUM':'medium','HIGH':'high','CRITICAL':'critical'}.get(severity,'medium')
                    add(safe_rule(str(vulnerability['id'])),mapped,'OSV dependency vulnerability')
                    count+=1
        require(packages>0)
        checks=[{'id':'osv','status':'completed','packages_scanned':packages,'vulnerabilities':count}]
    elif tool=='sbom':
        require(data.get('bomFormat')=='CycloneDX' and isinstance(data.get('specVersion'),str))
        components=data.get('components');require(isinstance(components,list) and components)
        missing_hash=sum(not isinstance(c.get('hashes'),list) or not c['hashes'] for c in components)
        missing_license=sum(not c.get('licenses') for c in components)
        missing_id=sum(not (c.get('purl') or c.get('bom-ref')) for c in components)
        if missing_hash:add('missing_hash','low',f'{missing_hash} SBOM components lack hashes')
        if missing_license:add('missing_license','low',f'{missing_license} SBOM components lack license data')
        if missing_id:add('missing_identifier','medium',f'{missing_id} SBOM components lack stable identifiers')
        checks=[{'id':'sbom','status':'completed','format':'CycloneDX','components':len(components)}]
    elif tool=='authz':
        require(returncode==0 and isinstance(data.get('cases'),list) and data['cases'])
        incomplete=False
        for case in data['cases']:
            require(all(isinstance(case.get(k),str) and case[k] for k in ['id','actor','action','resource','expected','actual']))
            require(case['expected'] in {'allow','deny'} and case['actual'] in {'allow','deny','error'})
            if case['actual']=='error':incomplete=True
            elif case['actual']!=case['expected']:
                add('case.'+safe_rule(case['id']),'high','Authorization matrix result differs from policy')
        checks=[{'id':'authz','status':'error' if incomplete else 'completed','cases':len(data['cases']),
                 'reason':'One or more authorization cases could not execute.' if incomplete else 'Explicit authorization cases assessed.'}]
    else:raise ValueError('Unsupported external tool')
    return findings,checks


def parse_tool_report(tool,data,returncode):
    try:
        return _parse_tool_report(tool,data,returncode)
    except (KeyError,TypeError,AttributeError,IndexError) as exc:
        raise ValueError('Invalid or incomplete tool report') from exc
