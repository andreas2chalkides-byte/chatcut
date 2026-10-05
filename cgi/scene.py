"""Build the BMP gaming PC scene in Blender (procedural, no external assets)."""
import bpy, math
from mathutils import Vector

CYAN = (0.0, 0.55, 1.0, 1)
WHITE = (1, 1, 1, 1)
PINK = (1.0, 0.1, 0.6, 1)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat_emit(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def mat_pbr(name, color, metallic=0.0, rough=0.4, transmission=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    return m


def box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    o.data.materials.append(mat)
    return o


def fan(name, loc, rot, M, r=0.06):
    """Fan: dark frame, glowing cyan ring, white hub glow, dark blades."""
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    fr = bpy.context.object
    fr.scale = (r * 2.2, r * 2.2, 0.025)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 1.02, depth=0.05)
    hole = bpy.context.object
    bo = fr.modifiers.new("hole", "BOOLEAN")
    bo.object = hole
    bpy.context.view_layer.objects.active = fr
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(hole)
    fr.data.materials.append(M["frame"])
    parts.append(fr)
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=r * 0.09, location=(0, 0, 0.004))
    ring = bpy.context.object
    ring.data.materials.append(M["cyan"])
    parts.append(ring)
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.32, depth=0.012, location=(0, 0, 0.006))
    hub = bpy.context.object
    hub.data.materials.append(M["hubglow"])
    parts.append(hub)
    blades = []
    for i in range(11):
        a = i * 2 * math.pi / 11
        bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * r * 0.62, math.sin(a) * r * 0.62, 0))
        bl = bpy.context.object
        bl.scale = (r * 0.6, r * 0.14, 0.002)
        bl.rotation_euler = (0.5, 0, a + 0.3)
        bl.data.materials.append(M["blade"])
        blades.append(bl)
    # join blades into one rotor so it can spin
    bpy.ops.object.select_all(action="DESELECT")
    for bl in blades:
        bl.select_set(True)
    bpy.context.view_layer.objects.active = blades[0]
    bpy.ops.object.join()
    rotor = bpy.context.object
    rotor.name = name + "_rotor"
    bpy.ops.object.empty_add(location=loc, rotation=rot)
    root = bpy.context.object
    root.name = name
    for p in parts + [rotor]:
        p.parent = root
    return root, rotor


def text(body, loc, rot, size, mat, extrude=0.001):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.extrude = extrude
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(mat)
    return t


