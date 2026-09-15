"""Public-safe consistency checks for the Spartan swordsman evidence manifest."""

from __future__ import annotations

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research" / "characters" / "spartan_swordsman_manifest.json"
HEX256 = re.compile(r"^[0-9a-f]{64}$")


class SpartanSwordsmanManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_identity_chain_is_specific_and_not_the_player(self) -> None:
        subject = self.data["subject"]
        self.assertEqual(subject["canonical_gameplay_name"], "SPARTAN_SWORDSMAN")
        self.assertEqual(subject["character_type_id"], 11)
        self.assertEqual(subject["asset_family"], "SPT_SWRD")
        self.assertEqual(self.data["source"]["character_root"], "DATA/CHR_MDLS/SPT_SWRD")
        self.assertEqual(self.data["player_relationship"]["classification"], "separate NPC geometry using the shared humanoid rig layout, not the player mesh")

    def test_candidate_decision_retains_distinct_hoplite(self) -> None:
        candidates = {item["gameplay_name"]: item for item in self.data["candidate_disposition"]}
        self.assertIn("SPARTAN_SWORDSMAN", candidates)
        self.assertIn("SPARTAN_HOPLITE", candidates)
        self.assertIn("distinct spear/hoplite", candidates["SPARTAN_HOPLITE"]["disposition"])
        self.assertEqual(len(self.data["archive_presence"]), 17)

    def test_lods_are_complete_monotonic_and_topologically_consistent(self) -> None:
        lods = self.data["lods"]
        self.assertEqual([lod["lod"] for lod in lods], list(range(5)))
        for field in ("stream_records", "unique_positions", "triangles"):
            values = [lod[field] for lod in lods]
            self.assertEqual(values, sorted(values, reverse=True))
        for lod in lods:
            self.assertEqual(lod["triangles"], lod["primary_triangles"] + lod["shield_triangles"])
            self.assertRegex(lod["sha256"], HEX256)

    def test_skeleton_equipment_and_anatomical_sides_are_coherent(self) -> None:
        skeleton = self.data["skeleton"]
        self.assertEqual(skeleton["bone_count"], 16)
        self.assertEqual(len(skeleton["parents"]), 16)
        self.assertIn("SPT_HOPL", skeleton["exact_shared_families"])
        self.assertNotEqual(skeleton["sha256"], skeleton["same_topology_not_byte_identical"]["player_spartan_sha256"])
        sides = self.data["anatomical_equipment"]
        self.assertEqual(sides["character_left_hand"], "sword")
        self.assertEqual(sides["character_right_arm"], "shield")
        self.assertEqual(self.data["equipment"]["shield"]["bone_id"], 12)
        self.assertEqual(self.data["equipment"]["weapon"]["bone_id"], 9)

    def test_texture_and_animation_contract(self) -> None:
        texture = self.data["texture"]
        self.assertEqual(texture["dimensions"], [256, 256])
        self.assertEqual(texture["decoded_alpha_range"], [255, 255])
        self.assertEqual(texture["material_slots"], 1)
        animations = self.data["animations"]
        self.assertEqual(animations["generic_swordsman_namespace"], "DATA/ANIMS/GREEK/SWORD")
        self.assertNotEqual(animations["generic_swordsman_namespace"], animations["player_only_comparison_namespace"])
        self.assertEqual(animations["generic_swordsman_clip_count_in_level04"], 19)
        self.assertEqual(animations["bounded_files_checked"], 30)
        self.assertTrue(all(item["frames"] > 0 for item in animations["representative"]))
        self.assertTrue(all(re.fullmatch(HEX256, item["sha256"]) for item in animations["representative"]))

    def test_manifest_contains_metadata_only(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8").lower()
        self.assertNotIn("data:image", text)
        self.assertNotIn("base64", text)
        private = self.data["private_outputs"]
        self.assertEqual(private["copyright_status"], "never commit or redistribute")
        self.assertTrue(private["obj"].endswith(".obj"))
        self.assertTrue(private["turnaround"].endswith(".png"))


if __name__ == "__main__":
    unittest.main()
