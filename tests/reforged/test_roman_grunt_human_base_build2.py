"""Architecture and safety tests for the Roman Grunt Build 2 form gate."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "tools/blender/build_roman_grunt_human_base_build2.py"
COMPOSE = ROOT / "tools/blender/compose_roman_grunt_human_base_build2_review.py"


class RomanGruntBuild2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BUILD.read_text(encoding="utf-8")
        cls.compose = COMPOSE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        ast.parse(cls.compose)

    def test_private_independent_build2_outputs(self):
        self.assertIn('OUTPUT_ROOT = ROOT / "temp" / "roman-human-base-build2"', self.source)
        self.assertIn('BUILD_BLEND = OUTPUT_ROOT / "roman-grunt-human-base-build2.blend"', self.source)
        self.assertNotIn("game-extracted", self.source.lower())

    def test_human_source_and_non_destructive_proportion_workflow(self):
        self.assertIn("Blender Human Base Meshes v1.4.1 / CC0-1.0", self.source)
        self.assertIn("smooth regional shoulder, torso, thigh and calf widening", self.source)
        self.assertIn("body.scale.z *= 0.945", self.source)

    def test_cuirass_is_manufactured_not_anatomy_extracted(self):
        section = self.source[self.source.index("def build_equipment"):self.source.index("def render_views")]
        self.assertNotIn("body_surface_shell", section)
        self.assertIn("independent manufactured closed plate with physical thickness", self.source)
        self.assertIn("Cuirass_Manufactured_Band_", self.source)

    def test_major_equipment_and_form_gates_exist(self):
        for token in (
            "both_feet_have_complete_footwear", "pteruges_surround_more_than_frontal_plane",
            "armour_is_separate_constructed_geometry", "left_right_major_equipment_present",
            "no_floating_major_attachment_by_authored_bounds",
            "no_obvious_neutral_pose_penetrations_by_authored_clearance",
            "height_to_shoulder_width", "torso_to_leg_ratio", "helmet_width_to_height",
            "shield_width_to_height",
        ):
            self.assertIn(token, self.source)

    def test_review_views_and_comparisons_are_complete(self):
        for token in (
            "roman-build2-front.png", "roman-build2-front-three-quarter.png",
            "roman-build2-left-side.png", "roman-build2-rear-three-quarter.png",
            "roman-build2-rear.png", "roman-build2-reference-comparison.png",
            "roman-build2-major-form-comparisons.png",
        ):
            self.assertIn(token, self.source + self.compose)

    def test_form_gate_explicitly_stops_before_production_work(self):
        self.assertIn('scene["rigging_present"]=False', self.source)
        self.assertIn('scene["runtime_integration"]=False', self.source)
        self.assertNotIn("armature_add", self.source)
        self.assertNotIn("export_scene", self.source)
        self.assertIn("AWAITING HUMAN VISUAL APPROVAL — BUILD 2", self.source)


if __name__ == "__main__":
    unittest.main()
