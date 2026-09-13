"""Build the targeted Roman Grunt Reforged V2 form-correction review scene.

V2 authors new geometry from parametric primitives. It does not import recovered
game geometry, textures, skeletons, or animations. Scene and render outputs are
private review material under ``temp/roman-reforged-v2``.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import build_roman_grunt_reforged_v1 as common


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "temp" / "roman-reforged-v2"
RENDER_ROOT = OUTPUT_ROOT / "renders"
BLEND_PATH = OUTPUT_ROOT / "roman-grunt-reforged-v2.blend"


def varied_material(name, dark, light, metallic, roughness, noise_scale=5.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[1].position = 0.72
    rough_map = nodes.new("ShaderNodeMapRange")
    rough_map.inputs["From Min"].default_value = 0.0
    rough_map.inputs["From Max"].default_value = 1.0
    rough_map.inputs["To Min"].default_value = max(0.0, roughness - 0.08)
    rough_map.inputs["To Max"].default_value = min(1.0, roughness + 0.08)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], rough_map.inputs["Value"])
    links.new(rough_map.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = metallic
    mat.diffuse_color = (*light, 1.0)
    return mat


def mesh_object(name, verts, faces, mat, parent=None, smooth=False, bevel=0.0):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if parent:
        obj.parent = parent
    common.assign(obj, mat)
    if smooth:
        common.smooth(obj)
    if bevel:
        common.bevel(obj, bevel, 2)
    return obj


def tapered_limb(name, start, end, r0, r1, mat, parent, segments=18):
    start_v, end_v = Vector(start), Vector(end)
    length = (end_v - start_v).length
    verts = []
    for z, radius in ((-length / 2, r0), (length / 2, r1)):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    verts.extend(((0, 0, -length / 2), (0, 0, length / 2)))
    faces = []
    for i in range(segments):
        n = (i + 1) % segments
        faces.append((i, n, segments + n, segments + i))
        faces.append((2 * segments, n, i))
        faces.append((2 * segments + 1, segments + i, segments + n))
    obj = mesh_object(name, verts, faces, mat, parent, smooth=True)
    obj.location = (start_v + end_v) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((end_v - start_v).normalized())
    return obj


def ellipsoid(name, loc, scale, mat, parent, segments=28, rings=16):
    return common.sphere(name, loc, scale, mat, segments=segments, rings=rings, parent=parent)


def elliptical_band(name, z, height, rx_bottom, rx_top, ry_bottom, ry_top, thickness, mat, parent, segments=32):
    verts = []
    loops = (
        (z - height / 2, rx_bottom, ry_bottom),
        (z + height / 2, rx_top, ry_top),
        (z - height / 2, rx_bottom - thickness, ry_bottom - thickness),
        (z + height / 2, rx_top - thickness, ry_top - thickness),
    )
    for level_z, rx, ry in loops:
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            verts.append((rx * math.cos(angle), ry * math.sin(angle), level_z))
    faces = []
    for i in range(segments):
        n = (i + 1) % segments
        faces.extend(
            (
                (i, n, segments + n, segments + i),
                (2 * segments + i, 3 * segments + i, 3 * segments + n, 2 * segments + n),
                (segments + i, segments + n, 3 * segments + n, 3 * segments + i),
                (i, 2 * segments + i, 2 * segments + n, n),
            )
        )
    return mesh_object(name, verts, faces, mat, parent, smooth=True, bevel=0.006)


def helmet_dome(name, loc, radii, mat, parent, segments=32, rings=10):
    verts = []
    for ring in range(rings + 1):
        phi = (math.pi / 2) * ring / rings
        ring_radius = math.cos(phi)
        z = radii[2] * math.sin(phi)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            verts.append((loc[0] + radii[0] * ring_radius * math.cos(angle), loc[1] + radii[1] * ring_radius * math.sin(angle), loc[2] + z))
    faces = []
    for ring in range(rings):
        for i in range(segments):
            n = (i + 1) % segments
            a = ring * segments + i
            b = ring * segments + n
            c = (ring + 1) * segments + n
            d = (ring + 1) * segments + i
            faces.append((a, b, c, d))
    obj = mesh_object(name, verts, faces, mat, parent, smooth=True)
    solid = obj.modifiers.new("Helmet_Thickness", "SOLIDIFY")
    solid.thickness = 0.018
    return obj


def tapered_panel(name, loc, top_width, bottom_width, height, depth, mat, parent, rotation=(0, 0, 0)):
    tw, bw, h, d = top_width / 2, bottom_width / 2, height / 2, depth / 2
    verts = [
        (-tw, -d, h), (tw, -d, h), (bw, -d, -h), (-bw, -d, -h),
        (-tw, d, h), (tw, d, h), (bw, d, -h), (-bw, d, -h),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    obj = mesh_object(name, verts, faces, mat, parent, bevel=0.012)
    obj.location = loc
    obj.rotation_euler = rotation
    return obj


def shield_surface(name, width, height, curve, y_offset, mat, parent, segments_x=16, segments_z=18, solidify=0.0):
    verts, faces = [], []
    for j in range(segments_z + 1):
        z_norm = -1 + 2 * j / segments_z
        z = z_norm * height / 2
        corner_scale = 1.0 - 0.11 * abs(z_norm) ** 7
        for i in range(segments_x + 1):
            x_norm = -1 + 2 * i / segments_x
            x = x_norm * width / 2 * corner_scale
            y = y_offset - curve * (1.0 - x_norm * x_norm)
            verts.append((x, y, z))
    for j in range(segments_z):
        for i in range(segments_x):
            a = j * (segments_x + 1) + i
            faces.append((a, a + 1, a + segments_x + 2, a + segments_x + 1))
    obj = mesh_object(name, verts, faces, mat, parent, smooth=True, bevel=0.01)
    if solidify:
        mod = obj.modifiers.new("Shield_Thickness", "SOLIDIFY")
        mod.thickness = solidify
        mod.offset = 0.0
    return obj


def flat_polygon(name, points, y, mat, parent):
    verts = [(x, y, z) for x, z in points]
    return mesh_object(name, verts, [tuple(range(len(verts)))], mat, parent)


def eagle_decal(parent, mat):
    # Painted emblem assembled from overlapping flat wing/feather silhouettes.
    parts = []
    wing = [(0.025, 0.10), (0.13, 0.23), (0.41, 0.30), (0.32, 0.17), (0.43, 0.13), (0.27, 0.07), (0.12, -0.03), (0.04, -0.01)]
    for side in (-1, 1):
        pts = [(side * x, z) for x, z in wing]
        parts.append(flat_polygon(f"Shield_Eagle_Wing_{side:+d}", pts, -0.230, mat, parent))
        for feather in range(4):
            inner_x = 0.08 + feather * 0.045
            inner_z = 0.055 - feather * 0.045
            outer_x = 0.30 + feather * 0.035
            outer_z = 0.01 - feather * 0.075
            feather_points = [
                (side * inner_x, inner_z + 0.035),
                (side * outer_x, outer_z + 0.025),
                (side * (outer_x + 0.035), outer_z - 0.015),
                (side * (inner_x + 0.025), inner_z - 0.035),
            ]
            parts.append(flat_polygon(f"Shield_Eagle_Feather_{side:+d}_{feather+1}", feather_points, -0.231, mat, parent))
    parts.append(flat_polygon("Shield_Eagle_Body", [(-0.06, 0.17), (0.065, 0.17), (0.085, -0.15), (0, -0.23), (-0.085, -0.15)], -0.232, mat, parent))
    parts.append(flat_polygon("Shield_Eagle_Head", [(0.01, 0.14), (0.075, 0.245), (0.16, 0.23), (0.115, 0.185), (0.205, 0.16), (0.085, 0.135)], -0.233, mat, parent))
    parts.append(flat_polygon("Shield_Eagle_Tail", [(-0.09, -0.12), (-0.035, -0.31), (0, -0.24), (0.035, -0.31), (0.09, -0.12)], -0.233, mat, parent))
    return parts


def add_stud(name, loc, mat, parent, scale=0.012):
    return common.sphere(name, loc, (scale, scale * 0.55, scale), mat, segments=12, rings=6, parent=parent)


def build_character(m):
    root = bpy.data.objects.new("Roman_Grunt_V2", None)
    bpy.context.collection.objects.link(root)

    # Human foundation: tapered masses and joint transitions instead of boxes.
    ellipsoid("Roman_Grunt_Chest", (0, 0, 1.42), (0.34, 0.22, 0.41), m["cloth"], root)
    ellipsoid("Roman_Grunt_Waist", (0, 0, 1.15), (0.27, 0.19, 0.22), m["cloth"], root, 24, 14)
    common.cylinder("Roman_Grunt_Neck", (0, 0, 1.79), 0.105, 0.20, m["skin"], vertices=20, parent=root)
    ellipsoid("Roman_Grunt_Head_Cranium", (0, 0, 1.96), (0.135, 0.125, 0.175), m["skin"], root, 28, 18)
    ellipsoid("Roman_Grunt_Head_Jaw", (0, -0.012, 1.90), (0.12, 0.115, 0.12), m["skin"], root, 24, 14)
    ellipsoid("Roman_Grunt_Nose", (0, -0.128, 1.95), (0.027, 0.028, 0.052), m["skin"], root, 18, 10)
    for side in (-1, 1):
        ellipsoid(f"Roman_Grunt_Eye_{side:+d}", (side * 0.047, -0.126, 1.995), (0.016, 0.008, 0.010), m["dark"], root, 14, 8)
        ellipsoid(f"Roman_Grunt_Ear_{side:+d}", (side * 0.132, 0, 1.96), (0.020, 0.014, 0.038), m["skin"], root, 14, 8)
    tapered_panel("Roman_Grunt_Mouth", (0, -0.126, 1.895), 0.075, 0.055, 0.012, 0.006, m["skin_dark"], root)

    # Fitted, squat, uncrested helmet.
    helmet_dome("Roman_Grunt_Helmet_Dome", (0, 0, 2.02), (0.168, 0.153, 0.145), m["iron"], root)
    elliptical_band("Roman_Grunt_Helmet_Rim", 2.018, 0.035, 0.185, 0.185, 0.167, 0.167, 0.022, m["steel"], root, 32)
    tapered_panel("Roman_Grunt_Helmet_RearGuard", (0, 0.135, 1.955), 0.34, 0.29, 0.13, 0.035, m["iron"], root, rotation=(0.16, 0, 0))
    for side in (-1, 1):
        tapered_panel(f"Roman_Grunt_Helmet_Cheek_{side:+d}", (side * 0.135, -0.080, 1.93), 0.075, 0.055, 0.18, 0.025, m["iron"], root, rotation=(0, side * 0.10, side * 0.035))
        add_stud(f"Helmet_Rivet_{side:+d}", (side * 0.135, -0.158, 2.025), m["bronze"], root, 0.012)

    # Curved, overlapping body-following armour bands.
    band_specs = [
        (1.23, 0.145, 0.300, 0.315, 0.205, 0.210),
        (1.35, 0.145, 0.315, 0.330, 0.210, 0.218),
        (1.47, 0.145, 0.330, 0.345, 0.218, 0.225),
        (1.59, 0.145, 0.345, 0.335, 0.225, 0.220),
        (1.70, 0.125, 0.335, 0.300, 0.220, 0.205),
    ]
    for idx, spec in enumerate(band_specs, 1):
        band = elliptical_band(f"Roman_Grunt_TorsoArmour_Band_{idx:02d}", *spec, 0.025, m["iron"], root)
        band.location.y = -0.008 * idx
        for x in (-0.24, 0, 0.24):
            front_y = -spec[5] - 0.018
            add_stud(f"Torso_Fastener_{idx:02d}_{x:+.2f}", (x, front_y, spec[0]), m["bronze"], root, 0.012)
    elliptical_band("Roman_Grunt_Armour_Collar", 1.765, 0.10, 0.29, 0.25, 0.20, 0.18, 0.028, m["iron"], root)
    elliptical_band("Roman_Grunt_Waist_Belt", 1.14, 0.095, 0.31, 0.31, 0.205, 0.205, 0.025, m["leather"], root)

    # Rounded overlapping shoulder shells follow the arm slope.
    for side in (-1, 1):
        for i in range(3):
            x = side * (0.34 + i * 0.075)
            z = 1.67 - i * 0.045
            plate = ellipsoid(f"Roman_Grunt_Shoulder_{'L' if side < 0 else 'R'}_{i+1:02d}", (x, -0.005, z), (0.15, 0.235 - i * 0.025, 0.085), m["iron"], root, 22, 12)
            plate.rotation_euler[1] = side * (0.11 + i * 0.06)
            plate.rotation_euler[2] = side * (-0.03 + i * 0.02)
            add_stud(f"Shoulder_Rivet_{side:+d}_{i:02d}", (x, -0.225 + i * 0.018, z), m["bronze"], root, 0.012)

    # Natural tapered limbs with articulated joint masses.
    arms = {
        "L": ((-0.43, 0, 1.62), (-0.57, -0.015, 1.35), (-0.64, -0.10, 1.10)),
        "R": ((0.43, 0, 1.62), (0.57, -0.010, 1.35), (0.65, -0.10, 1.08)),
    }
    for side_name, (shoulder, elbow, wrist) in arms.items():
        tapered_limb(f"Roman_Grunt_UpperArm_{side_name}", shoulder, elbow, 0.115, 0.095, m["skin"], root)
        ellipsoid(f"Roman_Grunt_Elbow_{side_name}", elbow, (0.095, 0.09, 0.105), m["skin"], root, 20, 12)
        tapered_limb(f"Roman_Grunt_Forearm_{side_name}", elbow, wrist, 0.095, 0.068, m["skin"], root)
        ellipsoid(f"Roman_Grunt_Hand_{side_name}", wrist, (0.075, 0.062, 0.105), m["skin"], root, 22, 12)
        side = -1 if side_name == "L" else 1
        for j in range(3):
            common.cylinder(f"Roman_Grunt_WristWrap_{side_name}_{j+1}", (side * (0.615 + j * 0.006), -0.07, 1.17 - j * 0.03), 0.075, 0.018, m["leather"], vertices=14, rotation=(0.25, 0.03, 0), parent=root)
        # Finger masses are visible at review distance without hero-level topology.
        for finger in range(4):
            x = wrist[0] + (finger - 1.5) * 0.018
            tapered_limb(f"Roman_Grunt_Finger_{side_name}_{finger+1}", (x, wrist[1] - 0.025, wrist[2] + 0.02), (x, wrist[1] - 0.035, wrist[2] - 0.045), 0.012, 0.010, m["skin"], root, 10)

    # Long underlayer plus overlapping, subtly varied front/rear pteruges.
    bpy.ops.mesh.primitive_cone_add(vertices=28, radius1=0.37, radius2=0.30, depth=0.58, location=(0, 0, 0.91))
    under = bpy.context.object
    under.name = "Roman_Grunt_Skirt_Underlayer"
    under.parent = root
    common.assign(under, m["cloth"])
    common.bevel(under, 0.008, 2)
    variations = (-0.018, 0.008, -0.006, 0.014, -0.010, 0.004, 0.017, -0.012, 0.006)
    for side_name, y_sign in (("Front", -1), ("Rear", 1)):
        for i, delta in enumerate(variations):
            x = -0.28 + i * 0.07
            y = y_sign * (0.335 - 0.035 * (abs(x) / 0.28) ** 2)
            height = 0.48 + delta
            panel = tapered_panel(f"Roman_Grunt_SkirtStrip_{side_name}_{i+1:02d}", (x, y, 0.90 + delta / 2), 0.068, 0.052, height, 0.035, m["leather_red"], root, rotation=(0, delta * 1.8, delta * 0.8))
            for stud_z in (1.045, 0.86):
                add_stud(f"Skirt_Stud_{side_name}_{i+1:02d}_{stud_z:.2f}", (x, y - y_sign * 0.025, stud_z + delta / 2), m["bronze"], root, 0.011)
    for side in (-1, 1):
        for i in range(3):
            z = 0.93 - i * 0.035
            tapered_panel(f"Roman_Grunt_SkirtStrip_Side_{side:+d}_{i+1}", (side * (0.32 + i * 0.01), -0.04 + i * 0.04, z), 0.07, 0.05, 0.46, 0.035, m["leather_red"], root, rotation=(0, side * 0.10, side * 0.04))

    # More anatomical legs, knees, calves, feet, and restrained straps.
    for side in (-1, 1):
        x = side * 0.18
        tapered_limb(f"Roman_Grunt_Thigh_{side:+d}", (x, 0, 0.75), (x, -0.005, 0.51), 0.125, 0.105, m["cloth"], root)
        ellipsoid(f"Roman_Grunt_Knee_{side:+d}", (x, -0.012, 0.49), (0.105, 0.10, 0.09), m["skin"], root, 20, 12)
        tapered_limb(f"Roman_Grunt_Calf_{side:+d}", (x, -0.005, 0.47), (x, -0.015, 0.17), 0.105, 0.075, m["skin"], root)
        ellipsoid(f"Roman_Grunt_Foot_{side:+d}", (x, -0.07, 0.075), (0.115, 0.205, 0.065), m["leather"], root, 22, 12)
        common.cube(f"Roman_Grunt_Sandal_Sole_{side:+d}", (x, -0.065, 0.035), (0.12, 0.215, 0.025), m["leather_dark"], 0.018, root)
        for strap_i, strap_z in enumerate((0.10, 0.16, 0.23)):
            tapered_panel(f"Roman_Grunt_Sandal_Strap_{side:+d}_{strap_i+1}", (x, -0.135 + strap_i * 0.035, strap_z), 0.19, 0.17, 0.032, 0.025, m["leather"], root, rotation=(0.08, side * 0.18, 0))

    # Broad/squat two-shell shield with deeper curvature and rounded corners.
    shield_root = bpy.data.objects.new("Roman_Grunt_Shield", None)
    bpy.context.collection.objects.link(shield_root)
    shield_root.parent = root
    shield_root.location = (-0.72, -0.34, 1.14)
    shield_root.rotation_euler = (0.015, -0.10, -0.065)
    shield_surface("Roman_Grunt_Shield_DarkShell", 0.96, 1.17, 0.145, 0.0, m["shield_edge"], shield_root, solidify=0.065)
    shield_surface("Roman_Grunt_Shield_RedFace", 0.87, 1.08, 0.155, -0.050, m["shield_red"], shield_root)
    eagle_decal(shield_root, m["eagle"])
    ellipsoid("Roman_Grunt_Shield_Boss", (0, -0.270, 0), (0.13, 0.075, 0.13), m["steel"], shield_root, 28, 16)
    shield_surface("Roman_Grunt_Shield_RearWood", 0.84, 1.03, -0.11, 0.045, m["wood"], shield_root)
    for x in (-0.28, -0.14, 0, 0.14, 0.28):
        tapered_panel(f"Shield_Rear_WoodSeam_{x:+.2f}", (x, 0.17, 0), 0.012, 0.012, 0.94, 0.012, m["wood_dark"], shield_root)
    for z in (-0.28, 0.28):
        tapered_panel(f"Shield_Rear_Brace_{z:+.2f}", (0, 0.19, z), 0.68, 0.64, 0.065, 0.035, m["leather"], shield_root)
    common.cylinder_between("Shield_Rear_Grip", (-0.20, 0.22, 0), (0.20, 0.22, 0), 0.028, m["leather_dark"], vertices=14, parent=shield_root)

    # Refined but still short gladius.
    sword_root = bpy.data.objects.new("Roman_Grunt_Sword", None)
    bpy.context.collection.objects.link(sword_root)
    sword_root.parent = root
    common.cylinder_between("Roman_Grunt_Sword_Blade", (0.66, -0.12, 1.02), (0.82, -0.16, 0.39), 0.040, m["steel"], vertices=4, parent=sword_root)
    common.cylinder_between("Roman_Grunt_Sword_Grip", (0.64, -0.105, 1.16), (0.665, -0.12, 1.01), 0.032, m["leather_dark"], vertices=14, parent=sword_root)
    tapered_panel("Roman_Grunt_Sword_Guard", (0.66, -0.12, 1.04), 0.22, 0.18, 0.045, 0.045, m["bronze"], sword_root, rotation=(0.02, -0.20, 0))
    ellipsoid("Roman_Grunt_Sword_Pommel", (0.635, -0.10, 1.18), (0.045, 0.045, 0.05), m["bronze"], sword_root, 16, 10)
    return root


def render_views(camera):
    views = [
        ("front", (0, -6.2, 1.15), (0, 0, 1.10), 58),
        ("front-three-quarter", (4.0, -5.0, 1.25), (0, 0, 1.10), 62),
        ("side", (6.2, 0, 1.20), (0, 0, 1.10), 62),
        ("rear-three-quarter", (4.1, 5.0, 1.25), (0, 0, 1.10), 62),
        ("rear", (0, 6.2, 1.15), (0, 0, 1.10), 58),
        ("closeup-head-helmet", (0, -3.35, 2.00), (0, 0, 2.00), 75),
        ("closeup-torso-armour", (0, -3.40, 1.43), (0, 0, 1.43), 75),
        ("closeup-skirt", (0, -3.25, 0.94), (0, 0, 0.94), 78),
        ("closeup-shield-front", (-0.72, -3.15, 1.14), (-0.72, -0.34, 1.14), 76),
        ("closeup-shield-rear", (-0.72, 3.15, 1.14), (-0.72, -0.34, 1.14), 76),
        ("closeup-sword", (1.0, -3.15, 0.80), (0.70, -0.12, 0.78), 82),
    ]
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    outputs = []
    for name, position, target, lens in views:
        camera.location = position
        camera.data.lens = lens
        common.look_at(camera, target)
        path = RENDER_ROOT / f"roman-grunt-reforged-v2-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        outputs.append({"name": name, "path": str(path), "resolution": [900, 1200]})
    return outputs


def triangle_rows():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name.startswith("Studio_"):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        rows.append({"object": obj.name, "triangles": len(mesh.loop_triangles)})
        evaluated.to_mesh_clear()
    rows.sort(key=lambda row: (-row["triangles"], row["object"]))
    total = sum(row["triangles"] for row in rows)
    for row in rows:
        row["percentage"] = round(row["triangles"] * 100.0 / total, 4) if total else 0
    return total, rows


def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)
    common.reset_scene()
    m = {
        "skin": varied_material("M2_Skin", (0.385, 0.165, 0.075), (0.445, 0.205, 0.100), 0.0, 0.50, 8.0),
        "skin_dark": common.material("M2_Skin_Dark", (0.10, 0.025, 0.012, 1), 0.0, 0.62),
        "dark": common.material("M2_Eye_Dark", (0.004, 0.003, 0.002, 1), 0.0, 0.28),
        "iron": varied_material("M2_Dark_Iron", (0.040, 0.034, 0.030), (0.064, 0.054, 0.046), 0.83, 0.36, 14.0),
        "steel": varied_material("M2_Worn_Steel", (0.19, 0.18, 0.17), (0.25, 0.24, 0.22), 0.90, 0.27, 15.0),
        "bronze": varied_material("M2_Aged_Bronze", (0.17, 0.070, 0.020), (0.24, 0.105, 0.030), 0.84, 0.33, 14.0),
        "cloth": varied_material("M2_Red_Brown_Cloth", (0.155, 0.027, 0.013), (0.205, 0.041, 0.020), 0.0, 0.73, 10.0),
        "leather_red": varied_material("M2_Red_Brown_Leather", (0.13, 0.022, 0.010), (0.18, 0.034, 0.016), 0.0, 0.53, 12.0),
        "leather": varied_material("M2_Dark_Leather", (0.020, 0.008, 0.003), (0.052, 0.021, 0.008), 0.0, 0.59, 7.0),
        "leather_dark": common.material("M2_Leather_Deep", (0.012, 0.004, 0.002, 1), 0.0, 0.67),
        "shield_red": common.material("M2_Shield_Red_Paint", (0.50, 0.010, 0.003, 1), 0.12, 0.52),
        "shield_edge": varied_material("M2_Shield_Dark_Edge", (0.012, 0.006, 0.003), (0.044, 0.019, 0.008), 0.62, 0.40, 8.0),
        "eagle": common.material("M2_Shield_Black_Eagle", (0.002, 0.002, 0.001, 1), 0.05, 0.72),
        "wood": varied_material("M2_Shield_Wood", (0.050, 0.017, 0.005), (0.12, 0.043, 0.012), 0.0, 0.68, 4.0),
        "wood_dark": common.material("M2_Shield_Wood_Seam", (0.008, 0.002, 0.001, 1), 0.0, 0.80),
        "platform": common.material("M2_Platform", (0.032, 0.037, 0.043, 1), 0.25, 0.42),
        "floor": common.material("M2_Studio_Floor", (0.010, 0.013, 0.017, 1), 0.0, 0.62),
    }
    build_character(m)
    common.setup_studio(m)
    camera = common.setup_camera()
    scene = bpy.context.scene
    scene["spartan_reforged_status"] = "V2 targeted form pass - awaiting human visual approval"
    scene["source_geometry_reused"] = False
    scene["source_texture_pixels_reused"] = False
    scene["rigging_present"] = False
    scene["runtime_integration"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    renders = render_views(camera)
    total, rows = triangle_rows()
    with (OUTPUT_ROOT / "v2-triangle-report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("object", "triangles", "percentage"))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "status": "IMPLEMENTED - AWAITING HUMAN VISUAL APPROVAL",
        "blend": str(BLEND_PATH),
        "triangle_count_approx": total,
        "materials": sorted(mat.name for mat in m.values()),
        "objects": sorted(obj.name for obj in scene.objects if not obj.name.startswith("Studio_") and obj.name != "Review_Camera"),
        "top_20_triangles": rows[:20],
        "renders": renders,
        "source_geometry_reused": False,
        "source_texture_pixels_reused": False,
        "rigging": False,
        "runtime_integration": False,
    }
    (OUTPUT_ROOT / "scene-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(json.dumps({"blend": str(BLEND_PATH), "triangles": total, "renders": len(renders)}))


if __name__ == "__main__":
    main()
