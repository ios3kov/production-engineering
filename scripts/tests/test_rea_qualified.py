"""Offline integrity tests; real CLI qualification is a separate workflow."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('rea_qualified', ROOT / 'integrations/rea/qualified.py')
qualified = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualified)


class QualifiedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / 'runtime'; (self.runtime / 'scripts').mkdir(parents=True)
        self.entry = self.runtime / 'scripts/rea.mjs'; self.entry.write_bytes(b'example fixture only')
        self.manifest = self.root / 'manifest.json'
        self.entries = [{'path':'scripts/rea.mjs','sha256':hashlib.sha256(self.entry.read_bytes()).hexdigest(),'bytes':self.entry.stat().st_size}]

    def write_manifest(self):
        self.manifest.write_text(json.dumps({'runtime_id':'rea-6.5.0-patch3552.1','entries':self.entries}))
        return hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def test_exact_fixture_matches(self):
        digest = self.write_manifest()
        result = qualified.verify_tree(self.runtime,self.manifest,digest)
        self.assertEqual(result['runtime_id'],'rea-6.5.0-patch3552.1')

    def test_unapproved_manifest_is_rejected(self):
        self.write_manifest()
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,'0'*64)

    def test_same_length_changed_file_is_rejected(self):
        digest = self.write_manifest(); self.entry.write_bytes(b'x'*self.entry.stat().st_size)
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_extra_runtime_file_is_rejected(self):
        digest = self.write_manifest(); (self.runtime/'scripts/extra.mjs').write_text('extra')
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_path_traversal_and_duplicate_entries_are_rejected(self):
        original = dict(self.entries[0])
        for entries in ([dict(original,path='../outside')],[original,original],[dict(original,path='scripts/../rea.mjs')]):
            self.entries=entries; digest=self.write_manifest()
            with self.subTest(entries=entries),self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_link_cannot_replace_regular_file(self):
        digest=self.write_manifest(); self.entry.unlink(); self.entry.symlink_to(self.manifest)
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_declared_link_cannot_escape_runtime(self):
        self.entry.unlink(); self.entry.symlink_to(self.root/'manifest.json')
        self.entries=[{'path':'scripts/rea.mjs','link':str(self.root/'manifest.json')}];digest=self.write_manifest()
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_empty_manifest_is_rejected(self):
        self.entries=[];digest=self.write_manifest()
        with self.assertRaises(ValueError): qualified.verify_tree(self.runtime,self.manifest,digest)

    def test_commands_are_only_qualified_static_operations(self):
        self.assertEqual(set(qualified.COMMANDS),{'javascript','view','feature-trace','semantic-trace','compare-applications'})
        for forbidden in ('mcp','setup','gdb_console','instrument-with-frida','capture-process','update'):
            self.assertNotIn(forbidden,qualified.COMMANDS.values())

    def test_json_duplicates_and_nonfinite_values_are_rejected(self):
        for text in ('{"entries":[],"entries":[1]}','{"value":NaN}'):
            self.manifest.write_text(text)
            with self.subTest(text=text),self.assertRaises(ValueError): qualified.load(self.manifest)


if __name__ == '__main__': unittest.main()
