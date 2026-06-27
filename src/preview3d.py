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

_sort_cache_voxel_faces_id = None
_sort_cache_zone = None
_sort_cache_sorted_voxels = None


def _view_zone(vx, vy, vz):
    ax, ay, az = abs(vx), abs(vy), abs(vz)
    sx = 1 if vx >= 0 else -1
    sy = 1 if vy >= 0 else -1
    sz = 1 if vz >= 0 else -1
    if ax >= ay and ax >= az:
        order = 0 if ay >= az else 1
    elif ay >= ax and ay >= az:
        order = 2 if ax >= az else 3
    else:
        order = 4 if ax >= ay else 5
    return (order, sx, sy, sz)


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

    return sx, sy


BACKDROP_FILL = "#888888"
BACKDROP_STIPPLE = "gray50"


def _draw_backdrop_cells(canvas, grid, verts_fn, project):
    for (col, row), color in grid.items():
        if not (NODE_START <= col < NODE_END and NODE_START <= row < NODE_END) or not color:
            continue
        pts = [project(*v) for v in verts_fn(col, row)]
        coords = [c for sx, sy in pts for c in (sx, sy)]
        canvas.create_polygon(coords, fill=BACKDROP_FILL, outline="", stipple=BACKDROP_STIPPLE)




def render_preview(canvas, voxel_faces, azimuth=None, elevation=None, backdrop_grids=None, zoom=1.0):
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
    scale = size / 50 * zoom
    screen_cx = w / 2
    screen_cy = h / 2

    vx, vy, vz = -sin_az * cos_el, sin_el, cos_az * cos_el

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

    if backdrop_grids:
        front_grid = backdrop_grids.get("front", {})
        side_grid = backdrop_grids.get("side", {})

        # Front view on the far z wall (away from camera)
        fz = NODE_END if vz > 0 else NODE_START
        _draw_backdrop_cells(canvas, front_grid,
            lambda col, row: [(col, row, fz), (col+1, row, fz),
                              (col+1, row+1, fz), (col, row+1, fz)],
            project)

        # Side view on the far x wall (away from camera)
        fx = NODE_START if vx < 0 else NODE_END
        _draw_backdrop_cells(canvas, side_grid,
            lambda col, row: [(fx, row, col), (fx, row, col+1),
                              (fx, row+1, col+1), (fx, row+1, col)],
            project)

        # Top view on the far y wall (away from camera)
        top_grid = backdrop_grids.get("top", {})
        fy = NODE_END if vy > 0 else NODE_START
        _draw_backdrop_cells(canvas, top_grid,
            lambda col, row: [(col, fy, row), (col+1, fy, row),
                              (col+1, fy, row+1), (col, fy, row+1)],
            project)

    if not voxel_faces:
        return

    global _sort_cache_voxel_faces_id, _sort_cache_zone, _sort_cache_sorted_voxels

    zone = _view_zone(vx, vy, vz)
    if id(voxel_faces) == _sort_cache_voxel_faces_id and zone == _sort_cache_zone:
        sorted_voxels = _sort_cache_sorted_voxels
    else:
        sorted_voxels = sorted(voxel_faces, key=lambda p: -(vx * p[0] + vy * p[1] + vz * p[2]))
        _sort_cache_voxel_faces_id = id(voxel_faces)
        _sort_cache_zone = zone
        _sort_cache_sorted_voxels = sorted_voxels

    dr, dg, db = BASE_COLOR

    for (fx, fy, fz) in sorted_voxels:
        for name, color in voxel_faces[(fx, fy, fz)]:
            nx, ny, nz = FACE_NORMALS[name]
            if nx * vx + ny * vy + nz * vz >= 0:
                continue

            verts = FACE_VERTS[name](fx, fy, fz)
            proj_verts = [project(*v) for v in verts]

            shade = FACE_SHADING[name]
            if color:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                fill = _shade_color(r, g, b, shade)
            else:
                fill = _shade_color(dr, dg, db, shade)

            coords = []
            for sx, sy in proj_verts:
                coords.extend([sx, sy])
            canvas.create_polygon(coords, fill=fill, outline="")

