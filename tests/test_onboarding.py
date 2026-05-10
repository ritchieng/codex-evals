import tempfile
import unittest
from pathlib import Path

from codex_evals.onboarding import build_doctor, ensure_repo_marketplace, init_onboarding, run_demo


class OnboardingTests(unittest.TestCase):
    def test_demo_renders_immediate_report(self):
        markdown = run_demo()

        self.assertIn("# Eval Report", markdown)
        self.assertIn("## 3 Strongest Signals", markdown)
        self.assertIn("## What To Do Next", markdown)

    def test_doctor_checks_repo_plugin_surface(self):
        report = build_doctor(".")
        checks = {check["name"]: check for check in report["checks"]}

        self.assertEqual(checks["Plugin manifest"]["status"], "ok")
        self.assertEqual(checks["/eval command"]["status"], "ok")
        self.assertEqual(checks["Skill: evaluate-conversation"]["status"], "ok")
        self.assertEqual(checks["Packaged marketplace"]["status"], "ok")
        self.assertEqual(checks["Report engine"]["status"], "ok")

    def test_init_can_write_demo_file_without_plugin_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = init_onboarding(root=tmp, install_plugin=False)
            demo_path = Path(tmp) / ".codex-evals" / "onboarding-thread.md"

            self.assertTrue(demo_path.exists())
            self.assertIn("Plugin registration", output)
            self.assertIn("codex-evals Onboarding", output)

    def test_marketplace_registration_writes_repo_local_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ensure_repo_marketplace(tmp)
            marketplace = Path(tmp) / ".agents" / "plugins" / "marketplace.json"

            self.assertEqual(result["status"], "ok")
            self.assertTrue(marketplace.exists())
            self.assertIn("./plugins/codex-evals", marketplace.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
