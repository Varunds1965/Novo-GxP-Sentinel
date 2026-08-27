"""RUN_OFFLINE_SELF_TEST assertions (TEST-R-014)."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "backend" / "app"


def python_files():
    return [p for p in APP.rglob("*.py")]


class TestNoCloudDependency(unittest.TestCase):
    """The offline guarantee is asserted mechanically, not promised in a README."""

    BANNED_IMPORTS = {
        "openai", "anthropic", "google.generativeai", "boto3", "azure",
        "langchain", "langgraph", "autogen", "crewai", "semantic_kernel",
        "requests", "httpx", "urllib3", "aiohttp",
    }

    def test_no_cloud_or_agent_framework_imports(self):
        offenders = []
        for path in python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    root = name.split(".")[0]
                    if root in self.BANNED_IMPORTS or name in self.BANNED_IMPORTS:
                        offenders.append(f"{path.name}: {name}")
        self.assertEqual(offenders, [], f"cloud or framework imports found: {offenders}")

    def test_no_api_key_is_ever_requested(self):
        for path in python_files():
            text = path.read_text(encoding="utf-8").lower()
            for banned in ("openai_api_key", "anthropic_api_key", "sk-proj", "bearer "):
                self.assertNotIn(banned, text, f"{path.name} references {banned}")

    def test_no_non_loopback_host_is_referenced(self):
        allowed = ("127.0.0.1", "localhost", "gxp-sentinel.local", "schemas.openxmlformats.org")
        for path in python_files():
            for line in path.read_text(encoding="utf-8").splitlines():
                if "http://" in line or "https://" in line:
                    self.assertTrue(
                        any(a in line for a in allowed) or line.strip().startswith(("#", '"', "'", "*", "r\"")),
                        f"{path.name}: non-loopback URL in {line.strip()[:80]}",
                    )

    def test_no_shell_or_code_execution_in_agent_or_tool_layers(self):
        for folder in ("agents", "tools", "rules", "verification", "policy", "actions"):
            for path in (APP / folder).rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                for banned in ("subprocess", "os.system", "eval(", "exec(", "pickle.loads"):
                    self.assertNotIn(banned, text, f"{folder}/{path.name} contains {banned}")

    def test_core_imports_with_no_third_party_packages(self):
        """The zero-install guarantee: the domain must load on a bare interpreter."""
        import importlib

        for module in (
            "app.domain.models",
            "app.domain.enums",
            "app.rules.confidence",
            "app.rules.readiness",
            "app.rules.applicability",
            "app.audit.chain",
            "app.rag.ingestion",
            "app.rag.retrieval",
            "app.security.injection",
        ):
            self.assertIsNotNone(importlib.import_module(module))


class TestSqliteCapability(unittest.TestCase):
    def test_fts5_is_available_in_the_bundled_sqlite(self):
        import sqlite3

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
        conn.execute("INSERT INTO t (body) VALUES ('access review overdue')")
        rows = list(conn.execute("SELECT body FROM t WHERE t MATCH 'overdue'"))
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
