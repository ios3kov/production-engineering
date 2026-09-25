import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from readiness import DOMAINS, plan, evaluate, load

class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime.now(dt.timezone.utc)
        self.passport={'schema_version':1,'project':'fixture','environment':'staging','components':['api'],
            'release':{'commit':'a'*40,'artifact_sha256':'b'*64,'scope_digest':'c'*64},
            'domains':{d:{'applicable':True,'checks':[{'id':d,'component':'api','method':'automated','criterion':'Fixture acceptance','max_age_hours':24}]} for d in DOMAINS}}
        self.evidence={'plan_digest':plan(self.passport)['plan_digest'],'release':self.passport['release'].copy(),'environment':'staging',
            'results':[{'id':d,'status':'PASS','method':'automated','producer':'fixture','version':'1','created_at':self.now.isoformat(),'evidence_sha256':'d'*64,'exit_code':0} for d in DOMAINS]}
    def test_complete_and_failed(self):
        self.assertEqual(evaluate(self.passport,self.evidence,[])['exit_code'],0)
        self.evidence['results'][0]['status']='FAIL'
        self.assertEqual(evaluate(self.passport,self.evidence,[])['exit_code'],1)
    def test_missing_stale_and_failed_process(self):
        for mutation in ['missing','stale','exit']:
            e=copy.deepcopy(self.evidence)
            if mutation=='missing':e['results'].pop()
            elif mutation=='stale':e['results'][0]['created_at']=(self.now-dt.timedelta(days=2)).isoformat()
            else:e['results'][0]['exit_code']=2
            with self.subTest(mutation=mutation):self.assertEqual(evaluate(self.passport,e,[])['exit_code'],2)
    def test_bindings_and_duplicates(self):
        for field,value in [('plan_digest','x'),('environment','production'),('release',{})]:
            e=copy.deepcopy(self.evidence);e[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):evaluate(self.passport,e,[])
        self.evidence['results'].append(self.evidence['results'][0])
        with self.assertRaises(ValueError):evaluate(self.passport,self.evidence,[])
    def test_issue_lifecycle(self):
        issue={'id':'issue','check_id':'security','severity':'high','state':'confirmed'}
        self.assertEqual(evaluate(self.passport,self.evidence,[issue])['exit_code'],1)
        issue.update(state='accepted_risk',owner='reviewer',reason='fixture',decision_sha256='e'*64,expires_at=(self.now+dt.timedelta(days=1)).isoformat())
        self.assertEqual(evaluate(self.passport,self.evidence,[issue])['exit_code'],0)
        issue['expires_at']=(self.now-dt.timedelta(days=1)).isoformat()
        self.assertEqual(evaluate(self.passport,self.evidence,[issue])['exit_code'],1)
        issue.update(state='fixed',retest_check='security')
        self.assertEqual(evaluate(self.passport,self.evidence,[issue])['exit_code'],0)
    def test_domain_exclusions(self):
        self.passport['domains']['data']={'applicable':False,'reason':''}
        with self.assertRaises(ValueError):plan(self.passport)
        self.passport['domains']['data']['reason']='No persistent storage'
        self.assertIn('data',plan(self.passport)['not_applicable'])
    def test_cli_and_duplicate_json(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            for name,data in [('passport',self.passport),('evidence',self.evidence),('issues',[])]:
                (p/name).write_text(json.dumps(data))
            result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'readiness.py'),str(p/'passport'),'--evidence',str(p/'evidence'),'--issues',str(p/'issues')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['coverage']),10)
            (p/'bad').write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):load(p/'bad')
