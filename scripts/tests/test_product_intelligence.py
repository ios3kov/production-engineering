"""Product Intelligence packaged research helpers: contract and regression tests."""
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "product-intelligence"
SCRIPTS = PLUGIN / "scripts"


def load_tool(name):
    spec = importlib.util.spec_from_file_location("pi_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reviews = load_tool("reviews")
parity = load_tool("parity")
sweep = load_tool("sweep")
listing = load_tool("listing")


class Packaging(unittest.TestCase):
    def test_manifest_and_marketplace(self):
        cfg = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["name"], "product-intelligence")
        self.assertEqual(cfg["version"], "1.0.0")
        self.assertEqual({r["name"] for r in market["plugins"]}, {"general-skills", "product-intelligence"})
        self.assertEqual(next(r for r in market["plugins"] if r["name"] == cfg["name"])["source"]["path"], "./plugins/product-intelligence")
        self.assertIn("replica-skill-LICENSE", (PLUGIN / "references/UPSTREAM.md").read_text())
        self.assertIn("Copyright (c) 2026 Jake Schincariol", (PLUGIN / "references/replica-skill-LICENSE").read_text())

    def test_skills_and_python_compile(self):
        names = {"competitor-recon", "customer-voice", "feature-parity"}
        self.assertEqual({p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir()}, names)
        for name in names:
            lines = (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "---")
            self.assertEqual(lines[1], "name: " + name)
            self.assertTrue(json.loads(lines[2][len("description: "):]))
            self.assertEqual(lines[3], "---")
            self.assertIn("## Source", "\n".join(lines))
        for name in ("reviews", "parity", "sweep", "listing"):
            self.assertGreater((SCRIPTS / (name + ".py")).stat().st_size, 1000)


class ReviewEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csvpath = Path(self.temp.name) / "reviews.csv"
        self.themes, self.requests = reviews.load_themes(str(SCRIPTS / "themes.json"))

    def write(self, rows, columns=("source", "url", "date", "rating", "text", "themes")):
        with self.csvpath.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)
        return reviews.load_reviews(str(self.csvpath))

    def test_multilingual_semantic_annotations(self):
        kept, dropped, dupes = self.write([
            ("app-store", "https://example.org/1", "2026-10-01", "1", "Очень дорого", "pricing"),
            ("reddit", "https://example.org/2", "2026-10-02", "", "功能缺少離線", "platforms"),
            ("g2", "https://example.org/3", "2026-10-03", "2", "Le prix est élevé", "pricing"),
            ("reddit", "https://example.org/4", "2026-10-03", "5", "Все хорошо", "none"),
        ])
        data = reviews.analyse(kept, self.themes, self.requests, require_annotations=True)
        by_id = {item["id"]: item for item in data["themes"]}
        self.assertEqual(data["annotated_reviews"], 4)
        self.assertEqual(data["english_keyword_fallback_reviews"], 0)
        self.assertEqual(by_id["pricing"]["count"], 2)
        self.assertEqual(by_id["platforms"]["count"], 1)
        self.assertEqual((dropped, dupes), (0, 0))
        self.assertEqual(by_id["pricing"]["quotes"][0]["url"], "https://example.org/1")

    def test_unlabelled_review_is_not_semantically_verified(self):
        kept, _, _ = self.write([("app-store", "https://example.org/1", "", "1", "Very expensive", "")])
        with self.assertRaises(reviews.FeedbackError):
            reviews.analyse(kept, self.themes, self.requests, require_annotations=True)
        fallback = reviews.analyse(kept, self.themes, self.requests)
        self.assertEqual(fallback["english_keyword_fallback_reviews"], 1)

    def test_unknown_label_is_rejected(self):
        kept, _, _ = self.write([("app-store", "https://example.org/1", "", "1", "Foo", "fictitious")])
        with self.assertRaises(reviews.FeedbackError):
            reviews.analyse(kept, self.themes, self.requests, require_annotations=True)

    def test_dedup_and_missing_url(self):
        kept, dropped, dupes = self.write([
            ("app-store", "", "", "1", "Expensive", "pricing"),
            ("reddit", "https://example.org/1", "", "1", "Really expensive", "pricing"),
            ("g2", "https://example.org/2", "", "1", "Really expensive", "pricing"),
        ])
        self.assertEqual((len(kept), dropped, dupes), (1, 1, 1))

    def test_cli_enforced_labels(self):
        self.write([("app-store", "https://example.org/1", "", "1", "Expensive", "")])
        with redirect_stderr(io.StringIO()):
            self.assertEqual(reviews.main([str(self.csvpath), "--require-annotations"]), 2)


class FeatureEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / "evidence.txt").write_text("real recorded test output", encoding="utf-8")
        digest = hashlib.sha256((self.path / "evidence.txt").read_bytes()).hexdigest()
        self.records = self.path / "checks.json"
        self.records.write_text(json.dumps({"subject_sha": "build-123", "checks": [
            {"id": "F01-H1", "status": "PASS", "artifact_path": "evidence.txt", "sha256": digest},
            {"id": "F02-H1", "status": "NOT_RUN"},
        ]}), encoding="utf-8")
        self.features = self.path / "features.csv"
        self.features.write_text("feature,area,priority,original,clone,check_id,notes\nCore,main,must,yes,yes,F01-H1,\nOther,main,must,yes,yes,F02-H1,\n", encoding="utf-8")

    def test_pass_with_digest_missing_test_does_not_score(self):
        passed, problems = parity.verified_checks(str(self.records), "build-123")
        self.assertEqual(passed, {"F01-H1"})
        self.assertEqual(problems, [])
        rows, missing = parity.apply_verified(parity.load(str(self.features)), passed)
        scored = parity.score(rows)
        self.assertEqual(scored["feature_score"], 50.0)
        self.assertEqual(missing, ["Other"])

    def test_subject_mismatch_is_error(self):
        with self.assertRaises(parity.MatrixError):
            parity.verified_checks(str(self.records), "different-build")

    def test_artifact_hash_mismatch_cannot_pass(self):
        (self.path / "evidence.txt").write_text("changed", encoding="utf-8")
        passed, warnings = parity.verified_checks(str(self.records), "build-123")
        self.assertNotIn("F01-H1", passed)
        self.assertTrue(any("mismatch" in x for x in warnings))

    def test_undeclared_score_is_explicit(self):
        data = parity.combine(parity.score(parity.load(str(self.features))), [])
        data["evidence_mode"] = "DECLARED ONLY"
        self.assertIn("DECLARED ONLY", parity.render(data))

    def test_must_have_skip_is_flagged(self):
        rows = parity.load(str(self.features))
        rows[0]["clone"] = "skip"
        self.assertTrue(any("must-have skipped" in issue for issue in parity.score(rows)["problems"]))

    def test_fail_under_requires_checks(self):
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(parity.main([str(self.features), "--fail-under", "80"]), 2)


class Branding(unittest.TestCase):
    def test_scan_svg_and_inventory_opaque_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            (d / "icon.svg").write_text('<svg><text>OldBrand</text></svg>', encoding="utf-8")
            (d / "image.png").write_bytes(b"\x89PNG\r\n\x1a\nexample")
            hits = sweep.sweep(directory, avoid=["OldBrand"])
            self.assertTrue(any(h["file"] == "icon.svg" for h in hits))
            self.assertEqual(set(sweep.asset_inventory(directory)), {"icon.svg", "image.png"})
            self.assertFalse(any(h["file"] == "image.png" for h in hits))

    def test_skip_symlinked_files(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            secret = Path(outside) / "secret.txt"
            secret.write_text("OldBrand", encoding="utf-8")
            (Path(directory) / "foreign.txt").symlink_to(secret)
            self.assertFalse(sweep.sweep(directory, avoid=["OldBrand"]))


class StoreLint(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "rules.json"
        self.rules = {
            "checked_at": dt.date.today().isoformat(),
            "sources": {"app_store": "https://developer.apple.com/help/app-store-connect/"},
            "limits": {"app_store": dict(listing.LIMITS["app_store"])},
        }
        self.file.write_text(json.dumps(self.rules), encoding="utf-8")

    def test_dated_source_snapshot_loads(self):
        limits = listing.read_rules(str(self.file))
        self.assertEqual(limits["app_store"]["name"], 30)
        result = listing.lint({"app_store": {"name": "a" * 31, "description": "Hi"}}, limits=limits)
        self.assertTrue(any(issue["level"] == "error" and issue["field"] == "name" for issue in result))

    def test_outdated_snapshot_blocks(self):
        self.rules["checked_at"] = "2020-01-01"
        self.file.write_text(json.dumps(self.rules), encoding="utf-8")
        with self.assertRaises(ValueError):
            listing.read_rules(str(self.file))

    def test_no_snapshot_is_not_ready_to_submit(self):
        store = Path(self.temp.name) / "listing.json"
        store.write_text(json.dumps({"app_store": {"name": "Test", "description": "Real product"}}), encoding="utf-8")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(listing.main([str(store), "--require-current-rules"]), 2)


if __name__ == "__main__":
    unittest.main()
