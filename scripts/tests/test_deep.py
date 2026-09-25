import datetime as dt
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from history import scan_history
from live_http import scan_http, validate_url
from external_reports import parse_tool_report
from release_gate import evaluate_gate
from deep_audit import import_evidence, deep_scan
from audit import render

class DeepTests(unittest.TestCase):
    def test_missing_required_blocks(self):
        r=evaluate_gate({'checks':[],'findings':[]},{'required':['browser'],'fail_on':'high'})
        self.assertEqual(r['exit_code'],2)
    def test_skipped_required_blocks(self):
        r=evaluate_gate({'checks':[{'id':'browser','status':'skipped'}],'findings':[]},{'required':['browser'],'fail_on':'high'})
        self.assertEqual(r['exit_code'],2)
    def test_high_finding_blocks(self):
        r=evaluate_gate({'checks':[{'id':'browser','status':'completed'}],'findings':[{'severity':'high'}]},{'required':['browser'],'fail_on':'high'})
        self.assertEqual(r['exit_code'],1)
    def test_empty_policy_rejected(self):
        with self.assertRaises(ValueError):evaluate_gate({'checks':[],'findings':[]},{'required':[]})
    def test_semgrep_errors_not_pass(self):
        with self.assertRaises(ValueError):parse_tool_report('semgrep',{'results':[],'errors':[{'message':'parse error'}],'paths':{'scanned':['a.py']}},0)
    def test_semgrep_empty_not_pass(self):
        with self.assertRaises(ValueError):parse_tool_report('semgrep',{},0)
    def test_browser_empty_not_pass(self):
        with self.assertRaises(ValueError):parse_tool_report('browser',{'pages':[]},0)
    def test_browser_http_error_is_finding(self):
        f,c=parse_tool_report('browser',{'pages':[{'url':'https://example.com/','status':500,'consoleErrorCount':0,'blockedRequests':0,'axe':[],'cookies':[],'trackerHosts':[]}]},0)
        self.assertTrue(any(x['severity']=='high' for x in f))
    def test_axe_error_incomplete(self):
        with self.assertRaises(ValueError):parse_tool_report('browser',{'pages':[{'url':'https://example.com/','status':200,'consoleErrorCount':0,'blockedRequests':0,'axe':{'error':'failed'},'cookies':[],'trackerHosts':[]}]},0)
    def test_lighthouse_missing_scores_not_pass(self):
        with self.assertRaises(ValueError):parse_tool_report('lighthouse',{'categories':{}},0)
    def test_zap_empty_not_pass(self):
        with self.assertRaises(ValueError):parse_tool_report('zap',{'site':[]},0)
    def test_url_credentials_query_private_denied(self):
        for url in ['file:///etc/passwd','http://u:p@example.com/','https://example.com/?token=secret','http://127.0.0.1/','http://10.0.0.1/']:
            with self.subTest(url=url),self.assertRaises(ValueError):validate_url(url)
    def test_stale_and_mismatched_evidence(self):
        identity={'commit':None,'dirty':None}
        bundle={'schema_version':2,'scope_digest':'abc','source_identity':identity,'created_at':(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=2)).isoformat(),'reports':[]}
        with self.assertRaises(ValueError):import_evidence(bundle,'abc',source_identity=identity)
        with self.assertRaises(ValueError):import_evidence(bundle,'different',source_identity=identity)
    def test_valid_evidence_and_duplicate_rejection(self):
        row={'tool':'semgrep','returncode':0,'data':{'results':[],'errors':[],'paths':{'scanned':['app.py']}}}
        identity={'commit':'a'*40,'dirty':False}
        bundle={'schema_version':2,'scope_digest':'abc','source_identity':identity,'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'reports':[row]}
        f,c=import_evidence(bundle,'abc',source_identity=identity);self.assertEqual(c[0]['status'],'completed')
        bundle['reports'].append(row)
        with self.assertRaises(ValueError):import_evidence(bundle,'abc',source_identity=identity)
    def test_evidence_requires_matching_git_identity(self):
        identity={'commit':'a'*40,'dirty':False}
        bundle={'schema_version':2,'scope_digest':'abc','source_identity':identity,'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
                'reports':[{'tool':'semgrep','returncode':0,'data':{'results':[],'errors':[],'paths':{'scanned':['app.py']}}}]}
        with self.assertRaises(ValueError):import_evidence(bundle,'abc',source_identity={'commit':'b'*40,'dirty':False})
    def test_sbom_trivy_osv_and_authz_adapters(self):
        sbom={'bomFormat':'CycloneDX','specVersion':'1.6','components':[{'type':'library','name':'demo','version':'1.0'}]}
        f,c=parse_tool_report('sbom',sbom,0);self.assertEqual(c[0]['status'],'completed');self.assertTrue(f)
        trivy={'SchemaVersion':2,'Results':[{'Target':'image','Class':'os-pkgs','Type':'alpine','Vulnerabilities':[{'VulnerabilityID':'CVE-2026-0001','Severity':'HIGH'}]}]}
        f,c=parse_tool_report('trivy',trivy,0);self.assertEqual(f[0]['severity'],'high')
        osv={'results':[{'packages':[{'package':{'name':'demo','version':'1','ecosystem':'PyPI'},'vulnerabilities':[{'id':'GHSA-abcd-1234-5678','database_specific':{'severity':'HIGH'}}]}]}]}
        f,c=parse_tool_report('osv',osv,0);self.assertEqual(c[0]['vulnerabilities'],1)
        authz={'cases':[{'id':'user-read-other','actor':'user-a','action':'read','resource':'user-b/item','expected':'deny','actual':'allow'}]}
        f,c=parse_tool_report('authz',authz,0);self.assertEqual(f[0]['severity'],'high')
        for tool,data in [('sbom',sbom),('trivy',trivy),('osv',osv)]:
            with self.subTest(tool=tool),self.assertRaises(ValueError):parse_tool_report(tool,data,2)
        with self.assertRaises(ValueError):parse_tool_report('authz',{'cases':authz['cases']*2},0)
    def test_incomplete_dependency_reports_rejected(self):
        rows=[('trivy',{'SchemaVersion':2,'Results':[{}]}),
              ('sbom',{'bomFormat':'CycloneDX','specVersion':'1.6','components':[{}]}),
              ('osv',{'results':[{'packages':[{}]}]})]
        for tool,data in rows:
            with self.subTest(tool=tool),self.assertRaises(ValueError):parse_tool_report(tool,data,0)
    def test_authz_policy_requires_all_cases(self):
        report={'checks':[{'id':'authz','status':'completed','case_ids':['own']}],'findings':[]}
        policy={'required':['authz'],'authz_required_cases':['own','other']}
        self.assertEqual(evaluate_gate(report,policy)['exit_code'],2)
        report['checks'][0]['case_ids'].append('other')
        self.assertEqual(evaluate_gate(report,policy)['exit_code'],0)
        with self.assertRaises(ValueError):evaluate_gate(report,{'required':['authz']})
    def test_gate_visible_in_all_formats(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cfg:
            Path(tmp,'app.py').write_text('print("hello")')
            policy=Path(cfg,'policy.json');policy.write_text(json.dumps({'required':['browser']}))
            r=deep_scan(tmp,policy=policy,web=False)
            self.assertEqual(r['exit_code'],2)
            self.assertIn('browser',render(r,'markdown'))
            sarif=json.loads(render(r,'sarif'))
            self.assertFalse(sarif['runs'][0]['invocations'][0]['executionSuccessful'])
            self.assertEqual(sarif['runs'][0]['properties']['gate']['missing_or_incomplete'],['browser'])
    def test_blocked_browser_scope_incomplete(self):
        f,c=parse_tool_report('browser',{'pages':[{'url':'https://example.com/','status':200,'consoleErrorCount':0,'blockedRequests':1,'axe':[],'cookies':[],'trackerHosts':[]}]},0)
        self.assertTrue(all(x['status']=='error' for x in c))
    def test_deleted_secret_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            def git(*args):return subprocess.run(['git','-C',tmp,*args],check=True,capture_output=True)
            git('init','-q');git('config','user.name','Fixture');git('config','user.email','test@example.test')
            token='ghp_'+'Q'*40
            (p/'secret.md').write_text(token);git('add','.');git('commit','-qm','one')
            (p/'secret.md').unlink();git('add','-u');git('commit','-qm','two')
            f,c=scan_history(p)
            self.assertEqual(c['status'],'completed');self.assertTrue(f)
            self.assertNotIn(token,json.dumps(f))
    def test_shallow_history_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);subprocess.run(['git','init','-q',tmp],check=True)
            subprocess.run(['git','-C',tmp,'-c','user.name=Fixture','-c','user.email=x@example.test','commit','--allow-empty','-qm','one'],check=True)
            sha=subprocess.check_output(['git','-C',tmp,'rev-parse','HEAD'],text=True).strip()
            (p/'.git/shallow').write_text(sha+'\n')
            f,c=scan_history(p);self.assertEqual(c['status'],'error')

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','http://example.com/');self.end_headers();return
        self.send_response(200);self.send_header('Content-Type','text/html')
        self.send_header('Set-Cookie','session=SECRET; HttpOnly; SameSite=Lax')
        self.send_header('Set-Cookie','auth=SECRET; SameSite=None')
        self.end_headers();self.wfile.write(b'<html lang="en"><title>Fixture</title><input type="password"></html>')
    def log_message(self,*args):pass

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def test_real_http_and_repeated_cookies(self):
        f,c=scan_http(self.base+'/',allow_loopback=True)
        self.assertEqual(c['status'],'completed')
        self.assertTrue(any(x['rule']=='http.cookie.httponly' for x in f))
        self.assertNotIn('SECRET',json.dumps(f))
    def test_cross_origin_redirect_blocked(self):
        f,c=scan_http(self.base+'/redirect',allow_loopback=True)
        self.assertEqual(c['status'],'error')

if __name__=='__main__':unittest.main()
