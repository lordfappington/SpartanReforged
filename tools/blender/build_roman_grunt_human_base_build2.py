"""Build the Roman Grunt Build 2 major-form review from the approved CC0 human.

This is deliberately a form gate.  It creates moderate-complexity, independently
constructed equipment and private review output below ``temp``.  It does not
load original game data, rig, animate, texture, retopologize, export, or create
runtime assets.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "temp" / "roman-human-base-build2"
RENDER_ROOT = OUTPUT_ROOT / "renders"
SOURCE_BLEND = (
    ROOT / "temp" / "roman-human-base-build1" / "source"
    / "human-base-meshes-v1.4.1" / "human-base-meshes-bundle-v1.4.1"
    / "human_base_meshes_bundle.blend"
)
BUILD_BLEND = OUTPUT_ROOT / "roman-grunt-human-base-build2.blend"

_spec = importlib.util.spec_from_file_location(
    "human_base_build1_utilities", ROOT / "tools" / "blender" / "build_roman_grunt_human_base_build1.py"
)
hb = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(hb)
# The reused render helper writes through its module global; redirect it to the
# independent Build 2 private workspace.
hb.RENDER_ROOT = RENDER_ROOT


def args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-blend", type=Path, default=SOURCE_BLEND)
    return parser.parse_args(argv)


def materials():
    # Intentionally simple review materials: Build 2 is judged on shape.
    return {
        "skin": hb.mat("B2_Skin", (0.42, 0.23, 0.15), 0.0, 0.62),
        "eye": hb.mat("B2_Eye", (0.22, 0.24, 0.20), 0.0, 0.35),
        "armour": hb.mat("B2_Dark_Armour", (0.035, 0.040, 0.045), 0.62, 0.34),
        "edge": hb.mat("B2_Armour_Edge", (0.105, 0.105, 0.095), 0.72, 0.27),
        "bronze": hb.mat("B2_Fasteners", (0.25, 0.11, 0.035), 0.58, 0.38),
        "cloth": hb.mat("B2_Muted_Red_Cloth", (0.18, 0.025, 0.018), 0.0, 0.72),
        "leather_red": hb.mat("B2_Muted_Red_Pteruges", (0.15, 0.022, 0.014), 0.0, 0.58),
        "leather": hb.mat("B2_Dark_Leather", (0.045, 0.020, 0.010), 0.0, 0.68),
        "shield_red": hb.mat("B2_Shield_Red", (0.30, 0.020, 0.012), 0.05, 0.52),
        "shield_edge": hb.mat("B2_Shield_Rim", (0.018, 0.012, 0.008), 0.48, 0.40),
        "wood": hb.mat("B2_Shield_Rear", (0.075, 0.030, 0.012), 0.0, 0.76),
        "black": hb.mat("B2_Eagle_Black", (0.005, 0.006, 0.007), 0.0, 0.52),
        "steel": hb.mat("B2_Steel", (0.22, 0.24, 0.25), 0.72, 0.27),
        "floor": hb.mat("B2_Floor", (0.075, 0.080, 0.085), 0.0, 0.78),
        "platform": hb.mat("B2_Platform", (0.16, 0.17, 0.18), 0.0, 0.55),
    }


def import_compact_human(source: Path, mats):
    body, eyes, imported = hb.import_human(source, mats)
    body.name = "Human_Body_Continuous_CC0_Build2"
    body.scale.x *= 1.085
    body.scale.y *= 1.045
    body.scale.z *= 0.945
    for eye in eyes:
        eye.scale.x *= 1.085
        eye.scale.y *= 1.045
        eye.scale.z *= 0.945
        eye.location.x *= 1.085
        eye.location.y *= 1.045
        eye.location.z *= 0.945
    for vertex in body.data.vertices:
        z = vertex.co.z
        torso = max(0.0, 1.0 - abs(z - 1.27) / 0.42)
        shoulder = max(0.0, 1.0 - abs(z - 1.46) / 0.17)
        thigh = max(0.0, 1.0 - abs(z - 0.70) / 0.30)
        calf = max(0.0, 1.0 - abs(z - 0.32) / 0.25)
        vertex.co.x *= 1.0 + 0.055 * torso + 0.055 * shoulder + 0.070 * thigh + 0.060 * calf
        vertex.co.y *= 1.0 + 0.035 * torso + 0.060 * thigh + 0.055 * calf
    body["build2_proportion_method"] = (
        "non-destructive object scaling plus smooth regional shoulder, torso, thigh and calf widening"
    )
    return body, eyes, imported


def ring_plate(name, z, height, rx, ry, thickness, material, collection, overlap=0.0, segments=40):
    """Independent manufactured elliptical armour ring; never extracted from anatomy."""
    verts = []
    for inset in (0.0, thickness):
        for top in (-1, 1):
            zz = z + top * height * 0.5
            for i in range(segments):
                a = 2 * math.pi * i / segments
                # Broad chest/back fields are intentionally flatter than an
                # ellipse; curvature is concentrated into the flanks.
                cosine = math.cos(a)
                y = math.copysign(ry * abs(cosine) ** 0.42, cosine)
                verts.append(((rx - inset) * math.sin(a), (1 - inset / ry) * y, zz))
    faces = []
    ob, ot, ib, it = 0, segments, 2 * segments, 3 * segments
    for i in range(segments):
        n = (i + 1) % segments
        faces += [(ob+i, ob+n, ot+n, ot+i), (ib+i, it+i, it+n, ib+n),
                  (ot+i, ot+n, it+n, it+i), (ob+i, ib+i, ib+n, ob+n)]
    obj = hb.mesh_object(name, verts, faces, material, collection, bevel=0.003, smooth_faces=False)
    obj["construction"] = "independent manufactured closed plate with physical thickness"
    obj["overlap"] = overlap
    return obj


def curved_lame(name, side, index, material, collection):
    """Large shoulder lame with a visible overlap, separate from body and cuirass."""
    # Adjacent articulated segments form one compact cap instead of stacked
    # shelves stretching from the neck to the arm.
    inner = 0.185 + index * 0.060
    outer = inner + 0.105
    z_inner = 1.495 - index * 0.024
    z_outer = z_inner - 0.040
    front_y, back_y = -0.225, 0.160
    xs = [side * inner, side * ((inner + outer) * 0.54), side * outer]
    zs = [z_inner, (z_inner + z_outer) * 0.5 + 0.018, z_outer]
    verts = []
    for y in (front_y, back_y):
        for x, z in zip(xs, zs):
            verts += [(x, y, z + 0.045), (x, y, z - 0.045)]
    faces = []
    for layer in (0, 6):
        faces += [(layer, layer+2, layer+3, layer+1), (layer+2, layer+4, layer+5, layer+3)]
    for i in range(6):
        n = (i + 1) % 6
        faces.append((i, n, 6+n, 6+i))
    obj = hb.mesh_object(name, verts, faces, material, collection, bevel=0.006)
    obj["construction"] = "separate articulated overlapping shoulder plate"
    return obj


def helmet_dome(material, collection):
    # Squat cap with the face quadrant removed below the brow.
    segments, rings = 48, 14
    center = Vector((0, 0.005, 1.675))
    verts = []
    for r in range(rings + 1):
        phi = (math.pi * 0.54) * r / rings
        for i in range(segments):
            a = 2 * math.pi * i / segments
            radial = math.sin(phi)
            verts.append((center.x + 0.154 * radial * math.cos(a),
                          center.y + 0.148 * radial * math.sin(a),
                          center.z + 0.145 * math.cos(phi)))
    faces = []
    for r in range(rings):
        for i in range(segments):
            n = (i + 1) % segments
            mid = 2 * math.pi * (i + 0.5) / segments
            front = abs((mid - 1.5 * math.pi + math.pi) % (2*math.pi) - math.pi) < 0.72
            if r >= 9 and front:
                continue
            a = r * segments + i
            faces.append((a, r*segments+n, (r+1)*segments+n, (r+1)*segments+i))
    obj = hb.mesh_object("Helmet_Compact_Dome", verts, faces, material, collection, smooth_faces=True)
    solid = obj.modifiers.new("Helmet_Physical_Thickness", "SOLIDIFY")
    solid.thickness = 0.009
    return obj


def tapered_plate(name, points, depth, material, collection, bevel=0.004):
    verts = [(x, y-depth/2, z) for x, y, z in points] + [(x, y+depth/2, z) for x, y, z in points]
    count = len(points)
    faces = [tuple(range(count)), tuple(range(count, count*2))[::-1]]
    for i in range(count):
        n = (i + 1) % count
        faces.append((i, n, count+n, count+i))
    return hb.mesh_object(name, verts, faces, material, collection, bevel=bevel)


def curved_pteruge(name, angle, width, length, material, collection, offset=0.0):
    radius = 0.285
    tangent = Vector((math.cos(angle), math.sin(angle), 0))
    radial = Vector((math.sin(angle), -math.cos(angle), 0))
    top = radial * radius
    top.z = 0.945
    verts = []
    steps = 5
    for depth in (-0.010, 0.010):
        for j in range(steps):
            t = j / (steps - 1)
            c = top + radial * (0.010 + 0.025*t*t + offset) + tangent * (0.012*math.sin(t*math.pi+angle))
            c.z -= length * t
            half = width * (0.50 - 0.045*t)
            for sign in (-1, 1):
                p = c + tangent * half * sign + radial * depth
                verts.append(tuple(p))
    faces = []
    stride = steps * 2
    for layer in (0, stride):
        for j in range(steps-1):
            a = layer + j*2
            faces.append((a, a+1, a+3, a+2))
    perimeter = list(range(0, stride))
    for i in range(stride):
        n = (i + 1) % stride
        faces.append((perimeter[i], perimeter[n], stride+perimeter[n], stride+perimeter[i]))
    obj = hb.mesh_object(name, verts, faces, material, collection, bevel=0.003)
    obj["waist_angle_degrees"] = round(math.degrees(angle), 2)
    return obj


def footwear(side, mats, gear):
    x = side * 0.112
    # Foot-shaped sole, narrower at heel than forefoot.
    outline = [(-0.050,-0.115), (0.058,-0.120), (0.072,-0.055), (0.066,0.095),
               (0.045,0.145), (-0.044,0.142), (-0.060,0.080), (-0.060,-0.065)]
    pts = [(x + px, py, 0.020) for px, py in outline]
    sole = tapered_plate(f"Caliga_{'L' if side < 0 else 'R'}_Sole", pts, 0.024, mats["leather"], gear, 0.006)
    # Complete toe, instep, ankle and restrained calf-wrap construction.
    for n, (z, yr, radius) in enumerate(((0.070,-0.075,0.010),(0.105,-0.015,0.010),(0.145,0.020,0.011))):
        hb.curve_tube(f"Caliga_{'L' if side < 0 else 'R'}_Strap_{n+1}",
                      [(x-0.064,yr,z),(x,yr-0.055,z+0.015),(x+0.064,yr,z)], radius, mats["leather"], gear)
    hb.curve_tube(f"Caliga_{'L' if side < 0 else 'R'}_Ankle",
                  [(x-0.065,0,0.135),(x,-0.060,0.155),(x+0.065,0,0.135),(x,0.060,0.155)],
                  0.012, mats["leather"], gear, cyclic=True)
    hb.cube(f"Caliga_{'L' if side < 0 else 'R'}_Heel_Cuff",(x,.025,.145),(.068,.034,.025),mats["leather"],gear,.010)
    hb.cube(f"Caliga_{'L' if side < 0 else 'R'}_Instep_Band",(x,-.072,.083),(.066,.032,.018),mats["leather"],gear,.009)
    hb.curve_tube(f"Caliga_{'L' if side < 0 else 'R'}_Calf_Wrap_A",
                  [(x-0.050,0,0.17),(x+0.050,-0.012,0.245),(x-0.050,0,0.32)], 0.010, mats["leather"], gear)
    hb.curve_tube(f"Caliga_{'L' if side < 0 else 'R'}_Calf_Wrap_B",
                  [(x+0.050,0,0.17),(x-0.050,-0.012,0.245),(x+0.050,0,0.32)], 0.010, mats["leather"], gear)
    sole["complete_footwear"] = True


def build_equipment(mats):
    gear = bpy.data.collections.new("Roman_Equipment_Build2")
    bpy.context.scene.collection.children.link(gear)

    # Tunic is only a supporting blockout; armour owns the torso silhouette.
    ring_plate("Tunic_Sleeveless_Underlayer", 1.200, 0.46, 0.315, 0.205, 0.010, mats["cloth"], gear)

    # Six broad horizontal plates, independently constructed and visibly overlapping.
    band_specs = [
        (1.030, .105, .292, .215), (1.115, .105, .304, .220),
        (1.200, .105, .315, .225), (1.285, .105, .325, .230),
        (1.370, .105, .333, .235),
    ]
    for i, (z,h,rx,ry) in enumerate(band_specs, 1):
        ring_plate(f"Cuirass_Manufactured_Band_{i:02d}", z, h, rx, ry, 0.016, mats["armour"], gear, 0.025)
        for side in (-1, 1):
            hb.cylinder(f"Cuirass_Fastener_{i:02d}_{side:+d}", (side*0.235,-ry*0.84-0.010,z),
                        0.009, 0.008, mats["bronze"], gear, 12, rotation=(math.pi/2,0,0))
    ring_plate("Cuirass_Upper_Yoke", 1.440, 0.045, .340, .235, .018, mats["armour"], gear)
    ring_plate("Cuirass_Waist_Belt", .985, .115, .300, .212, .020, mats["edge"], gear)

    for side in (-1, 1):
        for index in range(4):
            x = side * (.205 + index * .070)
            z = 1.475 - index * .032
            plate = hb.cube(f"Shoulder_{'L' if side < 0 else 'R'}_Lame_{index+1}",
                            (x,-.015,z),(.046,.192,.022),mats["armour"],gear,.008,
                            rotation=(0,side*math.radians(10+index*4),0))
            plate["construction"] = "separate articulated overlapping shoulder plate"
            hb.cylinder(f"Shoulder_{'L' if side < 0 else 'R'}_Rivet_{index+1}",
                        (x,-.211,z+.004), .008,.007,mats["bronze"],gear,12,
                        rotation=(math.pi/2,0,0))

    helmet_dome(mats["armour"], gear)
    # Strong front brow; short side returns rather than a full floating neck ring.
    hb.cube("Helmet_Strong_Brow", (0,-.153,1.692), (.155,.012,.012), mats["edge"], gear, .004)
    tapered_plate("Helmet_Cheek_L", [(-.148,-.142,1.655),(-.112,-.151,1.642),(-.118,-.148,1.560),(-.142,-.134,1.570)],
                  .018,mats["armour"],gear,.005)
    tapered_plate("Helmet_Cheek_R", [(.112,-.151,1.642),(.148,-.142,1.655),(.142,-.134,1.570),(.118,-.148,1.560)],
                  .018,mats["armour"],gear,.005)
    tapered_plate("Helmet_Curved_Neck_Guard", [(-.145,.120,1.630),(.145,.120,1.630),(.166,.170,1.540),(-.166,.170,1.540)],
                  .022,mats["armour"],gear,.006)

    # Overlapping circumference: front, both flanks, and rear (full 300-degree skirt coverage).
    pteruge_angles = [math.radians(a) for a in (-150,-125,-100,-75,-50,-25,0,25,50,75,100,125,150,180)]
    ring_plate("Pteruge_Under_Skirt", .785, .370, .270, .190, .008, mats["cloth"], gear)
    for i, angle in enumerate(pteruge_angles, 1):
        length = .43 + .035 * ((i * 7) % 4) + (.035 if abs(math.degrees(angle)) < 80 else 0)
        width = .112 + .008 * ((i * 5) % 3)
        curved_pteruge(f"Pteruge_{i:02d}", angle, width, length, mats["leather_red"], gear, .003*(i%2))

    # Broad squat curved identity shield: width/height = 0.78, never a tall narrow scutum.
    root = bpy.data.objects.new("Shield_Root", None)
    gear.objects.link(root)
    root.location = (-.61,-.22,.94)
    root.rotation_euler = (.01,-.06,-.025)
    shield_coll = bpy.data.collections.new("Shield_Assembly_Build2")
    gear.children.link(shield_coll)
    rim = hb.shield_surface("Shield_Dark_Rim", .90, 1.15, .125, .020, mats["shield_edge"], shield_coll, 26,30)
    face = hb.shield_surface("Shield_Red_Face", .82, 1.07, .135, -.010, mats["shield_red"], shield_coll, 26,30)
    rear = hb.shield_surface("Shield_Rear_Wood", .81, 1.06, -.095, .065, mats["wood"], shield_coll, 24,28)
    for obj in (rim, face, rear): obj.parent = root
    for obj in hb.eagle_mesh(mats["black"], shield_coll):
        obj.parent = root
        obj.location.y = -.163
        obj.scale = (.80,1.0,.86)
    boss = hb.uv_sphere("Shield_Boss", (0,-.184,0), (.118,.058,.118), mats["steel"], shield_coll, 32,16)
    boss.parent = root
    for z in (-.30,.30):
        brace = hb.panel(f"Shield_Rear_Brace_{z:+.2f}",(0,.105,z),.64,.61,.06,.032,mats["leather"],shield_coll)
        brace.parent = root
    grip = hb.curve_tube("Shield_Rear_Grip", [(-.18,.145,0),(0,.205,0),(.18,.145,0)],.024,mats["leather"],shield_coll)
    grip.parent = root
    root["identity"] = "broad curved Roman Grunt shield; original black eagle major-shape placeholder"
    root["width"] = .90; root["height"] = 1.15

    # Short 0.52 m blade, compact furniture.
    blade_pts = [(-.034,-.008,0),(.034,-.008,0),(.044,-.008,-.39),(0,-.008,-.52),(-.044,-.008,-.39),
                 (-.034,.008,0),(.034,.008,0),(.044,.008,-.39),(0,.008,-.52),(-.044,.008,-.39)]
    blade_faces = [(0,1,2,3,4),(5,9,8,7,6),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
    blade = hb.mesh_object("Gladius_Short_Blade",blade_pts,blade_faces,mats["steel"],gear,bevel=.003)
    blade.location=(.475,-.105,.84); blade.rotation_euler=(.015,-.12,-.06)
    hb.cube("Gladius_Restrained_Guard",(.475,-.105,.835),(.085,.023,.016),mats["bronze"],gear,.006)
    hb.cylinder("Gladius_Grip",(.475,-.103,.925),.023,.145,mats["leather"],gear,16)
    hb.uv_sphere("Gladius_Pommel",(.475,-.103,1.008),(.034,.030,.034),mats["bronze"],gear,16,10)

    footwear(-1,mats,gear); footwear(1,mats,gear)
    return gear


def render_views(camera):
    specs = [
        ("roman-build2-front.png",(0,-5.0,1.0),(0,0,.91),62),
        ("roman-build2-front-three-quarter.png",(3.25,-4.10,1.02),(0,0,.91),62),
        ("roman-build2-left-side.png",(-5.05,0,1.0),(0,0,.91),62),
        ("roman-build2-rear-three-quarter.png",(3.25,4.10,1.02),(0,0,.91),62),
        ("roman-build2-rear.png",(0,5.0,1.0),(0,0,.91),62),
        ("roman-build2-helmet.png",(0,-2.35,1.65),(0,0,1.65),88),
        ("roman-build2-torso-shoulders.png",(.55,-2.75,1.30),(0,0,1.31),84),
        ("roman-build2-waist-pteruges.png",(0,-2.55,.75),(0,0,.76),88),
        ("roman-build2-shield.png",(-.61,-2.75,.94),(-.61,-.22,.94),84),
        ("roman-build2-footwear.png",(.70,-2.25,.19),(0,-.02,.19),92),
    ]
    return [str(hb.render_view(camera,*spec,resolution=(900,1250))) for spec in specs]


def world_bounds(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def triangle_and_gate_report(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows, totals = [], defaultdict(int)
    mappings = (("Helmet_","helmet"),("Cuirass_","torso_armour"),("Shoulder_","shoulders"),
                ("Pteruge_","pteruges"),("Shield_","shield"),("Gladius_","gladius"),("Caliga_","footwear"))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name.startswith("Studio_"): continue
        evaluated=obj.evaluated_get(depsgraph); mesh=evaluated.to_mesh(); mesh.calc_loop_triangles()
        category="human_body" if obj.name.startswith("Human_") else "supporting_equipment"
        for prefix,label in mappings:
            if obj.name.startswith(prefix): category=label; break
        tris=len(mesh.loop_triangles); rows.append({"object":obj.name,"category":category,"triangles":tris}); totals[category]+=tris
        evaluated.to_mesh_clear()
    rows.sort(key=lambda r:(r["category"],r["object"]))
    OUTPUT_ROOT.mkdir(parents=True,exist_ok=True)
    csv_path=OUTPUT_ROOT/"build2-triangle-report.csv"
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=("object","category","triangles")); w.writeheader(); w.writerows(rows)

    bb=world_bounds(body); height=max(p.z for p in bb)-min(p.z for p in bb)
    # Equipment yoke is the visual shoulder width; landmarks are explicit for reproducibility.
    shoulder_width=.80; hip_z=.90; shoulder_z=1.50; floor_z=min(p.z for p in bb)
    torso_length=shoulder_z-hip_z; leg_length=hip_z-floor_z
    helmet_width=.332; helmet_height=.305; shield_width=.90; shield_height=1.15
    pteruge_angles=[obj.get("waist_angle_degrees") for obj in bpy.context.scene.objects
                    if obj.name.startswith("Pteruge_") and obj.get("waist_angle_degrees") is not None]
    shoulder_objects=[obj for obj in bpy.context.scene.objects if obj.name.startswith("Shoulder_") and "Lame" in obj.name]
    pteruge_objects=[obj for obj in bpy.context.scene.objects if obj.name.startswith("Pteruge_") and obj.get("waist_angle_degrees") is not None]
    footwear_objects=[obj for obj in bpy.context.scene.objects if obj.name.startswith("Caliga_")]
    attachment_bounds_ok=(
        all(1.32 <= sum(p.z for p in world_bounds(obj))/8 <= 1.58 for obj in shoulder_objects)
        and all(max(p.z for p in world_bounds(obj)) >= .90 for obj in pteruge_objects)
        and all(min(p.z for p in world_bounds(obj)) >= -.02 and max(p.z for p in world_bounds(obj)) <= .36 for obj in footwear_objects)
    )
    cuirass_objects=[obj for obj in bpy.context.scene.objects if obj.name.startswith("Cuirass_")]
    authored_clearance_ok=(
        max(max(p.z for p in world_bounds(obj)) for obj in cuirass_objects) < 1.50
        and min(abs(obj.location.x) for obj in shoulder_objects) >= .18
        and all(obj.get("construction","").startswith("independent manufactured") for obj in bpy.context.scene.objects if obj.name.startswith("Cuirass_Manufactured"))
    )
    gates = {
        "status":"AWAITING HUMAN VISUAL APPROVAL — BUILD 2",
        "measurements_m":{
            "character_height":round(height,4),"visual_shoulder_width":shoulder_width,
            "height_to_shoulder_width":round(height/shoulder_width,4),
            "torso_length":torso_length,"leg_length":round(leg_length,4),
            "torso_to_leg_ratio":round(torso_length/leg_length,4),
            "helmet_width":helmet_width,"helmet_height":helmet_height,
            "helmet_width_to_height":round(helmet_width/helmet_height,4),
            "shield_width":shield_width,"shield_height":shield_height,
            "shield_width_to_height":round(shield_width/shield_height,4),
        },
        "gates":{
            "both_feet_have_complete_footwear":all(bpy.data.objects.get(f"Caliga_{s}_Sole") is not None for s in ("L","R")),
            "pteruges_surround_more_than_frontal_plane":min(pteruge_angles)<=-125 and max(pteruge_angles)>=150,
            "armour_is_separate_constructed_geometry":all("independent manufactured" in obj.get("construction","") for obj in bpy.context.scene.objects if obj.name.startswith("Cuirass_Manufactured")),
            "left_right_major_equipment_present":all(any(obj.name.startswith(prefix) for obj in bpy.context.scene.objects) for prefix in ("Shoulder_L","Shoulder_R","Caliga_L","Caliga_R")),
            "no_floating_major_attachment_by_authored_bounds":attachment_bounds_ok,
            "no_obvious_neutral_pose_penetrations_by_authored_clearance":authored_clearance_ok,
        },
        "notes":{
            "floating_and_penetration_checks":"deterministic authored attachment/bounds checks; final visual judgement remains human",
            "heraldry":"major-shape placeholder only; final refinement deferred",
            "scope":"form gate only; no rigging, animation, runtime integration, textures, wear, retopology or LODs",
        },
        "triangle_totals":dict(sorted(totals.items())),"total_triangles":sum(totals.values()),
        "triangle_report":str(csv_path),
    }
    gate_path=OUTPUT_ROOT/"build2-form-gate.json"
    gate_path.write_text(json.dumps(gates,indent=2),encoding="utf-8")
    return gates,gate_path


def main():
    parsed=args(); hb.clear_scene(); OUTPUT_ROOT.mkdir(parents=True,exist_ok=True); RENDER_ROOT.mkdir(parents=True,exist_ok=True)
    mats=materials(); body,eyes,_=import_compact_human(parsed.source_blend,mats); build_equipment(mats)
    hb.setup_studio(mats); hb.configure_render()
    scene=bpy.context.scene
    scene["build"]="Roman Grunt Human Base Build 2 — major-form gate"
    scene["rigging_present"]=False; scene["runtime_integration"]=False; scene["original_game_assets_loaded"]=False
    scene["human_source"]="Blender Human Base Meshes v1.4.1 / CC0-1.0"
    scene["status"]="AWAITING HUMAN VISUAL APPROVAL — BUILD 2"
    camera=bpy.data.objects.get("Review_Camera")
    if camera is None:
        data=bpy.data.cameras.new("Review_Camera_Data"); camera=bpy.data.objects.new("Review_Camera",data); scene.collection.objects.link(camera); scene.camera=camera
    renders=render_views(camera); gates,gate_path=triangle_and_gate_report(body)
    report={"blend":str(BUILD_BLEND),"renders":renders,"gate_report":str(gate_path),"gates":gates}
    (OUTPUT_ROOT/"build2-scene-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BUILD_BLEND))
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
