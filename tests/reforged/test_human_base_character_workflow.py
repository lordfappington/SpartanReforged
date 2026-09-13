"""Safety and architecture tests for the anatomy-first character workflow."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "tools/blender/build_roman_grunt_human_base_build1.py"
COMPOSE_SCRIPT = ROOT / "tools/blender/compose_roman_grunt_human_base_build1_review.py"
DOC = ROOT / "docs/research/characters/HUMAN_BASE_MESH_WORKFLOW.md"


class HumanBaseCharacterWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BUILD_SCRIPT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_scripts_parse_and_outputs_are_private(self):
        ast.parse(COMPOSE_SCRIPT.read_text(encoding="utf-8"))
        self.assertIn('OUTPUT_ROOT = ROOT / "temp" / "roman-human-base-build1"', self.source)
        self.assertNotIn("game-extracted", self.source.lower())
        self.assertNotIn("roman-research/extracted", self.source.lower())

    def test_anatomy_gate_is_a_separate_required_phase(self):
        self.assertIn('choices=("human", "roman")', self.source)
        self.assertIn('if args.phase == "human"', self.source)
        self.assertIn("human-base-review.png", COMPOSE_SCRIPT.read_text(encoding="utf-8"))
        for required in ("human-front.png", "human-side.png", "human-rear.png", "human-head-neck.png", "human-arm-elbow-hand.png", "human-leg-knee-foot.png"):
            self.assertIn(required, self.source)

    def test_realistic_continuous_source_not_primitive_anatomy(self):
        self.assertIn('"Body Male - Realistic"', self.source)
        self.assertIn('body.name = "Human_Body_Continuous_CC0"', self.source)
        self.assertIn('body["license"] = "CC0-1.0"', self.source)
        human_section = self.source[self.source.index("def import_human"):self.source.index("def setup_studio")]
        self.assertNotIn("primitive_cube_add", human_section)
        self.assertNotIn("primitive_cylinder_add", human_section)
        self.assertNotIn("primitive_uv_sphere_add", human_section)

    def test_no_rigging_or_runtime_integration(self):
        self.assertIn('scene["rigging_present"] = False', self.source)
        self.assertIn('scene["runtime_integration"] = False', self.source)
        self.assertNotIn("bpy.ops.object.armature_add", self.source)
        self.assertNotIn("export_scene", self.source)

    def test_documented_license_boundary_and_rejected_predecessors(self):
        for phrase in ("CC0 1.0 Universal", "V1 and V2", "keeps the third-party mesh", "AWAITING HUMAN VISUAL APPROVAL"):
            self.assertIn(phrase, self.doc)


if __name__ == "__main__":
    unittest.main()
