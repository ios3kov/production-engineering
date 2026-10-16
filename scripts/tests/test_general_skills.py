"""Validate optional Work/Codex plugin structure without external dependencies."""
from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "general-skills"
NAMES = {
    "design-dna",
    "genjutsu",
    "motion-design",
    "gsap",
    "threejs",
    "brainstorming",
    "research-methodology",
    "fact-check",
}


class GeneralSkillsTests(unittest.TestCase):
    def test_marketplace_and_manifest(self):
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "general-skills")
        self.assertEqual(manifest["version"], "1.0.0")
        self.assertTrue(manifest["description"])
        self.assertEqual(marketplace["name"], "ios3kov-skills")
        entries = marketplace["plugins"]
        self.assertEqual({entry['name'] for entry in entries}, {'general-skills', 'product-intelligence'})
        self.assertEqual(entries[0]["name"], manifest["name"])
        self.assertEqual(entries[0]["source"]["source"], "local")
        self.assertEqual(entries[0]["source"]["path"], "./plugins/general-skills")

    def test_skill_files(self):
        skills_dir = PLUGIN / "skills"
        actual = {path.name for path in skills_dir.iterdir() if path.is_dir()}
        self.assertEqual(actual, NAMES)
        for name in sorted(NAMES):
            with self.subTest(skill=name):
                path = skills_dir / name / "SKILL.md"
                self.assertTrue(path.is_file())
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()
                self.assertEqual(lines[0], "---")
                self.assertEqual(lines[1], f"name: {name}")
                self.assertTrue(lines[2].startswith("description: "))
                # JSON-quoted strings are also YAML scalar strings.
                description = json.loads(lines[2].removeprefix("description: "))
                self.assertTrue(description.strip())
                self.assertEqual(lines[3], "---")
                self.assertIn("## Source", content)
                self.assertLess(len(content), 25000)


if __name__ == "__main__":
    unittest.main()
