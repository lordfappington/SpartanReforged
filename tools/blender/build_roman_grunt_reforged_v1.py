"""Build and render a public-safe Roman Grunt Reforged V1 review scene.

This script authors new geometry from Blender primitives. It intentionally does
not read or embed extracted game meshes, textures, skeletons, or animation data.
The output scene and renders default to ``temp/`` and remain private until human
visual approval.


Run with Blender 5.2 or newer::

    blender --background --python tools/blender/build_roman_grunt_reforged_v1.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "temp" / "roman-reforged-v1"
RENDER_ROOT = OUTPUT_ROOT / "renders"
BLEND_PATH = OUTPUT_ROOT / "roman-grunt-reforged-v1.blend"


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def material(name: str, color: tuple[float, float, float, float], metallic: float, roughness: float) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    if hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    return obj


def bevel(obj: bpy.types.Object, width: float = 0.015, segments: int = 3) -> None:
    mod = obj.modifiers.new("Edge_Soften", "BEVEL")
    mod.width = width
    mod.segments = segments


def smooth(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def cube(name: str, loc, scale, mat, bevel_width=0.012, parent=None, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if parent:
        obj.parent = parent
    assign(obj, mat)
    if bevel_width:
        bevel(obj, bevel_width)
    return obj


def sphere(name: str, loc, scale, mat, segments=32, rings=20, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if parent:
        obj.parent = parent
    assign(obj, mat)
    smooth(obj)
    return obj


def cylinder(name: str, loc, radius, depth, mat, vertices=24, rotation=(0, 0, 0), parent=None, bevel_width=0.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if parent:
        obj.parent = parent
    assign(obj, mat)
    smooth(obj)
    if bevel_width:
        bevel(obj, bevel_width, 2)
    return obj


def cylinder_between(name: str, start, end, radius, mat, vertices=24, parent=None):
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = cylinder(name, (a + b) / 2, radius, delta.length, mat, vertices=vertices, parent=parent)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    return obj


def torus(name: str, loc, major_radius, minor_radius, mat, rotation=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=40,
        minor_segments=10,
        location=loc,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    if parent:
        obj.parent = parent
    assign(obj, mat)
    smooth(obj)
    return obj


def make_shield_mesh(name: str, width: float, height: float, depth: float, mat, parent):
    cols, rows = 12, 14
    verts = []
    faces = []
    for j in range(rows + 1):
        z = -height / 2 + height * j / rows
        shoulder = 1.0 - 0.055 * (abs(z) / (height / 2)) ** 4
        for i in range(cols + 1):
            x = (-width / 2 + width * i / cols) * shoulder
            y = -depth * (1.0 - (x / (width / 2)) ** 2)
            verts.append((x, y, z))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    assign(obj, mat)
    solid = obj.modifiers.new("Shield_Thickness", "SOLIDIFY")
    solid.thickness = 0.045
    solid.offset = 0.0
    bevel(obj, 0.018, 3)
    return obj


def add_stud(name: str, loc, mat, scale=0.022, parent=None):
    return sphere(name, loc, (scale, scale * 0.65, scale), mat, segments=16, rings=8, parent=parent)


def build_character(mats: dict[str, bpy.types.Material]) -> bpy.types.Object:
    root = bpy.data.objects.new("Roman_Grunt_V1", None)
    bpy.context.collection.objects.link(root)

    # Grounded infantry anatomy: deliberately sturdy without hero exaggeration.
    sphere("Roman_Grunt_Torso", (0, 0, 1.36), (0.38, 0.22, 0.46), mats["cloth_red"], parent=root)
    sphere("Roman_Grunt_Head", (0, -0.01, 1.94), (0.145, 0.13, 0.19), mats["skin"], parent=root)
    sphere("Roman_Grunt_Nose", (0, -0.132, 1.94), (0.035, 0.035, 0.055), mats["skin"], segments=20, rings=12, parent=root)
    cube("Roman_Grunt_Brow", (0, -0.125, 2.01), (0.10, 0.014, 0.018), mats["skin_shadow"], 0.008, root)
    for side in (-1, 1):
        sphere(f"Roman_Grunt_Eye_{side:+d}", (side * 0.052, -0.132, 1.992), (0.018, 0.010, 0.011), mats["eye_dark"], segments=16, rings=8, parent=root)
        sphere(f"Roman_Grunt_Ear_{side:+d}", (side * 0.145, -0.005, 1.95), (0.022, 0.017, 0.042), mats["skin"], segments=16, rings=10, parent=root)
    cube("Roman_Grunt_Mouth", (0, -0.135, 1.895), (0.052, 0.007, 0.007), mats["skin_shadow"], 0.005, root)

    # Squat, plain, uncrested helmet with a modest rear skirt and cheek guards.
    sphere("Roman_Grunt_Helmet_Crown", (0, -0.005, 2.075), (0.176, 0.158, 0.145), mats["dark_metal"], parent=root)
    cube("Roman_Grunt_Helmet_Brow", (0, -0.145, 2.035), (0.19, 0.028, 0.022), mats["edge_metal"], 0.012, root)
    cube("Roman_Grunt_Helmet_Rear", (0, 0.13, 1.995), (0.205, 0.055, 0.075), mats["dark_metal"], 0.02, root, rotation=(0.10, 0, 0))
    for side in (-1, 1):
        cube(f"Roman_Grunt_Helmet_Cheek_{side:+d}", (side * 0.145, -0.095, 1.94), (0.038, 0.025, 0.11), mats["dark_metal"], 0.014, root, rotation=(0, side * 0.10, side * 0.06))
        for z in (2.07, 2.12):
            add_stud(f"Helmet_Rivet_{side:+d}_{z:.2f}", (side * 0.12, -0.15, z), mats["bronze"], 0.014, root)

    # Segmented torso armour and fastener rhythm.
    for index, z in enumerate((1.20, 1.31, 1.42, 1.53, 1.64)):
        width = 0.35 - 0.012 * abs(index - 2)
        plate = cube(f"Roman_Grunt_TorsoArmour_Band_{index+1:02d}", (0, -0.175, z), (width, 0.065, 0.072), mats["dark_metal"], 0.018, root)
        plate.scale.x = 1.0
        for x in (-0.25, 0, 0.25):
            add_stud(f"Torso_Fastener_{index+1:02d}_{x:+.2f}", (x, -0.248, z), mats["bronze"], 0.016, root)
    cube("Roman_Grunt_BackArmour", (0, 0.165, 1.43), (0.34, 0.06, 0.34), mats["dark_metal"], 0.025, root)
    cube("Roman_Grunt_Collar", (0, -0.02, 1.74), (0.29, 0.20, 0.07), mats["dark_metal"], 0.025, root)
    cube("Roman_Grunt_Waist_Belt", (0, -0.005, 1.145), (0.36, 0.22, 0.045), mats["leather"], 0.018, root)
    for x in (-0.27, -0.14, 0, 0.14, 0.27):
        add_stud(f"Waist_Belt_Stud_{x:+.2f}", (x, -0.228, 1.145), mats["bronze"], 0.016, root)

    # Layered shoulder lames retain the broad PS2 massing.
    for side in (-1, 1):
        for i in range(4):
            x = side * (0.34 + i * 0.055)
            z = 1.67 - i * 0.025
            cube(f"Roman_Grunt_Shoulder_{'L' if side < 0 else 'R'}_{i+1:02d}", (x, -0.01, z), (0.085, 0.22 - i * 0.02, 0.055), mats["dark_metal"], 0.018, root, rotation=(0, side * (0.08 + i * 0.035), 0))
            add_stud(f"Shoulder_Rivet_{side:+d}_{i:02d}", (x, -0.215 + i * 0.012, z), mats["bronze"], 0.015, root)

    # Arms in a relaxed review pose; shield and sword remain readable together.
    arm_defs = {
        "L": ((-0.43, 0, 1.60), (-0.58, -0.02, 1.30), (-0.64, -0.12, 1.08)),
        "R": ((0.43, 0, 1.60), (0.58, -0.01, 1.30), (0.65, -0.10, 1.07)),
    }
    for side_name, (shoulder, elbow, wrist) in arm_defs.items():
        cylinder_between(f"Roman_Grunt_UpperArm_{side_name}", shoulder, elbow, 0.105, mats["skin"], parent=root)
        cylinder_between(f"Roman_Grunt_Forearm_{side_name}", elbow, wrist, 0.09, mats["skin"], parent=root)
        sphere(f"Roman_Grunt_Hand_{side_name}", wrist, (0.095, 0.075, 0.105), mats["skin"], segments=24, rings=14, parent=root)
        for j in range(3):
            z = 1.20 - j * 0.035
            cylinder(f"Roman_Grunt_WristWrap_{side_name}_{j+1}", ((-1 if side_name == 'L' else 1) * (0.61 + j * 0.008), -0.065, z), 0.096, 0.023, mats["leather"], vertices=20, rotation=(0.25, 0.05, 0), parent=root)

    # Long red-brown skirt underlayer and distinct studded pteruges.
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.38, radius2=0.31, depth=0.56, location=(0, 0, 0.95))
    skirt = bpy.context.object
    skirt.name = "Roman_Grunt_Skirt_Underlayer"
    skirt.parent = root
    assign(skirt, mats["cloth_red"])
    bevel(skirt, 0.012, 2)
    for i in range(11):
        x = -0.30 + i * 0.06
        y = -0.345 + 0.045 * (abs(x) / 0.30) ** 2
        cube(f"Roman_Grunt_SkirtStrip_Front_{i+1:02d}", (x, y, 0.90), (0.026, 0.024, 0.31), mats["leather_red"], 0.010, root)
        for stud_z in (0.74, 0.90, 1.06):
            add_stud(f"Skirt_Stud_Front_{i+1:02d}_{stud_z:.2f}", (x, y - 0.030, stud_z), mats["bronze"], 0.012, root)
    for i in range(9):
        x = -0.28 + i * 0.07
        y = 0.345 - 0.045 * (abs(x) / 0.28) ** 2
        cube(f"Roman_Grunt_SkirtStrip_Rear_{i+1:02d}", (x, y, 0.90), (0.030, 0.024, 0.31), mats["leather_red"], 0.010, root)
        for stud_z in (0.74, 0.90, 1.06):
            add_stud(f"Skirt_Stud_Rear_{i+1:02d}_{stud_z:.2f}", (x, y + 0.030, stud_z), mats["bronze"], 0.012, root)

    # Grounded legs with exposed calves and leather sandals.
    for side in (-1, 1):
        x = side * 0.19
        cylinder_between(f"Roman_Grunt_Thigh_{side:+d}", (x, 0, 0.76), (x, 0, 0.53), 0.125, mats["cloth_red"], parent=root)
        cylinder_between(f"Roman_Grunt_Calf_{side:+d}", (x, 0, 0.54), (x, -0.01, 0.20), 0.105, mats["skin"], parent=root)
        cube(f"Roman_Grunt_Foot_{side:+d}", (x, -0.055, 0.075), (0.14, 0.24, 0.075), mats["leather"], 0.035, root)
        for z in (0.16, 0.23, 0.30):
            torus(f"Roman_Grunt_SandalStrap_{side:+d}_{z:.2f}", (x, -0.005, z), 0.105, 0.017, mats["leather"], rotation=(math.pi / 2, 0, 0), parent=root)

    # Broad curved shield, consciously wider than a conventional tall scutum.
    shield_root = bpy.data.objects.new("Roman_Grunt_Shield", None)
    bpy.context.collection.objects.link(shield_root)
    shield_root.parent = root
    shield_root.location = (-0.73, -0.34, 1.14)
    shield_root.rotation_euler = (0.02, -0.10, -0.08)
    make_shield_mesh("Roman_Grunt_Shield_RedFace", 0.91, 1.12, 0.11, mats["shield_red"], shield_root)
    for x in (-0.43, 0.43):
        cube(f"Shield_Edge_V_{x:+.2f}", (x, -0.07, 0), (0.035, 0.025, 0.55), mats["shield_edge"], 0.014, shield_root)
    for z in (-0.53, 0.53):
        cube(f"Shield_Edge_H_{z:+.2f}", (0, -0.07, z), (0.43, 0.025, 0.035), mats["shield_edge"], 0.014, shield_root)
    sphere("Roman_Grunt_Shield_Boss", (0, -0.17, 0), (0.14, 0.075, 0.14), mats["edge_metal"], segments=32, rings=18, parent=shield_root)
    # Original Reforged eagle interpretation: central body, head, and stepped wings.
    sphere("Shield_Eagle_Body", (0, -0.175, 0.035), (0.07, 0.018, 0.16), mats["eagle_black"], segments=20, rings=12, parent=shield_root)
    sphere("Shield_Eagle_Head", (0.055, -0.178, 0.19), (0.055, 0.018, 0.055), mats["eagle_black"], segments=16, rings=10, parent=shield_root)
    for side in (-1, 1):
        for i in range(5):
            length = 0.26 - i * 0.026
            x = side * (0.12 + i * 0.045)
            z = 0.12 - i * 0.07
            cube(f"Shield_Eagle_Wing_{side:+d}_{i+1:02d}", (x, -0.182, z), (length / 2, 0.012, 0.025), mats["eagle_black"], 0.018, shield_root, rotation=(0, side * 0.05, side * (-0.20 - i * 0.05)))
        cylinder_between(f"Shield_Eagle_Leg_{side:+d}", (side * 0.035, -0.19, -0.11), (side * 0.11, -0.19, -0.24), 0.018, mats["eagle_black"], vertices=12, parent=shield_root)
    cube("Shield_Rear_Wood", (0, 0.055, 0), (0.385, 0.025, 0.48), mats["wood"], 0.028, shield_root)
    for x in (-0.27, -0.135, 0, 0.135, 0.27):
        cube(f"Shield_Rear_Slat_{x:+.3f}", (x, 0.087, 0), (0.009, 0.008, 0.46), mats["wood_dark"], 0.004, shield_root)
    cube("Shield_Rear_CrossBrace_Top", (0, 0.105, 0.27), (0.34, 0.022, 0.038), mats["leather"], 0.014, shield_root)
    cube("Shield_Rear_CrossBrace_Bottom", (0, 0.105, -0.27), (0.34, 0.022, 0.038), mats["leather"], 0.014, shield_root)
    cube("Shield_Rear_Grip", (0, 0.145, 0), (0.24, 0.035, 0.045), mats["leather"], 0.018, shield_root)

    # Short, straight gladius-scale sword in the opposite hand.
    sword_root = bpy.data.objects.new("Roman_Grunt_Sword", None)
    bpy.context.collection.objects.link(sword_root)
    sword_root.parent = root
    cylinder_between("Roman_Grunt_Sword_Blade", (0.67, -0.12, 1.02), (0.83, -0.16, 0.36), 0.045, mats["steel"], vertices=4, parent=sword_root)
    cylinder_between("Roman_Grunt_Sword_Grip", (0.65, -0.11, 1.12), (0.67, -0.12, 1.00), 0.038, mats["leather"], vertices=16, parent=sword_root)
    cylinder_between("Roman_Grunt_Sword_Guard", (0.56, -0.12, 1.02), (0.76, -0.12, 1.07), 0.025, mats["bronze"], vertices=12, parent=sword_root)
    sphere("Roman_Grunt_Sword_Pommel", (0.64, -0.105, 1.16), (0.05, 0.05, 0.05), mats["bronze"], segments=16, rings=10, parent=sword_root)

    return root


def look_at(obj: bpy.types.Object, target) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_studio(mats: dict[str, bpy.types.Material]):
    cube("Studio_Platform", (0, 0, -0.045), (1.4, 1.15, 0.05), mats["platform"], 0.06)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.10))
    floor = bpy.context.object
    floor.name = "Studio_Floor"
    assign(floor, mats["floor"])

    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.011, 0.015, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.20

    lights = [
        ("Studio_Key", (-4.0, -4.5, 5.5), 1050, (1.0, 0.82, 0.65), 4.0),
        ("Studio_Fill", (4.0, -2.5, 3.0), 650, (0.58, 0.70, 1.0), 4.0),
        ("Studio_Rim", (2.0, 4.0, 4.8), 1100, (1.0, 0.48, 0.20), 3.0),
        ("Studio_Top", (-0.5, 0.5, 6.5), 550, (1.0, 0.92, 0.82), 3.0),
    ]
    for name, loc, energy, color, size in lights:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        look_at(obj, (0, 0, 1.1))


def setup_camera():
    data = bpy.data.cameras.new("Review_Camera")
    data.lens = 58
    data.sensor_width = 36
    obj = bpy.data.objects.new("Review_Camera", data)
    bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj
    return obj


def render_views(camera: bpy.types.Object) -> list[dict]:
    views = [
        ("front", (0, -6.2, 1.15), (0, 0, 1.10), 58),
        ("front-three-quarter", (4.0, -5.0, 1.25), (0, 0, 1.10), 62),
        ("side", (6.2, 0, 1.20), (0, 0, 1.10), 62),
        ("rear-three-quarter", (4.1, 5.0, 1.25), (0, 0, 1.10), 62),
        ("rear", (0, 6.2, 1.15), (0, 0, 1.10), 58),
        ("closeup-head-helmet", (0.0, -3.35, 2.00), (0, 0, 2.00), 75),
        ("closeup-torso-armour", (0.0, -3.40, 1.43), (0, 0, 1.43), 75),
        ("closeup-skirt", (0.0, -3.25, 0.94), (0, 0, 0.94), 78),
        ("closeup-shield-front", (-0.73, -3.15, 1.14), (-0.73, -0.34, 1.14), 76),
        ("closeup-shield-rear", (-0.73, 3.15, 1.14), (-0.73, -0.34, 1.14), 76),
        ("closeup-sword", (1.0, -3.15, 0.80), (0.70, -0.12, 0.78), 82),
    ]
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.view_settings.look = "AgX - Medium High Contrast"
    outputs = []
    for name, position, target, lens in views:
        camera.location = position
        camera.data.lens = lens
        look_at(camera, target)
        path = RENDER_ROOT / f"roman-grunt-reforged-v1-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        outputs.append({"name": name, "path": str(path), "resolution": [900, 1200]})
    return outputs


def triangle_count(root: bpy.types.Object) -> int:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name.startswith("Studio_"):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    return total


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    mats = {
        "skin": material("M_Skin", (0.43, 0.20, 0.10, 1), 0.0, 0.48),
        "skin_shadow": material("M_Skin_Shadow", (0.12, 0.045, 0.025, 1), 0.0, 0.62),
        "eye_dark": material("M_Eye_Dark", (0.006, 0.004, 0.003, 1), 0.0, 0.25),
        "dark_metal": material("M_Dark_Iron", (0.055, 0.045, 0.040, 1), 0.82, 0.34),
        "edge_metal": material("M_Worn_Steel", (0.18, 0.14, 0.10, 1), 0.9, 0.25),
        "bronze": material("M_Aged_Bronze", (0.25, 0.11, 0.035, 1), 0.85, 0.30),
        "cloth_red": material("M_Red_Brown_Cloth", (0.25, 0.035, 0.018, 1), 0.0, 0.72),
        "leather_red": material("M_Red_Brown_Leather", (0.20, 0.025, 0.012, 1), 0.0, 0.48),
        "leather": material("M_Dark_Leather", (0.055, 0.022, 0.010, 1), 0.0, 0.58),
        "shield_red": material("M_Shield_Red_Paint", (0.29, 0.018, 0.010, 1), 0.18, 0.49),
        "shield_edge": material("M_Shield_Dark_Edge", (0.035, 0.020, 0.012, 1), 0.65, 0.38),
        "eagle_black": material("M_Shield_Black_Eagle", (0.006, 0.005, 0.004, 1), 0.1, 0.60),
        "wood": material("M_Shield_Wood", (0.095, 0.035, 0.012, 1), 0.0, 0.66),
        "wood_dark": material("M_Shield_Wood_Seam", (0.018, 0.007, 0.003, 1), 0.0, 0.78),
        "steel": material("M_Sword_Steel", (0.30, 0.32, 0.34, 1), 0.93, 0.19),
        "platform": material("M_Platform", (0.032, 0.037, 0.043, 1), 0.25, 0.42),
        "floor": material("M_Studio_Floor", (0.010, 0.013, 0.017, 1), 0.0, 0.62),
    }
    root = build_character(mats)
    setup_studio(mats)
    camera = setup_camera()
    bpy.context.scene["spartan_reforged_status"] = "V1 review build - awaiting human visual approval"
    bpy.context.scene["source_geometry_reused"] = False
    bpy.context.scene["source_texture_pixels_reused"] = False
    bpy.context.scene["rigging_present"] = False
    bpy.context.scene["runtime_integration"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    outputs = render_views(camera)
    report = {
        "status": "IMPLEMENTED - AWAITING HUMAN VISUAL APPROVAL",
        "blend": str(BLEND_PATH),
        "triangle_count_approx": triangle_count(root),
        "materials": sorted(mat.name for mat in mats.values()),
        "objects": sorted(obj.name for obj in bpy.context.scene.objects if not obj.name.startswith("Studio_") and obj.name != "Review_Camera"),
        "renders": outputs,
        "source_geometry_reused": False,
        "source_texture_pixels_reused": False,
        "rigging": False,
        "runtime_integration": False,
    }
    (OUTPUT_ROOT / "scene-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(json.dumps({"blend": str(BLEND_PATH), "triangles": report["triangle_count_approx"], "renders": len(outputs)}))


if __name__ == "__main__":
    main()
