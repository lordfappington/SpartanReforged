"""Build Roman Grunt — Human Base Build 1 from Blender's CC0 human base.

The source human is Blender Human Base Meshes v1.4.1, downloaded privately to
``temp``.  This script never imports original Spartan game assets and writes all
scene, render, and geometry-report outputs below ``temp/roman-human-base-build1``.

Run the mandatory anatomy gate first::

    blender -b --factory-startup --python tools/blender/build_roman_grunt_human_base_build1.py -- --phase human

Only after visual inspection of that output should the equipment phase run::

    blender -b --factory-startup --python tools/blender/build_roman_grunt_human_base_build1.py -- --phase roman
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "temp" / "roman-human-base-build1"
RENDER_ROOT = OUTPUT_ROOT / "renders"
SOURCE_BLEND = (
    OUTPUT_ROOT
    / "source"
    / "human-base-meshes-v1.4.1"
    / "human-base-meshes-bundle-v1.4.1"
    / "human_base_meshes_bundle.blend"
)
HUMAN_BLEND = OUTPUT_ROOT / "roman-grunt-human-foundation-build1.blend"
ROMAN_BLEND = OUTPUT_ROOT / "roman-grunt-human-base-build1.blend"


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("human", "roman"), required=True)
    parser.add_argument("--source-blend", type=Path, default=SOURCE_BLEND)
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def mat(name, color, metallic=0.0, roughness=0.5):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    material.diffuse_color = (*color, 1.0)
    return material


def textured_mat(name, dark, light, metallic, roughness, scale=6.0):
    material = mat(name, light, metallic, roughness)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 2.0
    tex.inputs["Roughness"].default_value = 0.55
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[1].position = 0.75
    links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
    return material


def assign(obj, material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def smooth(obj) -> None:
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def mesh_object(name, verts, faces, material, collection, bevel=0.0, smooth_faces=False):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    assign(obj, material)
    if smooth_faces:
        smooth(obj)
    if bevel:
        modifier = obj.modifiers.new("Edge_Rounding", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def cube(name, location, scale, material, collection, bevel=0.0, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for target in list(obj.users_collection):
        target.objects.unlink(obj)
    collection.objects.link(obj)
    assign(obj, material)
    if bevel:
        modifier = obj.modifiers.new("Edge_Rounding", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def uv_sphere(name, location, scale, material, collection, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for target in list(obj.users_collection):
        target.objects.unlink(obj)
    collection.objects.link(obj)
    assign(obj, material)
    smooth(obj)
    return obj


def cylinder(name, location, radius, depth, material, collection, vertices=32, rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    for target in list(obj.users_collection):
        target.objects.unlink(obj)
    collection.objects.link(obj)
    assign(obj, material)
    smooth(obj)
    if bevel:
        modifier = obj.modifiers.new("Edge_Rounding", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def curve_tube(name, points, radius, material, collection, cyclic=False, resolution=2):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    assign(obj, material)
    return obj


def look_at(obj, target) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def import_human(source_blend: Path, materials):
    if not source_blend.is_file():
        raise FileNotFoundError(source_blend)
    with bpy.data.libraries.load(str(source_blend), link=False) as (data_from, data_to):
        if "Body Male - Realistic" not in data_from.collections:
            raise RuntimeError("Official realistic male collection missing")
        data_to.collections = ["Body Male - Realistic"]
    imported = data_to.collections[0]
    imported.name = "Human_Foundation_CC0"
    bpy.context.scene.collection.children.link(imported)
    body = bpy.data.objects["GEO-body_male_realistic"]
    eyes = [bpy.data.objects["GEO-body_male_realistic.eye.L"], bpy.data.objects["GEO-body_male_realistic.eye.R"]]

    # Place the official continuous mesh at the origin and tune broad infantry
    # proportions by smooth regional deformation.  Topology and UVs are kept.
    origin_x = body.location.x
    body.location.x = 0.0
    for eye in eyes:
        eye.location.x -= origin_x
    for vertex in body.data.vertices:
        co = vertex.co
        chest = max(0.0, 1.0 - abs(co.z - 1.30) / 0.35)
        shoulder = max(0.0, 1.0 - abs(co.z - 1.43) / 0.18)
        waist = max(0.0, 1.0 - abs(co.z - 1.02) / 0.22)
        co.x *= 1.0 + 0.055 * chest + 0.035 * shoulder - 0.015 * waist
        if co.y < 0:
            co.y *= 1.0 + 0.025 * chest
        co.z *= 1.035
    for obj in [body, *eyes]:
        obj.scale *= 1.035
    body.name = "Human_Body_Continuous_CC0"
    eyes[0].name = "Human_Eye_L_CC0"
    eyes[1].name = "Human_Eye_R_CC0"
    assign(body, materials["skin"])
    # Keep one multires level for smooth review while retaining a tractable
    # working mesh.  The source carries three levels (1.35M evaluated tris).
    for modifier in body.modifiers:
        if modifier.type == "MULTIRES":
            modifier.levels = 1
            modifier.sculpt_levels = 1
            modifier.render_levels = 1
    assign(eyes[0], materials["eye"])
    assign(eyes[1], materials["eye"])
    body["source"] = "Blender Human Base Meshes v1.4.1 / Body Male - Realistic"
    body["license"] = "CC0-1.0"
    body["anatomy_method"] = "continuous base mesh; smooth broad-proportion deformation"
    return body, eyes, imported


def setup_studio(materials):
    stage = bpy.data.collections.new("Studio")
    bpy.context.scene.collection.children.link(stage)
    cube("Studio_Platform", (0, 0, -0.055), (1.25, 0.95, 0.05), materials["platform"], stage, 0.04)
    bpy.ops.mesh.primitive_plane_add(size=25, location=(0, 0, -0.108))
    floor = bpy.context.object
    floor.name = "Studio_Floor"
    for target in list(floor.users_collection):
        target.objects.unlink(floor)
    stage.objects.link(floor)
    assign(floor, materials["floor"])
    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.018, 0.021, 0.026, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30
    specs = [
        ("Key", (-3.2, -4.2, 4.8), 850, (1.0, 0.88, 0.76), 3.0),
        ("Fill", (3.6, -2.8, 3.2), 650, (0.72, 0.82, 1.0), 3.5),
        ("Rear", (2.5, 4.0, 4.1), 900, (0.90, 0.94, 1.0), 2.6),
        ("Top", (-0.5, 0.0, 5.8), 450, (1.0, 0.92, 0.82), 2.4),
    ]
    for name, location, energy, color, size in specs:
        light_data = bpy.data.lights.new("Studio_" + name, "AREA")
        light_data.energy = energy
        light_data.color = color
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new("Studio_" + name, light_data)
        stage.objects.link(light)
        light.location = location
        look_at(light, (0, 0, 1.05))
    camera_data = bpy.data.cameras.new("Review_Camera")
    camera = bpy.data.objects.new("Review_Camera", camera_data)
    stage.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def configure_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1000
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"


def render_view(camera, filename, location, target, lens=62, resolution=(720, 1000)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    output = RENDER_ROOT / filename
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    return output


def render_human_views(camera):
    specs = [
        ("human-front.png", (0, -4.6, 0.95), (0, 0, 0.90), 62),
        ("human-front-three-quarter.png", (3.0, -3.8, 1.0), (0, 0, 0.90), 64),
        ("human-side.png", (4.6, 0, 0.95), (0, 0, 0.90), 64),
        ("human-rear-three-quarter.png", (3.0, 3.8, 1.0), (0, 0, 0.90), 64),
        ("human-rear.png", (0, 4.6, 0.95), (0, 0, 0.90), 62),
        ("human-head-neck.png", (0, -2.45, 1.58), (0, 0, 1.58), 86),
        ("human-torso-shoulder.png", (0.75, -2.75, 1.25), (0, 0, 1.27), 82),
        ("human-arm-elbow-hand.png", (2.55, -2.25, 0.95), (0.34, 0, 0.94), 92),
        ("human-leg-knee-foot.png", (1.55, -2.65, 0.45), (0.14, 0, 0.43), 88),
    ]
    return [str(render_view(camera, *spec)) for spec in specs]


def body_following_band(name, z, height, rx, front_y, back_y, thickness, material, collection, segments=48):
    # A non-elliptical wrapped plate with a flatter sternum, fuller back and
    # small asymmetric overlap at the right-front closure.
    verts = []
    for ring, inset in ((0, 0.0), (1, thickness)):
        for level in (-1, 1):
            zz = z + level * height * 0.5
            taper = 1.0 - (0.018 * level)
            for index in range(segments):
                angle = 2 * math.pi * index / segments
                x = rx * taper * math.sin(angle)
                front_weight = (1.0 - math.cos(angle)) * 0.5
                y_radius = back_y * (1 - front_weight) + front_y * front_weight
                y = y_radius * math.cos(angle)
                # Flatten centre front/back and retain curved flanks.
                y *= 0.82 + 0.18 * abs(math.sin(angle))
                scale = 1.0 - inset / max(rx, front_y)
                verts.append((x * scale, y * scale, zz))
    faces = []
    stride = segments
    outer_bottom, outer_top, inner_bottom, inner_top = 0, stride, 2 * stride, 3 * stride
    for i in range(segments):
        n = (i + 1) % segments
        faces.extend([
            (outer_bottom + i, outer_bottom + n, outer_top + n, outer_top + i),
            (inner_bottom + i, inner_top + i, inner_top + n, inner_bottom + n),
            (outer_top + i, outer_top + n, inner_top + n, inner_top + i),
            (outer_bottom + i, inner_bottom + i, inner_bottom + n, outer_bottom + n),
        ])
    return mesh_object(name, verts, faces, material, collection, bevel=0.0035, smooth_faces=True)


def body_surface_shell(name, body, predicate, material, collection, thickness=0.012):
    """Extract a body-conforming open surface and give it outward thickness."""
    source = body.data
    matrix = body.matrix_world
    chosen = []
    used = set()
    for poly in source.polygons:
        world_points = [matrix @ source.vertices[index].co for index in poly.vertices]
        center = sum(world_points, Vector()) / len(world_points)
        if predicate(center, world_points):
            chosen.append(poly)
            used.update(poly.vertices)
    if not chosen:
        raise RuntimeError(f"No source faces selected for {name}")
    ordered = sorted(used)
    remap = {old: new for new, old in enumerate(ordered)}
    verts = [tuple(matrix @ source.vertices[index].co) for index in ordered]
    faces = [tuple(remap[index] for index in poly.vertices) for poly in chosen]
    obj = mesh_object(name, verts, faces, material, collection, smooth_faces=True)
    solid = obj.modifiers.new("Armour_Thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 1.0
    bevel = obj.modifiers.new("Armour_Edge_Soften", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 2
    return obj


def helmet_dome(name, center, material, collection, segments=56, rings=18):
    verts = []
    for r in range(rings + 1):
        phi = (math.pi * 0.54) * r / rings
        radial = math.sin(phi)
        z = center[2] + 0.185 * math.cos(phi)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            # Slightly squat, longer rear, and subtle crown ridge.
            x = center[0] + 0.145 * radial * math.cos(angle)
            y_scale = 0.140 + 0.018 * max(0.0, math.cos(angle))
            y = center[1] + y_scale * radial * math.sin(angle)
            z_local = z + 0.006 * math.cos(2 * angle) * radial
            verts.append((x, y, z_local))
    faces = []
    for r in range(rings):
        for i in range(segments):
            n = (i + 1) % segments
            angle = 2 * math.pi * (i + 0.5) / segments
            # The lower front is an actual face opening, not a sphere laid over
            # the head.  Retain the brow edge and full rear/side protection.
            front_delta = abs((angle - 1.5 * math.pi + math.pi) % (2 * math.pi) - math.pi)
            if r >= int(rings * 0.62) and front_delta < 0.78:
                continue
            a = r * segments + i
            faces.append((a, r * segments + n, (r + 1) * segments + n, (r + 1) * segments + i))
    obj = mesh_object(name, verts, faces, material, collection, smooth_faces=True)
    solid = obj.modifiers.new("Helmet_Thickness", "SOLIDIFY")
    solid.thickness = 0.008
    return obj


def panel(name, center, top_width, bottom_width, height, depth, material, collection, rotation=(0, 0, 0), curve=0.0):
    tw, bw = top_width * 0.5, bottom_width * 0.5
    h, d = height * 0.5, depth * 0.5
    front = -d - curve
    verts = [(-tw, -d, h), (tw, -d, h), (bw, front, -h), (-bw, front, -h),
             (-tw, d, h), (tw, d, h), (bw, d, -h), (-bw, d, -h)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    obj = mesh_object(name, verts, faces, material, collection, bevel=0.006)
    obj.location = center
    obj.rotation_euler = rotation
    return obj


def shield_surface(name, width, height, depth, y, material, collection, sx=28, sz=32):
    verts, faces = [], []
    for j in range(sz + 1):
        vz = -1 + 2 * j / sz
        z = vz * height * 0.5
        corner = 1.0 - 0.08 * abs(vz) ** 8
        for i in range(sx + 1):
            vx = -1 + 2 * i / sx
            x = vx * width * 0.5 * corner
            yy = y - depth * (1.0 - vx * vx)
            verts.append((x, yy, z))
    for j in range(sz):
        for i in range(sx):
            a = j * (sx + 1) + i
            faces.append((a, a + 1, a + sx + 2, a + sx + 1))
    return mesh_object(name, verts, faces, material, collection, bevel=0.004, smooth_faces=True)


def eagle_mesh(material, collection):
    # Authored heraldic silhouette with a head, body, tail and layered swept
    # feathers.  It is original geometry; no game texture pixels are used.
    shapes = [
        ("Body", [(-0.050,0.235),(0.050,0.235),(0.065,-0.135),(0,-0.225),(-0.065,-0.135)]),
        ("Head", [(0.00,0.205),(0.075,0.305),(0.150,0.285),(0.105,0.245),(0.195,0.220),(0.070,0.190)]),
        ("Tail", [(-0.080,-0.10),(-0.045,-0.275),(0,-0.215),(0.045,-0.275),(0.080,-0.10)]),
    ]
    for side in (-1, 1):
        shapes.append((f"Wing_{side:+d}", [(side*x,z) for x,z in [(0.035,0.185),(0.13,0.285),(0.405,0.285),(0.345,0.215),(0.19,0.165),(0.075,0.035)]]))
        # Four separated, swept primary feathers make the heraldic bird read
        # as wings rather than a radial polygon star.
        for n in range(4):
            z_root = 0.135 - n * 0.052
            z_tip = 0.145 - n * 0.082
            root = 0.075 + n * 0.014
            tip = 0.37 - n * 0.018
            shapes.append((f"Primary_{side:+d}_{n+1}", [(side*root,z_root+0.018),(side*tip,z_tip+0.014),(side*(tip+0.025),z_tip-0.014),(side*(root+0.015),z_root-0.018)]))
    objects = []
    for part_name, points in shapes:
        polygon = [Vector((x, z, 0.0)) for x, z in points]
        triangles = tessellate_polygon([polygon])
        if triangles and isinstance(triangles[0][0], int):
            faces = [tuple(triangle) for triangle in triangles]
        else:
            index = {(round(vertex.x, 8), round(vertex.y, 8)): i for i, vertex in enumerate(polygon)}
            faces = [tuple(index[(round(vertex.x, 8), round(vertex.y, 8))] for vertex in triangle) for triangle in triangles]
        verts = [(x, -0.022, z) for x, z in points]
        objects.append(mesh_object("Shield_Eagle_" + part_name, verts, faces, material, collection))
    return objects


def build_equipment(materials, body):
    gear = bpy.data.collections.new("Roman_Equipment_Build1")
    bpy.context.scene.collection.children.link(gear)

    # Tunic and cuirass surfaces are extracted from the real torso topology.
    body_surface_shell("Tunic_Torso", body, lambda c, p: 0.91 <= c.z <= 1.58 and abs(c.x) < 0.31, materials["cloth"], gear, 0.009)
    band_ranges = ((1.05,1.14),(1.125,1.215),(1.20,1.29),(1.275,1.365),(1.35,1.44),(1.425,1.515))
    for index, (z0, z1) in enumerate(band_ranges):
        body_surface_shell(
            f"Cuirass_Segment_{index+1:02d}", body,
            lambda c, p, lo=z0, hi=z1: lo <= c.z <= hi and abs(c.x) < 0.315,
            materials["iron"], gear, 0.014,
        )
        for side in (-1, 1):
            cylinder(f"Cuirass_Rivet_{index+1:02d}_{side:+d}", (side * 0.205, -0.205, (z0+z1)/2), 0.008, 0.006, materials["bronze"], gear, 14, rotation=(math.pi/2, 0, 0))
    body_surface_shell("Cuirass_Collar", body, lambda c,p: 1.505 <= c.z <= 1.585 and abs(c.x)<0.30, materials["iron"], gear, 0.014)
    body_surface_shell("Cuirass_Waist", body, lambda c,p: 0.96 <= c.z <= 1.055 and abs(c.x)<0.29, materials["iron"], gear, 0.016)

    # Layered shoulder lames follow the deltoid slope rather than horizontal boxes.
    for side in (-1, 1):
        for layer, (inner, outer) in enumerate(((0.17,0.225),(0.215,0.275),(0.265,0.33))):
            body_surface_shell(
                f"Shoulder_Lame_{side:+d}_{layer+1}", body,
                lambda c,p,s=side,lo=inner,hi=outer: 1.34 <= c.z <= 1.57 and lo <= s*c.x <= hi,
                materials["iron"], gear, 0.013,
            )
            x = side * ((inner+outer)/2)
            cylinder(f"Shoulder_Rivet_{side:+d}_{layer+1}", (x, -0.19, 1.50), 0.007, 0.006, materials["bronze"], gear, 14, rotation=(math.pi/2,0,0))

    # Plain, squat, uncrested helmet with brow, cheek and rear protection.
    helmet_dome("Helmet_Dome", (0, -0.005, 1.70), materials["iron"], gear)
    body_following_band("Helmet_Brow_Rim", 1.690, 0.030, 0.154, 0.150, 0.148, 0.010, materials["steel"], gear)
    panel("Helmet_Cheek_L", (-0.126, -0.096, 1.595), 0.055, 0.070, 0.185, 0.015, materials["iron"], gear, rotation=(0.07, -0.11, -0.03))
    panel("Helmet_Cheek_R", (0.126, -0.096, 1.595), 0.055, 0.070, 0.185, 0.015, materials["iron"], gear, rotation=(0.07, 0.11, 0.03))
    panel("Helmet_Rear_Guard", (0, 0.128, 1.615), 0.25, 0.278, 0.145, 0.016, materials["iron"], gear, rotation=(-0.16, 0, 0))
    curve_tube("Helmet_Crown_Ridge", [(0,-0.13,1.70),(0,-0.05,1.875),(0,0.11,1.71)], 0.007, materials["steel"], gear)
    for side in (-1, 1):
        cylinder(f"Helmet_Brow_Rivet_{side:+d}", (side*0.10,-0.151,1.704), 0.007, 0.006, materials["bronze"], gear, 14, rotation=(math.pi/2,0,0))

    # Belt and long pteruges with controlled width/angle variation.
    body_following_band("Belt", 0.965, 0.105, 0.275, 0.165, 0.165, 0.018, materials["leather"], gear)
    front_x = (-0.225, -0.155, -0.078, 0.0, 0.082, 0.16, 0.228)
    for i, x in enumerate(front_x):
        length = (0.49, 0.54, 0.51, 0.57, 0.52, 0.55, 0.48)[i]
        angle = (-0.025, 0.02, -0.015, 0.0, 0.018, -0.02, 0.027)[i]
        strip = panel(f"Pteruge_Front_{i+1}", (x, -0.155, 0.71), 0.075, 0.060, length, 0.022, materials["leather_red"], gear, rotation=(0.02, angle, 0))
        for stud_z in (0.84, 0.68):
            uv_sphere(f"Pteruge_Stud_F_{i+1}_{stud_z:.2f}", (x, -0.177, stud_z), (0.012,0.007,0.012), materials["bronze"], gear, 16, 8)
    for i, x in enumerate((-0.19, -0.095, 0.0, 0.10, 0.195)):
        panel(f"Pteruge_Rear_{i+1}", (x, 0.145, 0.73), 0.09, 0.068, 0.50, 0.022, materials["leather_red"], gear, rotation=(-0.02, 0, 0))

    # Broad, squat, curved shield with painted original heraldic eagle geometry.
    shield = bpy.data.objects.new("Shield_Root", None)
    gear.objects.link(shield)
    shield.location = (-0.64, -0.24, 0.93)
    shield.rotation_euler = (0.015, -0.08, -0.035)
    shield_coll = bpy.data.collections.new("Shield_Assembly")
    gear.children.link(shield_coll)
    front = shield_surface("Shield_Red_Face", 0.82, 1.02, 0.115, 0.0, materials["shield_red"], shield_coll)
    rim = shield_surface("Shield_Dark_Rim", 0.91, 1.11, 0.105, 0.022, materials["shield_edge"], shield_coll)
    rear = shield_surface("Shield_Rear_Wood", 0.80, 0.99, -0.09, 0.065, materials["wood"], shield_coll)
    for obj in (front, rim, rear):
        obj.parent = shield
    # Put rim behind the face spatially but preserve its larger border.
    front.location.y = -0.012
    for obj in eagle_mesh(materials["eagle"], shield_coll):
        obj.parent = shield
        obj.location.y = -0.142
    boss = uv_sphere("Shield_Boss", (0, -0.165, 0), (0.115,0.055,0.115), materials["steel"], shield_coll, 36, 18)
    boss.parent = shield
    for z in (-0.27, 0.27):
        brace = panel(f"Shield_Rear_Brace_{z:+.2f}", (0, 0.10, z), 0.65, 0.62, 0.055, 0.030, materials["leather"], shield_coll)
        brace.parent = shield
    grip = curve_tube("Shield_Rear_Grip", [(-0.17,0.145,0),(0,0.20,0),(0.17,0.145,0)], 0.024, materials["leather"], shield_coll)
    grip.parent = shield

    # Short gladius with a proper tapered, ridged blade profile.
    blade_points = [(-0.034,0.00,0.00),(0.034,0.00,0.00),(0.043,0.00,-0.42),(0.0,0.00,-0.55),(-0.043,0.00,-0.42)]
    blade_verts = [(x,-0.009,z) for x,y,z in blade_points] + [(x,0.009,z) for x,y,z in blade_points]
    blade_faces = [(0,1,2,3,4),(5,9,8,7,6),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    blade = mesh_object("Gladius_Blade", blade_verts, blade_faces, materials["steel"], gear, bevel=0.003)
    blade.location = (0.48, -0.11, 0.86)
    blade.rotation_euler = (0.02, -0.16, -0.08)
    cylinder("Gladius_Grip", (0.48,-0.105,0.98), 0.026, 0.145, materials["leather"], gear, 18)
    cube("Gladius_Guard", (0.48,-0.105,0.91), (0.10,0.025,0.018), materials["bronze"], gear, 0.008)
    uv_sphere("Gladius_Pommel", (0.48,-0.105,1.06), (0.04,0.035,0.04), materials["bronze"], gear, 20, 12)

    # Footwear: fitted soles and crossing leather straps, leaving toes visible.
    for side in (-1, 1):
        x = side * 0.105
        cube(f"Caliga_Sole_{side:+d}", (x,-0.025,0.018), (0.068,0.138,0.011), materials["leather_dark"], gear, 0.010)
        curve_tube(f"Caliga_Ankle_{side:+d}", [(x-0.065,-0.02,0.10),(x,-0.095,0.12),(x+0.065,-0.02,0.10),(x,0.05,0.13)], 0.011, materials["leather"], gear, cyclic=True)
        curve_tube(f"Caliga_Cross_A_{side:+d}", [(x-0.06,-0.12,0.07),(x+0.055,0.00,0.19)], 0.010, materials["leather"], gear)
        curve_tube(f"Caliga_Cross_B_{side:+d}", [(x+0.06,-0.12,0.07),(x-0.055,0.00,0.19)], 0.010, materials["leather"], gear)
        curve_tube(f"Caliga_Calf_{side:+d}", [(x-0.06,0,0.18),(x+0.05,-0.01,0.30),(x-0.05,-0.02,0.39)], 0.009, materials["leather"], gear)
    return gear


def render_roman_views(camera):
    specs = [
        ("roman-build1-front.png", (0, -5.0, 1.0), (0, 0, 0.92), 60),
        ("roman-build1-front-three-quarter.png", (3.3, -4.1, 1.05), (0, 0, 0.92), 62),
        ("roman-build1-side.png", (5.0, 0, 1.0), (0, 0, 0.92), 62),
        ("roman-build1-rear-three-quarter.png", (3.3, 4.1, 1.05), (0, 0, 0.92), 62),
        ("roman-build1-rear.png", (0, 5.0, 1.0), (0, 0, 0.92), 60),
        ("roman-build1-head-helmet.png", (0,-2.6,1.60),(0,0,1.58),88),
        ("roman-build1-torso-armour.png", (0,-2.9,1.28),(0,0,1.28),84),
        ("roman-build1-skirt.png", (0,-2.8,0.73),(0,0,0.73),86),
        ("roman-build1-shield-front.png", (-0.56,-2.8,0.93),(-0.56,-0.24,0.93),84),
        ("roman-build1-shield-rear.png", (-0.56,2.8,0.93),(-0.56,-0.24,0.93),84),
        ("roman-build1-sword.png", (1.8,-2.5,0.72),(0.48,-0.1,0.72),92),
        ("roman-build1-footwear.png", (1.4,-2.4,0.18),(0.1,0,0.18),92),
    ]
    return [str(render_view(camera, *spec)) for spec in specs]


def triangle_report(phase):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name.startswith("Studio_"):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        category = "human_body" if obj.name.startswith("Human_") else "equipment"
        for prefix, value in (("Helmet_", "helmet"), ("Cuirass_", "torso_armour"), ("Shoulder_", "shoulders"), ("Pteruge_", "skirt"), ("Shield_", "shield"), ("Gladius_", "sword"), ("Caliga_", "footwear")):
            if obj.name.startswith(prefix):
                category = value
                break
        rows.append({"object": obj.name, "category": category, "triangles": len(mesh.loop_triangles)})
        evaluated.to_mesh_clear()
    rows.sort(key=lambda row: (-row["triangles"], row["object"]))
    total = sum(row["triangles"] for row in rows)
    path = OUTPUT_ROOT / f"{phase}-triangle-report.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("object", "category", "triangles"))
        writer.writeheader()
        writer.writerows(rows)
    return total, rows, path


def main():
    args = parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)
    clear_scene()
    materials = {
        "skin": mat("HB1_Skin_Form", (0.43, 0.25, 0.17), 0.0, 0.58),
        "eye": mat("HB1_Eye", (0.03, 0.025, 0.02), 0.0, 0.28),
        "iron": textured_mat("HB1_Dark_Iron", (0.018,0.017,0.018),(0.055,0.050,0.046),0.72,0.48,11),
        "steel": textured_mat("HB1_Worn_Steel", (0.20,0.21,0.22),(0.48,0.47,0.44),0.88,0.25,13),
        "bronze": textured_mat("HB1_Bronze", (0.12,0.050,0.014),(0.30,0.14,0.035),0.80,0.34,12),
        "cloth": textured_mat("HB1_Red_Cloth", (0.10,0.015,0.010),(0.25,0.038,0.022),0.0,0.72,8),
        "leather_red": textured_mat("HB1_Red_Leather", (0.045,0.006,0.003),(0.13,0.020,0.009),0.0,0.61,10),
        "leather": textured_mat("HB1_Dark_Leather", (0.012,0.006,0.003),(0.055,0.025,0.010),0.0,0.58,7),
        "leather_dark": mat("HB1_Leather_Sole", (0.008,0.004,0.002),0.0,0.70),
        "shield_red": textured_mat("HB1_Shield_Red", (0.16,0.012,0.006),(0.46,0.045,0.020),0.12,0.54,9),
        "shield_edge": textured_mat("HB1_Shield_Edge", (0.010,0.006,0.003),(0.060,0.025,0.010),0.60,0.42,8),
        "eagle": mat("HB1_Black_Eagle", (0.003,0.003,0.002),0.02,0.69),
        "wood": textured_mat("HB1_Shield_Wood", (0.035,0.012,0.004),(0.12,0.048,0.015),0.0,0.70,5),
        "platform": mat("HB1_Platform", (0.075,0.080,0.085),0.1,0.52),
        "floor": mat("HB1_Floor", (0.018,0.021,0.025),0.0,0.68),
    }
    body, eyes, _ = import_human(args.source_blend.resolve(), materials)
    camera = setup_studio(materials)
    configure_render()
    scene = bpy.context.scene
    scene["human_base_source"] = "Blender Human Base Meshes v1.4.1"
    scene["human_base_license"] = "CC0-1.0"
    scene["original_game_assets_loaded"] = False
    scene["rigging_present"] = False
    scene["runtime_integration"] = False
    if args.phase == "human":
        scene["status"] = "HUMAN ANATOMY GATE - TECHNICAL REVIEW"
        bpy.ops.wm.save_as_mainfile(filepath=str(HUMAN_BLEND))
        renders = render_human_views(camera)
        total, rows, report_path = triangle_report("human")
        output = {"phase":"human","blend":str(HUMAN_BLEND),"renders":renders,"triangles":total,"source_base_triangles":21160,"top_20":rows[:20],"triangle_report":str(report_path)}
    else:
        scene["status"] = "AWAITING HUMAN VISUAL APPROVAL"
        build_equipment(materials, body)
        bpy.ops.wm.save_as_mainfile(filepath=str(ROMAN_BLEND))
        renders = render_roman_views(camera)
        total, rows, report_path = triangle_report("roman")
        output = {"phase":"roman","blend":str(ROMAN_BLEND),"renders":renders,"triangles":total,"source_base_triangles":21160,"top_20":rows[:20],"triangle_report":str(report_path)}
    report = OUTPUT_ROOT / f"{args.phase}-scene-report.json"
    with report.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=str(HUMAN_BLEND if args.phase == "human" else ROMAN_BLEND))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