def build():
    M = {
        "frame": mat_pbr("frame", (0.012, 0.012, 0.014, 1), metallic=0.8, rough=0.35),
        "black": mat_pbr("black", (0.02, 0.02, 0.022, 1), metallic=0.5, rough=0.5),
        "board": mat_pbr("board", (0.03, 0.035, 0.04, 1), metallic=0.3, rough=0.6),
        "glass": mat_pbr("glass", (0.9, 0.95, 1, 1), rough=0.02, transmission=1.0, ior=1.5),
        "cyan": mat_emit("cyan", CYAN, 5),
        "hubglow": mat_emit("hub", (0.75, 0.9, 1, 1), 3),
        "blade": mat_pbr("blade", (0.5, 0.6, 0.7, 1), rough=0.35, transmission=0.6),
        "pink": mat_emit("pink", PINK, 5),
        "white": mat_emit("white", WHITE, 4),
        "ramlight": mat_emit("ramlight", (0.6, 0.85, 1, 1), 3),
        "floor": mat_pbr("floor", (0.01, 0.01, 0.012, 1), metallic=0.6, rough=0.12),
        "tube": mat_pbr("tube", (0.015, 0.015, 0.02, 1), rough=0.55),
    }
    W, H, D = 0.47, 0.46, 0.28  # x width, z height, y depth
    base_z = 0.0
    # floor
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.001))
    bpy.context.object.data.materials.append(M["floor"])
    # case slabs and pillars
    box("top", (W, D, 0.02), (0, 0, H), M["frame"], 0.004)
    box("bottom", (W, D, 0.03), (0, 0, 0.015), M["frame"], 0.004)
    for x in (-W / 2, W / 2):
        for y in (-D / 2, D / 2):
            box("pillar", (0.018, 0.018, H), (x, y, H / 2), M["frame"], 0.003)
    box("tray", (W, 0.01, H), (0, D / 2 - 0.005, H / 2), M["black"])
    box("leftwall", (0.01, D, H), (-W / 2, 0, H / 2), M["black"])
    # glass: side (facing -y) and front (facing +x)
    box("glass_side", (W, 0.004, H - 0.03), (0, -D / 2, H / 2 + 0.005), M["glass"])
    box("glass_front", (0.004, D, H - 0.03), (W / 2, 0, H / 2 + 0.005), M["glass"])
    # motherboard
    box("board", (0.24, 0.006, 0.26), (-0.07, D / 2 - 0.02, 0.29), M["board"], 0.002)
    for i in range(14):  # small board details
        box("chip", (0.012 + (i % 3) * 0.006, 0.006, 0.01), (-0.16 + (i * 0.013), D / 2 - 0.026, 0.4 - (i % 4) * 0.01), M["black"])
    # pump with BMP logo
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.035, location=(-0.09, D / 2 - 0.045, 0.33), rotation=(math.pi / 2, 0, 0))
    pump = bpy.context.object
    pump.data.materials.append(M["black"])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.041, minor_radius=0.0035, location=(-0.09, D / 2 - 0.063, 0.33), rotation=(math.pi / 2, 0, 0))
    bpy.context.object.data.materials.append(M["cyan"])
    # logo: rounded box outline + letters
    box("logo_frame_t", (0.044, 0.001, 0.0022), (-0.09, D / 2 - 0.0635, 0.343), M["white"])
    box("logo_frame_b", (0.044, 0.001, 0.0022), (-0.09, D / 2 - 0.0635, 0.317), M["white"])
    box("logo_frame_l", (0.0022, 0.001, 0.026), (-0.112, D / 2 - 0.0635, 0.33), M["white"])
    box("logo_frame_r", (0.0022, 0.001, 0.026), (-0.068, D / 2 - 0.0635, 0.33), M["white"])
    text("BMP", (-0.09, D / 2 - 0.064, 0.33), (math.pi / 2, 0, 0), 0.018, M["white"])
    # tubes from pump to top radiator
    for dx in (-0.012, 0.012):
        crv = bpy.data.curves.new("tube", "CURVE")
        crv.dimensions = "3D"
        sp = crv.splines.new("BEZIER")
        sp.bezier_points.add(1)
        p0, p1 = sp.bezier_points
        p0.co = (-0.09 + dx, D / 2 - 0.05, 0.36)
        p0.handle_right = (-0.13 + dx, D / 2 - 0.08, 0.40)
        p0.handle_left = p0.co
        p1.co = (-0.05 + dx * 2, D / 2 - 0.09, H - 0.04)
        p1.handle_left = (-0.12 + dx, D / 2 - 0.1, H - 0.03)
        p1.handle_right = p1.co
        crv.bevel_depth = 0.006
        crv.bevel_resolution = 4
        ob = bpy.data.objects.new("tube", crv)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(M["tube"])
    # top radiator block
    box("radiator", (0.36, 0.12, 0.03), (0.0, 0.02, H - 0.03), M["black"], 0.003)
    # RAM sticks
    for i in range(4):
        x = 0.0 + i * 0.012
        box("ram", (0.006, 0.03, 0.12), (x, D / 2 - 0.04, 0.32), M["black"], 0.001)
        box("ramlight", (0.0062, 0.026, 0.006), (x, D / 2 - 0.04, 0.383), M["ramlight"])
    # GPU
    gpu = box("gpu", (0.29, 0.11, 0.045), (-0.04, D / 2 - 0.08, 0.17), M["black"], 0.004)
    box("gpu_strip", (0.2, 0.002, 0.008), (-0.06, D / 2 - 0.136, 0.18), M["pink"])
    box("gpu_strip2", (0.004, 0.08, 0.006), (0.105, D / 2 - 0.08, 0.19), M["pink"])
    # PSU cables (sleeved bundle)
    for i in range(6):
        crv = bpy.data.curves.new("cable", "CURVE")
        crv.dimensions = "3D"
        sp = crv.splines.new("BEZIER")
        sp.bezier_points.add(1)
        a, b = sp.bezier_points
        a.co = (0.02 + i * 0.008, D / 2 - 0.07, 0.15)
        a.handle_right = (0.02 + i * 0.008, D / 2 - 0.1, 0.08)
        a.handle_left = a.co
        b.co = (0.05 + i * 0.008, D / 2 - 0.02, 0.04)
        b.handle_left = (0.05 + i * 0.008, D / 2 - 0.08, 0.04)
        b.handle_right = b.co
        crv.bevel_depth = 0.0035
        ob = bpy.data.objects.new("cable", crv)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(M["tube"])
    rotors = []
    # bottom fans (facing up)
    for i in range(3):
        _, r = fan("fan_b%d" % i, (-0.14 + i * 0.135, -0.01, 0.045), (0, 0, 0), M)
        rotors.append(r)
    # side fans (facing -x, near front glass)
    for i in range(3):
        _, r = fan("fan_s%d" % i, (W / 2 - 0.04, 0.0, 0.11 + i * 0.13), (0, math.pi / 2, 0), M)
        rotors.append(r)
    # pink accent strip on front edge
    box("edge_strip", (0.004, 0.004, H - 0.06), (W / 2 + 0.006, -D / 2 + 0.01, H / 2), M["pink"])
    return M, rotors


def world_and_lights(haze=0.0):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    if haze > 0:
        vol = w.node_tree.nodes.new("ShaderNodeVolumeScatter")
        vol.inputs["Density"].default_value = haze
        w.node_tree.links.new(vol.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])
    # rim lights
    def area(loc, rot, energy, color, size):
        bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
        L = bpy.context.object
        L.data.energy = energy
        L.data.color = color
        L.data.size = size
        return L
    area((-1.2, 0.9, 1.2), (math.radians(55), 0, math.radians(-130)), 25, (0.6, 0.85, 1), 0.6)
    
    area((1.4, 0.8, 0.8), (math.radians(70), 0, math.radians(120)), 15, (1, 0.4, 0.8), 0.5)
    bpy.ops.object.light_add(type="SPOT", location=(0.3, -0.4, 1.6))
    s = bpy.context.object
    s.data.energy = 40
    s.data.spot_size = math.radians(25)
    s.data.color = (0.8, 0.9, 1)
    s.rotation_euler = (math.radians(15), math.radians(10), 0)


def camera(loc, target, lens=50):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    bpy.context.scene.camera = cam
    cam.data.lens = lens
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.8
    bpy.ops.object.empty_add(location=target)
    tgt = bpy.context.object
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    cam.data.dof.focus_object = tgt
    return cam, tgt


def render_settings(res=(1280, 720), samples=48):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.fps = 24
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 4
    sc.cycles.volume_bounces = 0
