"""Synthetic, non-copyrighted tests for the MODELS parser/export path."""

from __future__ import annotations

import pathlib
import struct
import sys
import tempfile
import unittest


CONVERSION = pathlib.Path(__file__).resolve().parents[2] / "tools" / "conversion"
sys.path.insert(0, str(CONVERSION))

from export_models_gltf import (  # noqa: E402
    MIRRORED_REPEAT,
    REPEAT,
    VALIDATED_MODERN_V_MODE,
    TextureImageInfo,
    TextureReference,
    build_gltf,
    validate_consistency,
    validate_external_images,
    validate_gltf,
)
from spartan_models import (  # noqa: E402
    AabData,
    Batch,
    Descriptor,
    MaterialRecord,
    ModelsData,
    ModelsFormatError,
    decode_uv,
    parse_mtl,
    parse_models_bin,
    reconstruct_triangles,
    select_descriptors,
    transform_position,
)


def synthetic_model(two_materials: bool = False) -> ModelsData:
    positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
    controls = (0x8000, 0x8000, 0, 0)
    uv = ((0, 0), (4096, 0), (0, 4096), (4096, 4096))
    attrs = ((1, 2, 3, 0x80),) * 4
    descriptors = [Descriptor(0, 0x40, 0x80, 0xFFFF, 0, 11)]
    batches = [Batch(0, 0, 0, 0, positions, controls, uv, attrs, 0x80)]
    materials = [MaterialRecord(0, "SYNTHETIC_A", ("SYNTHETIC_A",))]
    refs = {0}
    if two_materials:
        descriptors.append(Descriptor(1, 0xC0, 0x80, 7, 1, 11))
        batches.append(Batch(1, 0, 1, 1, positions, controls, uv, attrs, 0x80))
        materials.append(MaterialRecord(1, "SYNTHETIC_B", ("SYNTHETIC_B",)))
    return ModelsData(
        tuple(descriptors), tuple(batches), tuple(materials),
        AabData(frozenset(refs), tuple(sorted(refs)), 1, 0, 1),
        (0,) * 8,
    )


class TopologyTests(unittest.TestCase):
    def test_adc_strip_topology_and_parity(self) -> None:
        controls = (0x8000, 0x8000, 0, 0, 0x8000, 0)
        self.assertEqual(reconstruct_triangles(controls), ((0, 1, 2), (2, 1, 3), (4, 3, 5)))

    def test_winding_reversal(self) -> None:
        self.assertEqual(reconstruct_triangles((0x8000, 0x8000, 0), reverse=True), ((0, 2, 1),))

    def test_unknown_control_rejected(self) -> None:
        with self.assertRaises(ModelsFormatError):
            reconstruct_triangles((0x8000, 0x8000, 123))


class AttributeTests(unittest.TestCase):
    def test_q4_12_uv_and_flip(self) -> None:
        self.assertEqual(VALIDATED_MODERN_V_MODE, "source")
        self.assertEqual(decode_uv((-4096, 6144), "source"), (-1.0, 1.5))
        self.assertEqual(decode_uv((-4096, 6144), "flip"), (-1.0, -0.5))

    def test_coordinate_conversion(self) -> None:
        self.assertEqual(transform_position((1.0, 2.0, 3.0), "source"), (1.0, 2.0, 3.0))
        self.assertEqual(transform_position((1.0, 2.0, 3.0), "gltf"), (1.0, 2.0, -3.0))
        self.assertEqual(transform_position((1.0, 2.0, 3.0), "x_z_neg_y"), (1.0, 3.0, -2.0))
        self.assertEqual(transform_position((1.0, 2.0, 3.0), "x_z_y"), (1.0, 3.0, 2.0))


