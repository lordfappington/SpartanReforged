"""Public-safe consistency checks for the complete character roster."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
import unittest

from tools.analysis.character_roster import decoded_psq_fingerprint

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research" / "characters" / "character_roster_manifest.json"
HEX256 = re.compile(r"^[0-9a-f]{64}$")


class CharacterRosterManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_complete_counting_contract(self) -> None:
        summary = self.data["counting_summary"]
        expected = {
            "gameplay_type_definitions": 85,
            "packaged_gameplay_types": 60,
            "geometry_bearing_model_families": 46,
            "unique_high_detail_geometry_signatures": 51,
            "unique_decoded_character_textures": 67,
            "meaningful_visible_appearances": 61,
            "distinct_high_poly_masters": 42,
            "major_derived_variants": 9,
            "texture_skin_only_variants": 10,
            "unresolved_gameplay_types": 20,
        }
        for key, value in expected.items():
            self.assertEqual(summary[key], value, key)

    def test_every_global_type_is_reconciled_once(self) -> None:
        rows = self.data["gameplay_types"]
        self.assertEqual([row["id"] for row in rows], list(range(85)))
        self.assertTrue(all(row["production_action"] for row in rows))
        self.assertEqual(sum(row["packaged"] for row in rows), 60)
        unresolved = {row["id"] for row in rows if row["production_action"] == "HUMAN REVIEW REQUIRED"}
        self.assertIn(38, unresolved)
        self.assertIn(39, unresolved)

    def test_appearance_partition_and_geometry_dedup(self) -> None:
        rows = self.data["appearances"]
        classes = {name: sum(row["classification"] == name for row in rows) for name in ("DISTINCT MASTER", "MAJOR VARIANT", "SKIN VARIANT")}
        self.assertEqual(classes, {"DISTINCT MASTER": 42, "MAJOR VARIANT": 9, "SKIN VARIANT": 10})
        self.assertEqual(len({row["geometry_signature"] for row in rows}), 51)
        self.assertTrue(all(HEX256.fullmatch(row["geometry_signature"]) for row in rows))
        self.assertTrue(all(row["lod_series"] for row in rows))

    def test_known_exact_reuse_is_preserved(self) -> None:
        appearances = {row["id"]: row for row in self.data["appearances"]}
        self.assertEqual(appearances["ROMAN_GRUNT"]["geometry_signature"], appearances["ROMAN_GRUNT_WEAK"]["geometry_signature"])
        self.assertEqual(appearances["ROMAN_GRUNT"]["geometry_signature"], appearances["ROMAN_ZOMBIE_WARRIOR"]["geometry_signature"])
        self.assertEqual(appearances["ROMAN_ARCHER"]["geometry_signature"], appearances["ROMAN_ARCHER_SNOW"]["geometry_signature"])
        self.assertEqual(appearances["GIGANTES_WARRIOR"]["geometry_signature"], appearances["GIGANTES_CAPTAIN"]["geometry_signature"])
        self.assertEqual(appearances["POLLUX"]["geometry_signature"], appearances["POLLUX_ZOMBIE"]["geometry_signature"])
        self.assertEqual(appearances["PLAYER_SPARTAN_V3"]["geometry_signature"], appearances["NEMESIS"]["geometry_signature"])

    def test_model_texture_and_skeleton_inventory(self) -> None:
        self.assertEqual(len(self.data["model_families"]), 46)
        self.assertTrue(all(row["geometry_assets"] for row in self.data["model_families"]))
        self.assertEqual(len(self.data["textures"]), 68)
        self.assertEqual(len({row["tm2"]["rgba_sha256"] for row in self.data["textures"]}), 67)
        self.assertEqual(self.data["skeletons"]["unique_byte_hashes"], 16)
        self.assertEqual(self.data["skeletons"]["meaningful_topology_families"], 6)

    def test_tripo_queue_status_and_size(self) -> None:
        queue = self.data["tripo_high_poly_master_queue"]
        self.assertEqual(len(queue), 42)
        self.assertEqual(queue[0]["appearance_id"], "ROMAN_GRUNT")
        self.assertIn("HUMAN APPROVED / COMPLETE", queue[0]["tripo_status"])
        self.assertEqual(queue[1]["appearance_id"], "SPARTAN_SWORDSMAN")
        self.assertIn("IN PROGRESS", queue[1]["tripo_status"])
        self.assertEqual(sum(row["tripo_status"] == "NOT STARTED" for row in queue), 40)

    def test_manifest_is_metadata_only(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn("game-extracted", text)
        self.assertNotIn("D:\\\\SpartanReforged", text)
        self.assertNotIn("data:image", text.lower())
        for family in self.data["model_families"]:
            for item in family["geometry_assets"] + family["texture_assets"] + family["skeleton_assets"]:
                self.assertRegex(item["sha256"], HEX256)

    def test_decoded_fingerprint_ignores_render_only_final_word(self) -> None:
        def payload(final_word: int) -> bytes:
            records = []
            for index, position in enumerate(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))):
                adc = 2048.0 if index < 2 else 0.0
                records.append(struct.pack("<10fII", *position, adc, 0.0, 0.0, 1.0, 0.0, float(index & 1), float(index >> 1), 0, final_word))
            return struct.pack("<III", 3, 9_999_999, 1) + b"".join(records)

        first, summary = decoded_psq_fingerprint(payload(0))
        second, _ = decoded_psq_fingerprint(payload(0xCDCDCDCD))
        self.assertEqual(first, second)
        self.assertEqual(summary["triangles"], 1)


if __name__ == "__main__":
    unittest.main()
