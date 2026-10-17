"""Bounded extraction experiment on owned loopback pages, never visual QA.

COMPLETED means observations were recorded; admission always stays NOT_ADMITTED.
No public URLs, accounts, stealth mode or external page content are accepted.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

OUT=Path(os.environ['UI_QA_OUTPUT'])
BINARY=Path(os.environ['OBSCURA_BINARY'])
EXPECTED={'title':'Owned fixture','values':['alpha','beta','42']}
EXPR="({title:document.querySelector('h1').textContent,values:Array.from(document.querySelectorAll('li')).map(e=>e.textContent)})"
CONTENT='<h1>Owned fixture</h1><ul><li>alpha</li><li>beta</li><li>42</li></ul><i id="ready"></i>'
PAGES={
 'static':'<!doctype html><title>static</title>'+CONTENT,
 'dom':'<!doctype html><title>dom</title><main></main><script>document.querySelector("main").innerHTML='+json.dumps(CONTENT)+'</script>',
 'async':'<!doctype html><title>async</title><main></main><script>fetch("/payload").then(r=>r.text()).then(s=>document.querySelector("main").innerHTML=s)</script>',
}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        key=self.path.lstrip('/')
        body=CONTENT if key=='payload' else PAGES.get(key)
        self.send_response(200 if body is not None else 404)
        self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write((body or 'Not found').encode())


def decode(value):
    data=json.loads(value)
    return json.loads(data) if isinstance(data,str) else data


def main():
    if not BINARY.is_absolute() or not BINARY.is_file():raise ValueError('Explicit acquired Obscura binary required')
    OUT.mkdir(parents=True,exist_ok=False)
    version=subprocess.run([str(BINARY),'--version'],capture_output=True,text=True,timeout=10,check=True)
    if '0.2.4' not in version.stdout:raise ValueError('Unexpected Obscura version')
    report={'schema_version':1,'execution_status':'RUNNING','candidate_admission':'NOT_ADMITTED',
      'scope':'Three owned extraction fixtures, 3 trials per engine/mode; no visual or public-site benchmark',
      'host':{'platform':platform.platform(),'machine':platform.machine()},
      'obscura_version':version.stdout.strip(),'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
      'fixture_sha256':hashlib.sha256(json.dumps(PAGES,sort_keys=True).encode()).hexdigest(),
      'rss_bytes':None,'memory_status':'NOT_MEASURED','samples':[]}
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            warm=p.chromium.launch()
            report['chromium_version']=warm.version
            try:
                for case in PAGES:
                    for trial in range(3):
                        modes=['obscura-cold','chromium-cold','chromium-reused']
                        if trial%2:modes.reverse()
                        for mode in modes:
                            row={'case':case,'trial':trial,'mode':mode,'correct':False}
                            start=time.perf_counter()
                            try:
                                if mode=='obscura-cold':
                                    proc=subprocess.run([str(BINARY),'fetch',base+'/'+case,'--allow-private-network','--quiet','--timeout','5','--wait','0','--selector','#ready','--eval','JSON.stringify('+EXPR+')'],capture_output=True,text=True,timeout=12,env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/tmp','NO_COLOR':'1'})
                                    row['exit_code']=proc.returncode
                                    row['stdout']=proc.stdout;row['stderr']=proc.stderr
                                    value=decode(proc.stdout) if proc.returncode==0 else None
                                else:
                                    browser=p.chromium.launch() if mode=='chromium-cold' else warm
                                    context=browser.new_context(service_workers='block')
                                    try:
                                        page=context.new_page();page.goto(base+'/'+case,timeout=5000)
                                        page.wait_for_selector('#ready',state='attached',timeout=5000)
                                        value=page.evaluate(EXPR)
                                    finally:
                                        context.close()
                                        if mode=='chromium-cold':browser.close()
                                    row['value']=value
                                row['correct']=value==EXPECTED
                            except Exception as error:row['error']=str(error)
                            row['elapsed_ms']=round((time.perf_counter()-start)*1000,3)
                            report['samples'].append(row)
            finally:warm.close()
        report['execution_status']='COMPLETED'
        report['summary']={}
        for mode in ('obscura-cold','chromium-cold','chromium-reused'):
            rows=[r for r in report['samples'] if r['mode']==mode]
            good=[r['elapsed_ms'] for r in rows if r['correct']]
            report['summary'][mode]={'correct':sum(r['correct'] for r in rows),'total':len(rows),
              'median_correct_ms':statistics.median(good) if good else None,
              'all_attempts_ms':[r['elapsed_ms'] for r in rows]}
        report['decision']='PILOT_ONLY_NO_PRODUCTION_OR_VISUAL_QA'
        report['limitations']=['Latency is illustrative at n=3 per page; no generalized speed claim.',
          'Cold mode includes process/browser start and close; reused Chromium excludes browser startup.',
          'Persistent Obscura/CDP, memory, screenshots, public sites and hostile inputs were not qualified.',
          'A completed experiment is not a passing candidate; inspect exact field correctness and all failures.']
    finally:
        server.shutdown();server.server_close();thread.join()
        (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('execution_status','candidate_admission','summary','decision')}))
if __name__=='__main__':main()
