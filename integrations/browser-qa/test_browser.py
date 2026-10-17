"""Real browsers + generated fixture, not acceptance of a user's product."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from playwright.sync_api import sync_playwright, expect
from collector import measure_ui

HERE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('UI_QA_OUTPUT', '/tmp/pe-ui-qa'))
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path.startswith('/fixture'):
            content=(HERE/'fixture.html').read_bytes(); mime='text/html; charset=utf-8'; status=200
        elif self.path=='/data':
            content=json.dumps({'name':'A','count':0,'items':[]}).encode(); mime='application/json'; status=200
        else: content=b'Not found'; mime='text/plain'; status=404
        self.send_response(status); self.send_header('Content-Type',mime);self.end_headers();self.wfile.write(content)

class BrowserQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True,exist_ok=True)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start()
        cls.engine=os.environ.get('UI_QA_BROWSER','chromium')
        launch={}
        if cls.engine=='chromium' and os.environ.get('UI_QA_CHROMIUM_EXECUTABLE'): launch['executable_path']=os.environ['UI_QA_CHROMIUM_EXECUTABLE']
        cls.browser=getattr(cls.pw,cls.engine).launch(**launch)
        (OUT/(cls.engine+'-environment.json')).write_text(json.dumps({'browser':cls.engine,'browser_version':cls.browser.version,'playwright':importlib.metadata.version('playwright'),'revision':os.environ.get('TEST_REVISION'),'fixture_sha256':hashlib.sha256((HERE/'fixture.html').read_bytes()).hexdigest(),'product_readiness':'NOT_ASSESSED'}))
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':390,'height':844},locale='en-US',reduced_motion='no-preference',service_workers='block')
        self.context.route('**/*',lambda route: route.continue_() if route.request.url.startswith(self.base+'/') else route.abort())
        self.context.tracing.start(screenshots=True,snapshots=True)
        self.page=self.context.new_page()
    def tearDown(self):
        prefix=OUT/(self.engine+'-'+self._testMethodName)
        try:
            self.page.screenshot(path=str(prefix)+'.png',full_page=True)
            self.context.tracing.stop(path=str(prefix)+'.trace.zip')
        finally:
            self.context.close()
    def open(self,query=''):
        self.page.goto(self.base+'/fixture'+query)
        self.page.wait_for_selector('body[data-ready=yes]')
    def test_worst_case_data_and_variants(self):
        data={'name':'ОченьДлинноеИмя'*20,'count':999999999999,'items':[]}
        self.page.route('**/data',lambda route:route.fulfill(json=data))
        self.open()
        expect(self.page.locator('#name')).to_have_text(data['name'])
        expect(self.page.locator('#count')).to_have_text(str(data['count']))
        expect(self.page.locator('#empty')).to_be_visible()
        for width in (320,768,1440):
            self.page.set_viewport_size({'width':width,'height':900})
            for variant in ('dense','comfortable'):
                self.page.select_option('#variant',variant)
                report=measure_ui(self.page)
                self.assertNotIn('horizontal-overflow',[x['kind'] for x in report['candidates']])
                self.assertEqual(report['inspection_status'],'NEEDS_REVIEW')
        self.assertNotIn('score',report)
    def test_measured_defects_are_candidates(self):
        self.open('?defects=1')
        self.page.wait_for_function("document.getElementById('broken').complete")
        self.page.wait_for_function("Array.from(document.fonts).some(f=>f.status==='error')")
        report=measure_ui(self.page)
        kinds={x['kind'] for x in report['candidates']}
        self.assertTrue({'clipped-content','horizontal-overflow','hit-test-obstruction','broken-image','font-load-error'}<=kinds,kinds)
        wrapped=self.page.locator('#wrapped').evaluate('(e)=>e.getBoundingClientRect().height')
        self.assertGreater(wrapped,20)
        (OUT/(self.engine+'-measurements.json')).write_text(json.dumps(report,indent=2))
        self.assertEqual(report['release_readiness'],'not_assessed')
    def test_missing_and_truncated_scope_not_complete(self):
        self.open()
        self.assertEqual(measure_ui(self.page,('#does-not-exist',))['inspection_status'],'INCOMPLETE')
        self.assertEqual(measure_ui(self.page,max_elements=1)['inspection_status'],'INCOMPLETE')
        with self.assertRaises(ValueError):measure_ui(self.page,[])
    def test_error_retains_input_and_retry(self):
        self.open();self.page.fill('#draft','Edited draft survives')
        attempts=[]
        def save(route):
            attempts.append(route.request.post_data)
            route.fulfill(status=503 if len(attempts)==1 else 200,body='{}')
        self.page.route('**/save',save)
        self.page.click('#save')
        expect(self.page.locator('#status')).to_contain_text('Your draft is kept')
        expect(self.page.locator('#draft')).to_have_value('Edited draft survives')
        self.page.click('#save');expect(self.page.locator('#status')).to_have_text('Changes saved')
        self.assertEqual(len(attempts),2)
        self.assertEqual(json.loads(attempts[1])['draft'],'Edited draft survives')
    def test_repeated_toggle_and_reduced_motion(self):
        self.open()
        for _ in range(3):self.page.locator('#toggle').click()
        expect(self.page.locator('#toggle')).to_have_attribute('aria-expanded','true')
        self.page.wait_for_function("getComputedStyle(document.getElementById('panel')).transform.includes('70')")
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.locator('#panel').evaluate('(e)=>getComputedStyle(e).transitionDuration'),'0s')
        self.page.click('#toggle');expect(self.page.locator('#toggle')).to_have_attribute('aria-expanded','false')
    def test_cancel_drag_and_keyboard_focus(self):
        self.open();drag=self.page.locator('#drag');box=drag.bounding_box()
        self.page.mouse.move(box['x']+10,box['y']+10);self.page.mouse.down()
        expect(drag).to_have_attribute('data-dragging','true')
        self.page.keyboard.press('Escape');expect(drag).to_have_attribute('data-dragging','false')
        self.page.mouse.up();self.page.locator('#toggle').focus();self.page.keyboard.press('Enter')
        expect(self.page.locator('#toggle')).to_be_focused()
        expect(self.page.locator('#toggle')).to_have_attribute('aria-expanded','true')

if __name__=='__main__':unittest.main(verbosity=2)