class SelectionAndExportTests(unittest.TestCase):
    def test_material_grouping_and_accessors(self) -> None:
        model = synthetic_model(two_materials=True)
        selected = select_descriptors(model, material_ids={0, 1})
        document, buffer_data, report = build_gltf(
            model, selected, "synthetic.bin", {"MODELS.BIN": "SYNTHETIC"}, {},
            "source", "source", "source",
        )
        result = validate_gltf(document, buffer_data)
        consistency = validate_consistency(document, buffer_data, model, selected, "source", "source", "source")
        self.assertEqual(report["descriptorCount"], 2)
        self.assertEqual(report["materialCount"], 2)
        self.assertEqual(result["meshCount"], 2)
        self.assertEqual(result["positionCount"], 8)
        self.assertEqual(result["triangleCount"], 4)
        self.assertTrue(consistency["q4_12UvValuesMatchExactly"])
        self.assertEqual([mesh["primitives"][0]["material"] for mesh in document["meshes"]], [0, 1])

    def test_accessor_index_range_rejected(self) -> None:
        model = synthetic_model()
        document, buffer_data, _ = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, {}, "source", "source", "source"
        )
        index_accessor = document["meshes"][0]["primitives"][0]["indices"]
        document["accessors"][index_accessor]["max"] = [999]
        with self.assertRaises(ModelsFormatError):
            validate_gltf(document, buffer_data)

    def test_material_image_repeat_sampler_linkage(self) -> None:
        model = synthetic_model()
        texture_map = {"synthetic_a": [TextureReference("DATA/SYNTHETIC_A.TM2", "ABC")]}
        document, buffer_data, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", {"synthetic_a": "SYNTHETIC_A.png"},
        )
        result = validate_gltf(document, buffer_data)
        self.assertEqual(result["imageCount"], 1)
        self.assertEqual(document["samplers"], [{"wrapS": REPEAT, "wrapT": REPEAT}])
        self.assertEqual(document["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["index"], 0)
        self.assertEqual(report["textureImageCount"], 1)
        self.assertEqual(report["texturedMaterialCount"], 1)
        self.assertEqual(report["unresolvedPlaceholderMaterialCount"], 0)

    def test_unresolved_material_is_explicit_neutral_placeholder(self) -> None:
        model = synthetic_model()
        document, buffer_data, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, {}, "source", "source", "source",
        )
        validate_gltf(document, buffer_data)
        material = document["materials"][0]
        self.assertEqual(material["name"], "UNRESOLVED_SYNTHETIC_A")
        self.assertEqual(material["extras"]["placeholderOnly"], True)
        self.assertEqual(report["materialMappings"][0]["bindingStatus"], "PLACEHOLDER_UNRESOLVED")

    def test_shared_texture_is_reused_and_structure_is_deterministic(self) -> None:
        model = synthetic_model(two_materials=True)
        shared = TextureReference("DATA/SHARED.TM2", "ABC")
        texture_map = {"synthetic_a": [shared], "synthetic_b": [shared]}
        info = TextureImageInfo("textures/SHARED.png", 4, 4, "BINARY_ALPHA", "PNG", "RGBA")
        image_map = {"shared": info}
        # Image lookup is by source stem, irrespective of the MTL alias.
        document_a, buffer_a, report_a = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map,
        )
        document_b, buffer_b, report_b = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map,
        )
        validate_gltf(document_a, buffer_a)
        self.assertEqual(len(document_a["images"]), 1)
        self.assertEqual(len(document_a["textures"]), 1)
        self.assertEqual(report_a["texturedMaterialCount"], 2)
        self.assertEqual(document_a, document_b)
        self.assertEqual(buffer_a, buffer_b)
        self.assertEqual(report_a, report_b)

    def test_external_image_dimensions_and_links(self) -> None:
        document = {"images": [{
            "uri": "textures/SYNTHETIC.png",
            "extras": {"sourceWidth": 4, "sourceHeight": 2},
        }]}
        with tempfile.TemporaryDirectory() as temp_value:
            root = pathlib.Path(temp_value)
            image = root / "textures" / "SYNTHETIC.png"
            image.parent.mkdir()
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + struct.pack(">II", 4, 2))
            result = validate_external_images(document, root / "scene.gltf")
            self.assertEqual(result["missingImageCount"], 0)
            self.assertEqual(result["dimensions"]["textures/SYNTHETIC.png"], [4, 2])

    def test_mirrored_repeat_sampler_is_explicit(self) -> None:
        model = synthetic_model()
        texture_map = {"synthetic_a": [TextureReference("DATA/SYNTHETIC_A.TM2", "ABC")]}
        document, buffer_data, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", {"synthetic_a": "SYNTHETIC_A.png"},
            "mirrored-repeat",
        )
        validate_gltf(document, buffer_data)
        self.assertEqual(document["samplers"], [{"wrapS": MIRRORED_REPEAT, "wrapT": MIRRORED_REPEAT}])
        self.assertEqual(report["samplerMode"], "mirrored-repeat")

    def test_experimental_render_semantics_are_opt_in_and_threshold_free(self) -> None:
        base = synthetic_model()
        model = ModelsData(
            base.descriptors, base.batches,
            (MaterialRecord(0, "SYNTHETIC_A", ("SYNTHETIC_A",), ((2, (3, 0)),)),),
            base.aab, base.header_values,
        )
        texture_map = {"synthetic_a": [TextureReference("DATA/SYNTHETIC_A.TM2", "ABC")]}
        image_map = {"synthetic_a": TextureImageInfo(
            "textures/SYNTHETIC_A.png", 4, 4, "PARTIAL_ALPHA", "PNG", "RGBA"
        )}
        raw, raw_buffer, raw_report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map, "repeat", "raw",
        )
        experimental, experimental_buffer, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map, "repeat", "experimental",
        )
        validate_gltf(raw, raw_buffer)
        validate_gltf(experimental, experimental_buffer)
        self.assertNotIn("doubleSided", raw["materials"][0])
        self.assertNotIn("alphaMode", raw["materials"][0])
        self.assertEqual(raw_report["alphaModeCounts"], {"OPAQUE": 1})
        self.assertTrue(experimental["materials"][0]["doubleSided"])
        self.assertEqual(experimental["materials"][0]["alphaMode"], "BLEND")
        self.assertNotIn("alphaCutoff", experimental["materials"][0])
        self.assertEqual(report["doubleSidedMaterialCount"], 1)
        self.assertEqual(report["alphaModeCounts"], {"BLEND": 1})

    def test_experimental_type2_opaque_texture_remains_opaque(self) -> None:
        base = synthetic_model()
        model = ModelsData(
            base.descriptors, base.batches,
            (MaterialRecord(0, "SYNTHETIC_A", ("SYNTHETIC_A",), ((2, (5, 0)),)),),
            base.aab, base.header_values,
        )
        texture_map = {"synthetic_a": [TextureReference("DATA/SYNTHETIC_A.TM2", "ABC")]}
        image_map = {"synthetic_a": TextureImageInfo(
            "textures/SYNTHETIC_A.png", 4, 4, "FULLY_OPAQUE", "PNG", "RGBA"
        )}
        document, buffer_data, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map, "repeat", "experimental",
        )
        validate_gltf(document, buffer_data)
        self.assertNotIn("alphaMode", document["materials"][0])
        self.assertEqual(report["alphaModeCounts"], {"OPAQUE": 1})

    def test_experimental_nonopaque_without_type2_is_not_guessed(self) -> None:
        model = synthetic_model()
        texture_map = {"synthetic_a": [TextureReference("DATA/SYNTHETIC_A.TM2", "ABC")]}
        image_map = {"synthetic_a": TextureImageInfo(
            "textures/SYNTHETIC_A.png", 4, 4, "PARTIAL_ALPHA", "PNG", "RGBA"
        )}
        document, buffer_data, report = build_gltf(
            model, model.descriptors, "synthetic.bin", {}, texture_map,
            "source", "source", "source", image_map, "repeat", "experimental",
        )
        validate_gltf(document, buffer_data)
        self.assertTrue(document["materials"][0]["doubleSided"])
        self.assertNotIn("alphaMode", document["materials"][0])
        self.assertEqual(report["alphaModeCounts"], {"OPAQUE": 1})

    def test_static_and_special_selection(self) -> None:
        model = synthetic_model(two_materials=True)
        self.assertEqual([item.index for item in select_descriptors(model, "static")], [0])
        self.assertEqual([item.index for item in select_descriptors(model, "special")], [1])


class MalformedInputTests(unittest.TestCase):
    def test_mtl_numeric_property_is_retained_without_semantic_assignment(self) -> None:
        names = b"SYNTHETIC\0"
        record_offset = 8 + len(names)
        record = struct.pack("<4I", 32, 1, 0, 0) + struct.pack("<4I", 16, 2, 5, 0)
        materials = parse_mtl(struct.pack("<2I", record_offset, 1) + names + record)
        self.assertEqual(materials[0].numeric_properties, ((2, (5, 0)),))

    def test_descriptor_extent_out_of_bounds_rejected(self) -> None:
        header = struct.pack("<8I", 48, 15, 1, 48, 30, 0, 0, 0)
        descriptor = struct.pack("<4I", 48, 16, 0, 11)
        with self.assertRaisesRegex(ModelsFormatError, "exceeds"):
            parse_models_bin(header + descriptor, material_count=1)


if __name__ == "__main__":
    unittest.main()
