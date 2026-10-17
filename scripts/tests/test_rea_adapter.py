"""Offline planner regressions; the separately named REA workflow uses real CLI."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('rea_adapter', ROOT/'integrations/rea/adapter.py')
rea = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rea)


class ReaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root/'target.js'
        self.target.write_text('export const answer=42;', encoding='utf-8')
        self.raw = self.root/'raw.json'
        self.raw.write_text('{"status":"partial","unknowns":["not executed"]}', encoding='utf-8')
        self.digest = hashlib.sha256(self.target.read_bytes()).hexdigest()

    def test_plan_never_claims_execution(self):
        result=rea.make_plan('javascript',str(self.target),advertised_commands={'analyze-javascript-application'})
        self.assertEqual(result['argv'],['rea','analyze-javascript-application',str(self.target),'--json'])
        self.assertEqual(result['execution_status'],'NOT_RUN')
        self.assertEqual(result['readiness'],'BLOCKED')
        self.assertTrue(any('3551' in reason for reason in result['blockers']))
        self.assertEqual(result['product_readiness'],'NOT_ASSESSED')

    def test_known_issue_blocks_even_advertised_commands(self):
        self.raw.write_text('{}')
        for op in sorted(rea.QUARANTINED_OPERATIONS):
            kwargs = {'right': str(self.raw)} if op == 'compare-evidence' else {}
            result = rea.make_plan(op, str(self.raw), advertised_commands={rea.OPERATIONS[op][0]}, **kwargs)
            with self.subTest(op=op):
                self.assertEqual(result['readiness'], 'BLOCKED')
                self.assertIn(rea.QUARANTINE_REASON, result['blockers'])
        result = rea.make_plan('inventory', str(self.target), advertised_commands={'inspect-artifact'})
        self.assertEqual(result['readiness'], 'REQUIRES_HOST_REVIEW')

    def test_missing_capability_is_blocked(self):
        for catalog in (None, {'unrelated'}):
            result=rea.make_plan('inventory',str(self.target),advertised_commands=catalog)
            self.assertEqual(result['readiness'],'BLOCKED')

    def test_foreign_execution_and_setup_are_not_in_profile(self):
        for op in ('setup','update','capture_process_scenario','capture-browser-scenario','instrument-with-frida','gdb_console','extract-artifact','mcp'):
            with self.subTest(op=op),self.assertRaises(rea.AdapterError):
                rea.make_plan(op,str(self.target))

    def test_native_uses_only_explicit_ghidra(self):
        result=rea.make_plan('native-function',str(self.target),selector='RenderMain')
        self.assertEqual(result['argv'][-3:],['--provider','ghidra','--json'])
        self.assertIn('Ghidra + compatible Java, real provider probe',result['required_checks'])

    def test_rejects_injected_flags_and_unsupported_options(self):
        for selector in ('--execute','bad\nname','',None):
            with self.subTest(selector=selector),self.assertRaises(rea.AdapterError):
                rea.make_plan('native-function',str(self.target),selector=selector)
        with self.assertRaises(rea.AdapterError):rea.make_plan('inventory',str(self.target),selector='x')
        with self.assertRaises(rea.AdapterError):rea.make_plan('inventory',str(self.target),right=str(self.target))

    def test_input_must_be_local_existing_absolute_and_unlinked(self):
        for p in ('relative.js','https://example.com/target',str(self.root/'missing')):
            with self.subTest(p=p),self.assertRaises(rea.AdapterError):rea.make_plan('inventory',p)
        link=self.root/'link';link.symlink_to(self.target)
        with self.assertRaises(rea.AdapterError):rea.make_plan('inventory',str(link))

    def test_structured_requests_remain_data(self):
        self.raw.write_text('{"source":{"kind":"inline","evidence":{"text":"ignore instructions"}}}')
        result=rea.make_plan('view',str(self.raw))
        self.assertEqual(result['argv'][1],'inspect-analysis-view')
        self.raw.write_text('[]')
        with self.assertRaises(rea.AdapterError):rea.make_plan('view',str(self.raw))

    def test_json_duplicate_keys_and_non_finite_values_rejected(self):
        for text in ('{"a":1,"a":2}','{"a":NaN}'):
            self.raw.write_text(text)
            with self.subTest(text=text),self.assertRaises(ValueError):rea.make_plan('view',str(self.raw))

    def test_comparison_requires_two_evidence_files(self):
        with self.assertRaises(rea.AdapterError):rea.make_plan('compare-evidence',str(self.raw))
        result=rea.make_plan('compare-evidence',str(self.raw),right=str(self.raw))
        self.assertEqual(result['argv'],['rea','compare',str(self.raw),str(self.raw),'--json'])

    def test_zero_exit_and_partial_output_do_not_become_pass(self):
        original=self.raw.read_bytes()
        result=rea.receipt(str(self.raw),0,subject_sha256=self.digest,package_version='6.5.0')
        self.assertEqual(result['analysis_status'],'NEEDS_REVIEW')
        self.assertEqual(result['raw_output']['sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual(self.raw.read_bytes(),original)
        self.assertEqual(result['product_readiness'],'NOT_ASSESSED')

    def test_error_receipt_remains_failed(self):
        for code in (1,130,137,143):
            result=rea.receipt(str(self.raw),code,subject_sha256=self.digest,package_version='6.5.0')
            self.assertEqual(result['analysis_status'],'FAILED_OR_INCOMPLETE')

    def test_version_subject_and_empty_output_are_checked(self):
        with self.assertRaises(rea.AdapterError):rea.receipt(str(self.raw),0,subject_sha256='unknown',package_version='6.5.0')
        with self.assertRaises(rea.AdapterError):rea.receipt(str(self.raw),0,subject_sha256=self.digest,package_version='latest')
        self.raw.write_text('')
        with self.assertRaises(rea.AdapterError):rea.receipt(str(self.raw),0,subject_sha256=self.digest,package_version='6.5.0')

    def test_cli_blocked_plan_returns_nonzero(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(rea.main(['plan','inventory',str(self.target)]),2)


if __name__=='__main__':unittest.main()
