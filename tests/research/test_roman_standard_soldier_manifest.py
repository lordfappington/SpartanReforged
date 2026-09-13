"""Public-safe consistency checks for the Roman soldier evidence manifest."""

from __future__ import annotations

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research" / "characters" / "roman_standard_soldier_manifest.json"
HEX256 = re.compile(r"^[0-9a-f]{64}$")


class RomanStandardSoldierManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_identity_and_relationships_are_specific(self) -> None:
        self.assertEqual(self.data["subject"]["canonical_gameplay_name"], "ROMAN_GRUNT")
        self.assertEqual(self.data["subject"]["character_type_id"], 3)
        self.assertEqual(self.data["subject"]["asset_family"], "RMN_GRNT")
        self.assertEqual(self.data["source"]["character_root"], "DATA/CHR_MDLS/RMN_GRNT")
        self.assertEqual(
            self.data["source"]["presence_table"],
            "DATA/ENV/LEVEL01/ENTITIES/CHAR_TYPES.BIN",
        )

    def test_lods_are_complete_monotonic_and_topologically_consistent(self) -> None:
        lods = self.data["lods"]
        self.assertEqual([lod["lod"] for lod in lods], list(range(5)))
        for field in ("stream_records", "unique_positions", "triangles"):
            values = [lod[field] for lod in lods]
            self.assertEqual(values, sorted(values, reverse=True))
        for lod in lods:
            self.assertEqual(lod["triangles"], lod["primary_triangles"] + lod["shield_triangles"])
            self.assertRegex(lod["sha256"], HEX256)

    def test_skeleton_texture_and_animation_contract(self) -> None:
        self.assertEqual(self.data["skeleton"]["bone_count"], 16)
        self.assertEqual(len(self.data["skeleton"]["parents"]), 16)
        self.assertFalse(self.data["skeleton"]["bone_names_present"])
        self.assertEqual(self.data["texture"]["dimensions"], [256, 256])
        self.assertEqual(self.data["texture"]["decoded_alpha_range"], [255, 255])
        self.assertTrue(all(item["frames"] > 0 for item in self.data["animations"]["representative"]))

    def test_variant_geometry_claims_do_not_flatten_role_families(self) -> None:
        weak = next(item for item in self.data["variants"] if item["name"] == "WEAK")
        self.assertEqual(weak["geometry"], "byte-identical to standard")
        rejected = {item["gameplay_name"] for item in self.data["rejected_candidates"]}
        self.assertIn("ROMAN_GRUNT_HEAVY", rejected)
        self.assertIn("ROMAN_CENT", rejected)
        self.assertIn("ROMAN_ARCHER", rejected)

    def test_manifest_contains_metadata_only(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8").lower()
        self.assertNotIn("data:image", text)
        self.assertNotIn("base64", text)
        tracked = [path.lower() for path in self.data["private_outputs"].values() if isinstance(path, str)]
        self.assertTrue(any(path.endswith(".obj") for path in tracked))
        self.assertEqual(self.data["private_outputs"]["copyright_status"], "never commit or redistribute")


if __name__ == "__main__":
    unittest.main()
