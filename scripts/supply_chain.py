"""Offline, bounded checks for GitHub Actions supply-chain hazards."""
from pathlib import Path
import re


SHA = re.compile(r"^[0-9a-fA-F]{40}$")
USES = re.compile(r"^\s*-?\s*uses\s*:\s*([^\s#]+)")


def scan_workflows(root, make_finding):
    findings=[]
    workflow_root=Path(root)/'.github'/'workflows'
    if not workflow_root.is_dir():
        return findings,{'id':'supply_chain.github_actions','status':'not_applicable','reason':'No GitHub Actions workflows in scope.'}
    files=sorted([*workflow_root.glob('*.yml'),*workflow_root.glob('*.yaml')])
    for path in files:
        text=path.read_text(encoding='utf-8')
        lines=text.splitlines();rel=path.relative_to(root).as_posix()
        direct=[i for i,line in enumerate(lines,1) if re.match(r'^\s*["\']?pull_request_target["\']?\s*:',line)]
        inline=[i for i,line in enumerate(lines,1) if re.search(r'^\s*on\s*:\s*\[[^]]*\bpull_request_target\b',line)]
        has_pr_target=bool(direct or inline)
        if has_pr_target:
            line=(direct or inline)[0]
            severity='high' if '${{ secrets.' in text else 'medium'
            findings.append(make_finding('supply_chain.pull_request_target',rel,line,severity,
                'pull_request_target workflow requires privileged-trigger review',
                'Ensure untrusted pull-request code is never checked out or executed with repository secrets or write permissions.',
                source='supply-chain',confidence='observed',standards=['NIST-SSDF-PS.1']))
        for i,line in enumerate(lines):
            stripped=line.strip()
            if re.match(r'permissions\s*:\s*write-all\s*$',stripped,re.I):
                findings.append(make_finding('supply_chain.write_all',rel,i+1,'high','Workflow grants write-all permissions',
                    'Declare the minimum read/write permissions required by each job.',source='supply-chain',confidence='observed',standards=['NIST-SSDF-PS.1']))
            if re.match(r'(contents|actions|checks|deployments|packages|pull-requests|security-events)\s*:\s*write\s*$',stripped,re.I):
                findings.append(make_finding('supply_chain.write_permission',rel,i+1,'medium','Workflow grants a write permission',
                    'Confirm the permission is required and scope it to the smallest job.',source='supply-chain',standards=['NIST-SSDF-PS.1']))
            match=USES.match(line)
            if not match:continue
            value=match.group(1)
            if value.startswith(('./','docker://')) or '@' not in value:continue
            action,ref=value.rsplit('@',1)
            if not SHA.fullmatch(ref):
                findings.append(make_finding('supply_chain.unpinned_action',rel,i+1,'medium','Third-party action is not pinned to a full commit SHA',
                    'Pin the action to a reviewed 40-character commit SHA and keep the human-readable version in a comment.',
                    source='supply-chain',confidence='observed',standards=['NIST-SSDF-PS.2']))
            if action.lower()=='actions/checkout':
                block='\n'.join(lines[i+1:i+9]).lower()
                if not re.search(r'persist-credentials\s*:\s*false\b',block):
                    findings.append(make_finding('supply_chain.checkout_credentials',rel,i+1,'low','Checkout may retain repository credentials',
                        'Set persist-credentials: false unless later authenticated Git operations are explicitly required.',
                        source='supply-chain',standards=['NIST-SSDF-PS.1']))
    return findings,{'id':'supply_chain.github_actions','status':'completed','files_scanned':len(files)}
