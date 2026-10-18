"""Structural/content regressions only; not an agent or image-quality benchmark."""
from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "general-skills"
BRAIN = PLUGIN / "skills" / "brainstorming"
GEN = PLUGIN / "skills" / "genjutsu"


def read(path):
    return path.read_text(encoding="utf-8")


class VisualSkillsTests(unittest.TestCase):
    def test_optional_scoped_loading(self):
        brain = read(BRAIN / "SKILL.md")
        gen = read(GEN / "SKILL.md")
        self.assertIn("For visual ideation only", brain)
        self.assertIn("when a new concept is needed", brain)
        self.assertIn("force three concepts for a typo", brain)
        self.assertIn("not a second workflow", gen)
        self.assertIn("do not redesign the work", gen)

    def test_local_reference_links_resolve_inside_plugin(self):
        paths = [BRAIN / "SKILL.md", GEN / "SKILL.md", PLUGIN / "README.md", PLUGIN / "CHANGELOG.md"]
        paths += list(BRAIN.glob("references/*.md")) + list(GEN.glob("references/*.md"))
        count = 0
        for path in paths:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", read(path)):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(path=path.name, target=target):
                    self.assertTrue(resolved.is_relative_to(PLUGIN.resolve()))
                    self.assertTrue(resolved.is_file())
                count += 1
        self.assertGreaterEqual(count, 8)

    def test_ten_distinct_mechanisms(self):
        text = read(BRAIN / "references" / "visual-mechanisms.md")
        ids = re.findall(r"^### (V\d{2})\b", text, re.MULTILINE)
        self.assertEqual(ids, [f"V{i:02d}" for i in range(1, 11)])
        self.assertIn("Use selectively", text)
        self.assertIn("not copied examples", text)

    def test_production_brief_and_missing_target_contract(self):
        text = read(GEN / "references" / "visual-production.md")
        for term in ("pixel dimensions", "safe areas", "crop variants", "approved text verbatim", "editable typography", "available target", "cannot guarantee exact rendering"):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_identity_and_product_truth_contract(self):
        text = read(GEN / "references" / "visual-production.md")
        for term in ("identity-defining", "unless the user requests a change", "verified outputs", "illustrative concept", "FSTR", "claim is unverified"):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_separate_review_and_bounded_repair_contract(self):
        text = read(GEN / "references" / "visual-production.md")
        for term in ("| Message |", "| Audience |", "| Concept |", "| Execution |", "NOT_RUN", "Concept problem", "Composition problem", "Text problem", "same failure", "change the production method"):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertIn("Do not turn these judgments into a universal numeric quality score", text)

    def test_preferences_and_reference_trust_contract(self):
        skill = read(GEN / "SKILL.md")
        reference = read(GEN / "references" / "visual-production.md")
        for term in ("Preserve user preferences", "no mandatory palette bans", "untrusted data", "actual production tool's interface"):
            with self.subTest(term=term):
                self.assertIn(term, skill)
        self.assertIn("no mandatory network fetch", reference)
        self.assertIn("No reuse license was established", reference)
        self.assertIn("Approved templates", reference)

    def test_version_docs_and_no_new_executable_resources(self):
        manifest = json.loads(read(PLUGIN / "plugin.json"))
        self.assertEqual(manifest["version"], "1.3.0")
        self.assertIn("1.3.0", read(PLUGIN / "README.md"))
        changelog = read(PLUGIN / "CHANGELOG.md")
        self.assertIn("structural/content regression tests", changelog)
        self.assertIn("NOT_RUN", changelog)
        for root in (BRAIN / "references", GEN / "references"):
            for path in root.rglob("*"):
                if path.is_file():
                    self.assertEqual(path.suffix, ".md")


if __name__ == "__main__":
    unittest.main()
