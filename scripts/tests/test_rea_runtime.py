"""Local wrapper tests; real REA/engine behavior is tested by the separate workflow."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('rea_runtime', ROOT/'integrations/rea/runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_install_plan_has_no_side_effects(self):
        prefix = self.root/'new'
        with patch.object(subprocess,'Popen',side_effect=AssertionError('execution not allowed')), contextlib.redirect_stdout(io.StringIO()):
            runtime.install(prefix, False)
        self.assertFalse(prefix.exists())

    def test_existing_prefix_is_never_replaced(self):
        marker=self.root/'keep'; marker.write_text('original')
        with self.assertRaises(ValueError):runtime.install(self.root,True)
        self.assertEqual(marker.read_text(),'original')

    def test_tree_digest_detects_content_and_names(self):
        file=self.root/'a';file.write_bytes(b'one')
        first=runtime.tree_digest(self.root)
        self.assertEqual(first,runtime.tree_digest(self.root))
        file.write_bytes(b'two');second=runtime.tree_digest(self.root)
        self.assertNotEqual(first,second)
        file.rename(self.root/'b');self.assertNotEqual(second,runtime.tree_digest(self.root))

    def test_missing_tree_is_not_an_empty_valid_runtime(self):
        with self.assertRaisesRegex(ValueError,'missing'):
            runtime.tree_digest(self.root/'absent')

    def test_changed_installed_launcher_is_refused(self):
        launcher=self.root/'runtime.py';launcher.write_text('original')
        manifest={'source_commit':runtime.COMMIT,'host':[sys.platform,platform.machine()],
                  'launcher_sha256':runtime.sha(launcher),'reports':{}}
        (self.root/'runtime.json').write_text(json.dumps(manifest))
        launcher.write_text('changed')
        with self.assertRaisesRegex(ValueError,'launcher changed'):
            runtime.verify(self.root)

    def test_missing_qualification_reports_are_refused(self):
        launcher=self.root/'runtime.py';launcher.write_text('example')
        manifest={'source_commit':runtime.COMMIT,'host':[sys.platform,platform.machine()],
                  'launcher_sha256':runtime.sha(launcher),'reports':{}}
        (self.root/'runtime.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'reports are missing'):
            runtime.verify(self.root)

    def test_external_symlink_is_refused(self):
        (self.root/'outside').symlink_to(sys.executable)
        with self.assertRaises(ValueError):runtime.tree_digest(self.root)
        with self.assertRaises(ValueError):runtime.local_path(str(self.root/'outside'))

    def test_client_config_is_parseable_and_limited(self):
        config=tomllib.loads(runtime.config_text(self.root))['mcp_servers']['rea_static']
        self.assertIn('analyze_javascript_application',config['enabled_tools'])
        self.assertIn('inspect_analysis_view',config['enabled_tools'])
        for dangerous in ('gdb_console','capture_process_scenario','instrument_with_frida','install_adb_package'):
            self.assertNotIn(dangerous,config['enabled_tools'])
        self.assertEqual(config['args'][1],'mcp')
        self.assertEqual(config['args'][0],str(self.root/'runtime.py'))

    def test_environment_does_not_inherit_credentials(self):
        with patch.dict(os.environ,{'SECRET_TOKEN':'example','NODE_OPTIONS':'--require untrusted','HTTPS_PROXY':'credential-url'}):
            env=runtime.environment(self.root)
        self.assertNotIn('SECRET_TOKEN',env)
        self.assertNotIn('NODE_OPTIONS',env)
        self.assertNotIn('HTTPS_PROXY',env)
        self.assertEqual(env['HOME'],str(self.root/'home'))

    def test_execution_retains_nonzero_and_original_streams(self):
        prefix=self.root/'output'
        code=runtime.execute([sys.executable,'-c','import sys;print("out");print("err",file=sys.stderr);sys.exit(7)'],self.root,runtime.environment(self.root),prefix)
        self.assertEqual(code,7)
        self.assertEqual(prefix.with_suffix('.stdout').read_text(),'out\n')
        self.assertEqual(prefix.with_suffix('.stderr').read_text(),'err\n')
        with self.assertRaises(FileExistsError):
            runtime.execute([sys.executable,'-c','print("overwrite")'],self.root,{},prefix)

    def test_runtime_profile_does_not_enable_arbitrary_execution(self):
        for operation in ('mcp','setup','eval','capture-browser-scenario','gdb_console'):
            self.assertNotIn(operation,runtime.OPS)
        self.assertEqual(runtime.COMMIT,'20643d4a47b0562aa794f0a15903630c62912c80')

if __name__=='__main__':unittest.main()
