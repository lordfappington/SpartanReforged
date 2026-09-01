"""Synthetic tests for the read-only public-release audit helpers."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/audit/public_release_audit.py"
SPEC = importlib.util.spec_from_file_location("public_release_audit_test", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class PublicReleaseAuditTests(unittest.TestCase):
    def test_binary_magic_classification(self) -> None:
        self.assertEqual(AUDIT.binary_kind(b"\x7fELF" + b"\0" * 12), "ELF executable")
        self.assertEqual(AUDIT.binary_kind(b"\x89PNG\r\n\x1a\n"), "PNG image")
        iso = bytearray(32774)
        iso[32769:32774] = b"CD001"
        self.assertEqual(AUDIT.binary_kind(bytes(iso)), "ISO-9660 image")
        self.assertIsNone(AUDIT.binary_kind(b"plain public documentation\n"))

    def test_secret_finding_reports_type_not_value(self) -> None:
        sample = b"api_key=" + b"A" * 24
        result = AUDIT.findings(sample, AUDIT.SECRET_PATTERNS)
        self.assertEqual(result, ["credential-assignment"])
        self.assertNotIn("A" * 24, result)

    def test_suspicious_extensions_are_case_normalized(self) -> None:
        self.assertIn(".iso", AUDIT.SUSPICIOUS_EXTENSIONS)
        self.assertIn(".tm2", AUDIT.SUSPICIOUS_EXTENSIONS)
        self.assertNotIn(".png", AUDIT.SUSPICIOUS_EXTENSIONS)


if __name__ == "__main__":
    unittest.main()
