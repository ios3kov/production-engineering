"""Offline contracts only; actual browser tests live in integrations/browser-qa."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[2]
PLUGIN=ROOT/'plugins/general-skills'
spec=importlib.util.spec_from_file_location('ui_collector',ROOT/'integrations/browser-qa/collector.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

class InterfaceAdoptionTests(unittest.TestCase):
    def test_relevant_skills_link_local_supplement(self):
        for name in ('genjutsu','motion-design','design-dna'):
            p=PLUGIN/'skills'/name/'SKILL.md'
            self.assertIn('interface-practice.md',p.read_text())
        for p in PLUGIN.rglob('*.md'):
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
                if '://' in target or target.startswith('#'):continue
                q=(p.parent/target.split('#')[0]).resolve()
                self.assertTrue(q.is_relative_to(PLUGIN.resolve()),(p,target))
                self.assertTrue(q.is_file(),(p,target))
    def test_all_nine_sources_and_limits_are_retained(self):
        text=(PLUGIN/'references/interface-sources.md').read_text()
        self.assertEqual(re.findall(r'^## (S\d{2})',text,re.M),[f'S{i:02}' for i in range(1,10)])
        for phrase in ('motion counts','No model training','not a passing extraction'):
            self.assertIn(phrase,text)
        recon=(ROOT/'plugins/product-intelligence/skills/competitor-recon/SKILL.md').read_text()
        self.assertIn('Optional UI-flow reference source',recon)
        self.assertIn('without separate written permission',recon)
    def test_bounds_reject_before_browser_calls(self):
        page=Mock()
        for kwargs in ({'selectors':[]},{'selectors':['']},{'selectors':['x']*33},{'max_elements':True},{'max_elements':5001},{'timeout_ms':0}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):collector.measure_ui(page,**kwargs)
        page.evaluate.assert_not_called();page.wait_for_function.assert_not_called()
    def test_empty_missing_and_truncated_scope_stays_incomplete(self):
        for scope in ({'missingSelectors':[],'truncated':False,'measured':0},{'missingSelectors':['x'],'truncated':False,'measured':1},{'missingSelectors':[],'truncated':True,'measured':1}):
            page=Mock();page.evaluate.return_value={'coverage':scope}
            self.assertEqual(collector.measure_ui(page)['inspection_status'],'INCOMPLETE')
    def test_complete_measurement_never_becomes_pass(self):
        page=Mock();page.evaluate.return_value={'coverage':{'missingSelectors':[],'truncated':False,'measured':1},'candidates':[]}
        self.assertEqual(collector.measure_ui(page)['inspection_status'],'NEEDS_REVIEW')
    def test_browser_failures_are_not_hidden(self):
        page=Mock();page.wait_for_function.side_effect=TimeoutError('font')
        with self.assertRaises(TimeoutError):collector.measure_ui(page)
        page.evaluate.assert_not_called()
    def test_collector_has_no_runtime_dependency_or_navigation(self):
        page=Mock();page.evaluate.return_value={'coverage':{'missingSelectors':[],'truncated':False,'measured':1}}
        collector.measure_ui(page)
        page.goto.assert_not_called()
        self.assertNotIn('MOTION_MIN',collector.MEASUREMENT)
        self.assertNotIn('willChange',collector.MEASUREMENT)

if __name__=='__main__':unittest.main()
