import math

NODE_START = 16
NODE_END = 48

DEFAULT_AZIMUTH = 35
DEFAULT_ELEVATION = 25

FACE_SHADING = {
    "top":    1.0,
    "bottom": 0.45,
    "front":  0.75,
    "back":   0.6,
    "right":  0.7,
    "left":   0.65,
}

FACE_NORMALS = {
    "top":    (0, -1, 0),
    "bottom": (0, 1, 0),
    "front":  (0, 0, 1),
    "back":   (0, 0, -1),
    "right":  (1, 0, 0),
    "left":   (-1, 0, 0),
}

FACE_VERTS = {
    "top":    lambda x, y, z: [(x,y,z), (x+1,y,z), (x+1,y,z+1), (x,y,z+1)],
    "bottom": lambda x, y, z: [(x,y+1,z), (x,y+1,z+1), (x+1,y+1,z+1), (x+1,y+1,z)],
    "front":  lambda x, y, z: [(x,y,z+1), (x+1,y,z+1), (x+1,y+1,z+1), (x,y+1,z+1)],
    "back":   lambda x, y, z: [(x,y,z), (x,y+1,z), (x+1,y+1,z), (x+1,y,z)],
    "right":  lambda x, y, z: [(x+1,y,z), (x+1,y+1,z), (x+1,y+1,z+1), (x+1,y,z+1)],
    "left":   lambda x, y, z: [(x,y,z), (x,y,z+1), (x,y+1,z+1), (x,y+1,z)],
}

BASE_COLOR = (90, 145, 185)
WIREFRAME_COLOR = "#888888"
REF_CUBE_COLOR = "#444444"


def _shade_color(r, g, b, factor):
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


def _project(x, y, z, cx, cy, cz, cos_az, sin_az, cos_el, sin_el, scale, screen_cx, screen_cy):
    dx = x - cx
    dy = y - cy
    dz = z - cz

    rx = cos_az * dx + sin_az * dz
    rz = -sin_az * dx + cos_az * dz

    ry = cos_el * dy - sin_el * rz
    depth = sin_el * dy + cos_el * rz

    persp = 120 / (120 + depth)
    sx = screen_cx + rx * scale * persp
    sy = screen_cy + ry * scale * persp

    return sx, sy, depth


def render_preview(canvas, faces, azimuth=None, elevation=None):
    canvas.delete("all")

    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w <= 1 or h <= 1:
        return

    az = math.radians(azimuth if azimuth is not None else DEFAULT_AZIMUTH)
    el = math.radians(elevation if elevation is not None else DEFAULT_ELEVATION)
    cos_az = math.cos(az)
    sin_az = math.sin(az)
    cos_el = math.cos(el)
    sin_el = math.sin(el)

    grid_mid = (NODE_START + NODE_END) / 2
    cx, cy, cz = grid_mid, grid_mid, grid_mid

    size = min(w, h)
    scale = size / 50
    screen_cx = w / 2
    screen_cy = h / 2

    view_vec = (-sin_az * cos_el, sin_el, cos_az * cos_el)

    def project(x, y, z):
        return _project(x, y, z, cx, cy, cz, cos_az, sin_az, cos_el, sin_el, scale, screen_cx, screen_cy)

    # Reference cube
    ref = NODE_START
    ref2 = NODE_END
    ref_corners = [
        (ref, ref, ref), (ref2, ref, ref), (ref2, ref, ref2), (ref, ref, ref2),
        (ref, ref2, ref), (ref2, ref2, ref), (ref2, ref2, ref2), (ref, ref2, ref2),
    ]
    ref_edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    proj_ref = [project(*c) for c in ref_corners]
    for a, b in ref_edges:
        canvas.create_line(
            proj_ref[a][0], proj_ref[a][1],
            proj_ref[b][0], proj_ref[b][1],
            fill=REF_CUBE_COLOR, dash=(3, 3)
        )

    # Backface cull and project
    visible = []
    dr, dg, db = BASE_COLOR
    vx, vy, vz = view_vec

    for face in faces:
        if len(face) == 5:
            fx, fy, fz, name, color = face
        else:
            fx, fy, fz, name = face
            color = None

        nx, ny, nz = FACE_NORMALS[name]
        dot = nx * vx + ny * vy + nz * vz
        if dot >= 0:
            continue

        verts = FACE_VERTS[name](fx, fy, fz)
        proj_verts = [project(*v) for v in verts]
        center_depth = sum(p[2] for p in proj_verts) / 4

        shade = FACE_SHADING[name]
        if color:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            fill = _shade_color(r, g, b, shade)
        else:
            fill = _shade_color(dr, dg, db, shade)

        visible.append((center_depth, proj_verts, fill))

    visible.sort(key=lambda f: -f[0])

    for depth, proj_verts, fill in visible:
        coords = []
        for sx, sy, _ in proj_verts:
            coords.extend([sx, sy])
        canvas.create_polygon(coords, fill=fill, outline="")
