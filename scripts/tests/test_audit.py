import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p
    def test_secret_in_docs_and_examples_never_leaks(self):
        token = 'ghp_' + 'A1b2C3d4' * 5
        for path in ['README.md', '.env.example', 'tests/key.test.ts']:
            self.put(path, 'token = "' + token + '"')
        report = audit.scan(self.root, web=False)
        secrets = [f for f in report['findings'] if f['rule'].startswith('secret.')]
        self.assertEqual(len(secrets), 3)
        for fmt in ['json','markdown','sarif']:
            self.assertNotIn(token, audit.render(report, fmt))
        self.assertEqual(audit.exit_code(report), 1)
    def test_clean_does_not_mean_ready(self):
        self.put('main.py', 'print("hello")\n')
        r = audit.scan(self.root, web=False)
        self.assertEqual(audit.exit_code(r), 0)
        self.assertEqual(r['release_readiness'], 'not_assessed')
    def test_empty_and_missing_are_incomplete(self):
        self.assertEqual(audit.exit_code(audit.scan(self.root, web=False)), 2)
        with self.assertRaises(ValueError):
            audit.scan(self.root/'missing')
    def test_symlink_is_not_read_and_is_disclosed(self):
        outside = self.root.parent / (self.root.name+'-secret')
        outside.write_text('ghp_'+'Z'*40)
        self.addCleanup(outside.unlink)
        self.put('safe.py', 'print(1)')
        (self.root/'link.py').symlink_to(outside)
        r = audit.scan(self.root, web=False)
        self.assertFalse(r['findings'])
        self.assertEqual(audit.exit_code(r), 2)
        self.assertTrue(r['inventory']['omissions'])
    def test_oversize_is_incomplete(self):
        self.put('large.py', 'x'*(audit.MAX_FILE+1))
        self.assertEqual(audit.exit_code(audit.scan(self.root, web=False)), 2)
    def test_vendor_error_is_not_success(self):
        self.put('index.html','<html><body>Hello</body></html>')
        with patch.object(audit, 'run_json', side_effect=RuntimeError('bad output')):
            r = audit.scan(self.root)
        self.assertEqual(audit.exit_code(r), 2)
    def test_public_publishable_key_not_secret(self):
        self.put('client.ts','const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;')
        r = audit.scan(self.root, web=False)
        self.assertFalse(any(f['rule'].startswith('secret.') for f in r['findings']))
    def test_compose_modern_name(self):
        self.put('compose.production.yaml', 'services:\n  db:\n    environment:\n      POSTGRES_PASSWORD: postgres\n')
        r=audit.scan(self.root,web=False)
        self.assertTrue(any(f['rule']=='config.default_db_password' for f in r['findings']))
    def test_reports_share_exit_and_sarif_locations(self):
        self.put('space folder/key.py','KEY="ghp_'+'Q'*40+'"')
        r=audit.scan(self.root,web=False)
        s=json.loads(audit.render(r,'sarif'))
        self.assertEqual(s['version'],'2.1.0')
        self.assertIn('space%20folder',s['runs'][0]['results'][0]['locations'][0]['physicalLocation']['artifactLocation']['uri'])
        self.assertEqual(r['exit_code'],audit.exit_code(r))
    def test_cli_json_nonzero(self):
        self.put('bad.py','TOKEN="ghp_'+'Q'*40+'"')
        p=subprocess.run([sys.executable,str(Path(audit.__file__)),str(self.root),'--profile','code','--format','json'],capture_output=True,text=True)
        self.assertEqual(p.returncode,1)
        self.assertEqual(json.loads(p.stdout)['exit_code'],1)
    def test_npm_network_error_incomplete(self):
        self.put('package.json','{}')
        self.put('package-lock.json','{"lockfileVersion":3}')
        with patch.object(audit,'run_json',return_value={'error':{'code':'ENETUNREACH'}}):
            r=audit.scan(self.root,web=False,npm=True)
        self.assertEqual(audit.exit_code(r),2)
    def test_no_overwrite_input_report(self):
        p=self.put('main.py','print(1)')
        r=subprocess.run([sys.executable,str(Path(audit.__file__)),str(self.root),'--out',str(p)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertEqual(p.read_text(),'print(1)')

class ExtendedAuditTests(unittest.TestCase):
    setUp = AuditTests.setUp
    put = AuditTests.put
    def test_python_multiline_query(self):
        self.put('db.py','cursor.execute(\n f"SELECT * FROM users WHERE id={user_input}"\n)')
        r=audit.scan(self.root,web=False)
        finding=next(f for f in r['findings'] if f['rule']=='injection.sql_fstring')
        self.assertIn('v5.0.0-1.2.4',finding['standards'])
    def test_bound_query_not_flagged(self):
        self.put('db.py','cursor.execute("SELECT * FROM users WHERE id=?", (user_input,))')
        r=audit.scan(self.root,web=False)
        self.assertFalse(any('sql' in f['rule'] for f in r['findings']))
    def test_web_metadata_failure(self):
        self.put('package.json','{"dependencies":null}')
        r=audit.scan(self.root)
        self.assertEqual(audit.exit_code(r),2)
    def test_nested_npm_high_vulnerability(self):
        self.put('apps/web/package.json','{}')
        self.put('apps/web/package-lock.json','{"lockfileVersion":3}')
        meta={'critical':0,'high':1,'moderate':0,'low':0,'info':0}
        with patch.object(audit,'run_json',return_value={'metadata':{'vulnerabilities':meta}}):
            f,c=audit.npm_checks(self.root)
        self.assertEqual(c[0]['status'],'completed')
        self.assertEqual(f[0]['path'],'apps/web/package.json')
        self.assertEqual(f[0]['severity'],'high')
    def test_missing_lock_incomplete(self):
        self.put('package.json','{}')
        r=audit.scan(self.root,web=False,npm=True)
        self.assertEqual(audit.exit_code(r),2)
    def test_subprocess_invalid_json(self):
        with self.assertRaises(ValueError):
            audit.run_json([sys.executable,'-c','print("not-json")'])
    def test_subprocess_exit_error(self):
        with self.assertRaises(RuntimeError):
            audit.run_json([sys.executable,'-c','import sys; print("{}"); sys.exit(3)'])
    def test_subprocess_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            audit.run_json([sys.executable,'-c','import time; time.sleep(5)'],timeout=.05)
    def test_git_tracked_env(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        self.put('.env','LOCAL=1')
        subprocess.run(['git','-C',str(self.root),'add','.env'],check=True)
        r=audit.scan(self.root,web=False)
        self.assertTrue(any(f['rule']=='secret.tracked_env' for f in r['findings']))
    def test_git_command_failure_is_incomplete(self):
        (self.root/'.git').mkdir()
        self.put('main.py','print(1)')
        failed=subprocess.CompletedProcess(['git'],2,stdout=b'',stderr=b'failure')
        with patch.object(audit.subprocess,'run',return_value=failed):
            r=audit.scan(self.root,web=False)
        self.assertEqual(audit.exit_code(r),2)
        self.assertEqual(next(c for c in r['checks'] if c['id']=='git.index')['status'],'error')
    def test_source_identity_records_commit_and_dirty_state(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=x@example.test','commit','--allow-empty','-qm','one'],check=True)
        clean=audit.scan(self.root,web=False)['source_identity']
        self.assertRegex(clean['commit'],r'^[0-9a-f]{40}$');self.assertFalse(clean['dirty'])
        self.put('main.py','print(1)')
        self.assertTrue(audit.scan(self.root,web=False)['source_identity']['dirty'])
    def test_supply_chain_workflow_findings(self):
        self.put('.github/workflows/release.yml','''on:\n  pull_request_target:\npermissions: write-all\njobs:\n  release:\n    steps:\n      - uses: actions/checkout@v4\n      - run: echo "${{ secrets.TOKEN }}"\n''')
        r=audit.scan(self.root,web=False)
        rules={f['rule'] for f in r['findings']}
        self.assertTrue({'supply_chain.pull_request_target','supply_chain.write_all','supply_chain.unpinned_action'} <= rules)
        self.assertTrue(any(f['standards'] for f in r['findings'] if f['rule'].startswith('supply_chain.')))
        self.assertEqual(next(c for c in r['checks'] if c['id']=='supply_chain.github_actions')['status'],'completed')
    def test_total_budget_marks_incomplete(self):
        self.put('a.py','print(123)')
        self.put('b.py','print(456)')
        with patch.object(audit,'MAX_TOTAL',10):
            r=audit.scan(self.root,web=False)
        self.assertEqual(audit.exit_code(r),2)
    def test_binary_candidate_marks_incomplete(self):
        self.put('main.py','print(1)')
        (self.root/'bad.py').write_bytes(b'\0foo')
        r=audit.scan(self.root,web=False)
        self.assertEqual(audit.exit_code(r),2)

    def test_alt_whitespace_is_valid(self):
        self.put('index.html','<html><img alt = "Logo" src="a.svg"></html>')
        r=audit.scan(self.root)
        self.assertFalse(any(f['rule']=='web.a11y.alt' for f in r['findings']))
    def test_unlabeled_checkbox_is_detected(self):
        self.put('index.html','<html><input type="checkbox"></html>')
        r=audit.scan(self.root)
        self.assertTrue(any(f['rule']=='web.a11y.labels' for f in r['findings']))
    def test_unrelated_label_does_not_hide_missing_label(self):
        self.put('index.html','<label for="other">Name</label><input id="name">')
        r=audit.scan(self.root)
        self.assertTrue(any(f['rule']=='web.a11y.labels' for f in r['findings']))
    def test_valid_associated_labels(self):
        self.put('index.html','<label for="name">Name</label><input id="name"><label><input type="checkbox">Agree</label>')
        r=audit.scan(self.root)
        self.assertFalse(any(f['rule']=='web.a11y.labels' for f in r['findings']))
    def test_python_ast_parse_failure_is_incomplete(self):
        self.put('bad.py','def broken(')
        r=audit.scan(self.root,web=False)
        self.assertEqual(audit.exit_code(r),2)

    def test_vibe_config_candidate_completes(self):
        self.put('app.py','app.run(debug=True)')
        r=audit.scan(self.root,web=False)
        self.assertEqual(audit.exit_code(r),1)
        self.assertTrue(any(f['rule']=='vibe.debug_on' for f in r['findings']))
    def test_npm_uses_distinct_config_files(self):
        self.put('package.json','{}')
        self.put('package-lock.json','{"lockfileVersion":3}')
        def run(command,**kw):
            env=kw['env']
            self.assertNotEqual(env['npm_config_userconfig'],env['npm_config_globalconfig'])
            self.assertEqual(Path(env['npm_config_userconfig']).read_text(),'')
            return {'metadata':{'vulnerabilities':{k:0 for k in ['critical','high','moderate','low','info']}}}
        with patch.object(audit,'run_json',side_effect=run):
            f,c=audit.npm_checks(self.root)
        self.assertEqual(c[0]['status'],'completed')

if __name__=='__main__': unittest.main()
